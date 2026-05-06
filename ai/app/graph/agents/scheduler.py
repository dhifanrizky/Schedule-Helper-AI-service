from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ValidationError

from app.graph.state import AppState
from app.graph.agents.helpers import get_proposed_schedule, get_metadata, ai_msg
from app.graph.types import ScheduleItem

# ---------------------------------------------------------------------------
# Agent 4 / Scheduler
# Catatan:
# - Scheduler menerima proposed_schedule dari Agent 3.
# - Tidak membuat prioritas lagi.
# - Hanya validasi dan mengirim jadwal ke calendar_client.
# ---------------------------------------------------------------------------


DEFAULT_TIMEZONE = "Asia/Jakarta"


class LLMCalendarItem(BaseModel):
    title: str = Field(description="Judul task untuk kalender")
    description: str = Field(description="Deskripsi ringkas untuk kalender")
    category: str = Field(description="Kategori task")
    estimatedMinutes: int | None = Field(default=None, ge=1)
    priority: int | None = Field(default=None, ge=1, le=3)
    deadline: str | None = Field(default=None, description="ISO-8601 end time")
    startTime: str | None = Field(default=None, description="ISO-8601 start time")
    status: str | None = Field(default="pending")


class LLMCalendarResponse(BaseModel):
    items: list[LLMCalendarItem]


def make_scheduler(llm, calendar_client):
    structured_llm = llm.with_structured_output(LLMCalendarResponse)

    def run(state: AppState) -> dict:
        schedule_items = get_proposed_schedule(state)
        metadata = get_metadata(state) or {}

        if not schedule_items:
            return {
                **ai_msg("Belum ada proposed_schedule yang bisa dijadwalkan."),
                "error_message": "proposed_schedule kosong.",
                "api_status": 400,
                "api_payload": {"error": "proposed_schedule kosong."},
            }

        try:
            normalized_items = _validate_schedule_items(schedule_items)
            calendar_payloads = _build_calendar_payloads_with_llm(
                normalized_items,
                metadata,
                structured_llm,
            )
            event_ids = _schedule_items(calendar_client, calendar_payloads, metadata)
        except ValueError as err:
            return {
                **ai_msg("Format jadwal belum valid. Mohon perbaiki dulu sebelum dikirim ke kalender."),
                "error_message": str(err),
                "api_status": 400,
                "api_payload": {"error": str(err)},
            }
        except Exception as err:
            return {
                **ai_msg("Gagal mengirim jadwal ke Google Calendar. Coba lagi sebentar ya."),
                "error_message": str(err),
                "api_status": 500,
                "api_payload": {"error": str(err)},
            }

        return {
            **ai_msg(f"Semua {len(event_ids)} tugas sudah dijadwalkan di Google Calendar."),
            "metadata": {
                **metadata,
                "scheduled": True,
                "event_ids": event_ids,
            },
            "api_status": 200,
            "api_payload": {
                "scheduled_count": len(event_ids),
                "event_ids": event_ids,
                "calendar_items": calendar_payloads,
            },
            "error_message": None,
            "final_message": f"Berhasil menjadwalkan {len(event_ids)} tugas.",
        }

    return run


def _schedule_items(
    calendar_client,
    calendar_items: list[dict],
    metadata: dict,
) -> list[str]:
    event_ids: list[str] = []
    timezone_name = metadata.get("timezone") or DEFAULT_TIMEZONE

    for item in calendar_items:
        payload = _calendar_dto_to_event_payload(item, timezone_name)
        event_id = calendar_client.create_event(payload)
        event_ids.append(event_id)

    return event_ids


def _parse_iso_datetime(value: str, timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as err:
        raise ValueError(f"start_time harus ISO-8601 valid: {value}") from err

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(timezone_name))

    return dt


def _build_calendar_payloads_with_llm(
    schedule_items: list[ScheduleItem],
    metadata: dict,
    structured_llm,
) -> list[dict]:
    timezone_name = metadata.get("timezone") or DEFAULT_TIMEZONE
    seed_items: list[dict] = []

    for item in schedule_items:
        start_dt = _parse_iso_datetime(item["start_time"], timezone_name)
        end_dt = start_dt + timedelta(minutes=int(item["duration_minutes"]))
        seed_items.append({
            "task_id": item["task_id"],
            "task": item["task"],
            "priority": item["priority"],
            "category": item["category"],
            "estimated_minutes": item["duration_minutes"],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
        })

    prompt = (
        "Ubah daftar proposed_schedule berikut menjadi payload CreateCalendarDto. "
        "Ikuti format field DTO: title, description, category, estimatedMinutes, "
        "priority, deadline, startTime, status. "
        "Gunakan start_time -> startTime, end_time -> deadline, "
        "estimated_minutes -> estimatedMinutes. "
        "description harus ringkas dan boleh memuat task_id. "
        "status default 'pending' jika tidak jelas."
        f"\n\nInput:\n{seed_items}"
    )

    try:
        result = structured_llm.invoke([
            {
                "role": "system",
                "content": "Kamu adalah adapter data untuk CreateCalendarDto.",
            },
            {"role": "user", "content": prompt},
        ])
    except Exception:
        return _fallback_calendar_payloads(seed_items)

    if hasattr(result, "model_dump"):
        result = result.model_dump()

    if not isinstance(result, dict):
        return _fallback_calendar_payloads(seed_items)

    items = result.get("items")
    if not isinstance(items, list) or not items:
        return _fallback_calendar_payloads(seed_items)

    normalized: list[dict] = []
    for idx, item in enumerate(items, start=1):
        try:
            parsed = LLMCalendarItem.model_validate(item)
        except ValidationError:
            return _fallback_calendar_payloads(seed_items)

        normalized.append(parsed.model_dump())

    return normalized


def _fallback_calendar_payloads(seed_items: list[dict]) -> list[dict]:
    fallback: list[dict] = []
    for item in seed_items:
        fallback.append({
            "title": item["task"],
            "description": (
                f"task_id={item['task_id']} | "
                f"priority={item['priority']} | "
                f"category={item['category']}"
            ),
            "category": item["category"],
            "estimatedMinutes": item["estimated_minutes"],
            "priority": item["priority"],
            "deadline": item["end_time"],
            "startTime": item["start_time"],
            "status": "pending",
        })

    return fallback


def _calendar_dto_to_event_payload(dto: dict, timezone_name: str) -> dict:
    start_value = dto.get("startTime")
    end_value = dto.get("deadline")

    start_dt = _parse_iso_datetime(start_value, timezone_name) if start_value else None
    if start_dt is None:
        start_dt = datetime.now(ZoneInfo(timezone_name))

    if end_value:
        end_dt = _parse_iso_datetime(end_value, timezone_name)
    else:
        estimated = dto.get("estimatedMinutes")
        if isinstance(estimated, int) and estimated > 0:
            end_dt = start_dt + timedelta(minutes=estimated)
        else:
            end_dt = start_dt + timedelta(hours=1)

    return {
        "title": dto.get("title") or "Untitled Task",
        "description": dto.get("description") or "",
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "timezone": timezone_name,
    }


def _validate_schedule_items(schedule_items: list[ScheduleItem]) -> list[ScheduleItem]:
    if not isinstance(schedule_items, list) or not schedule_items:
        raise ValueError("proposed_schedule harus berupa list dan tidak boleh kosong.")

    normalized: list[ScheduleItem] = []
    required_keys = {
        "task_id",
        "task",
        "priority",
        "start_time",
        "duration_minutes",
        "category",
    }

    for idx, item in enumerate(schedule_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Item ke-{idx} harus berupa object.")

        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(f"Item ke-{idx} missing field: {', '.join(sorted(missing))}.")

        task = str(item.get("task") or "").strip()
        if not task:
            raise ValueError(f"Item ke-{idx} punya task kosong.")

        task_id = str(item.get("task_id") or "").strip()
        if not task_id:
            raise ValueError(f"Item ke-{idx} punya task_id kosong.")

        duration = item.get("duration_minutes")
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError(f"Item ke-{idx} duration_minutes harus integer > 0.")

        _parse_iso_datetime(str(item.get("start_time")))

        priority = item.get("priority")
        if not isinstance(priority, int):
            raise ValueError(f"Item ke-{idx} priority harus integer.")

        if priority not in [1, 2, 3]:
            raise ValueError(f"Item ke-{idx} priority harus 1, 2, atau 3.")

        category = str(item.get("category") or "biasa").strip() or "biasa"

        normalized.append({
            "task_id": task_id,
            "task": task,
            "priority": priority,
            "start_time": str(item["start_time"]),
            "duration_minutes": duration,
            "category": category,
        })

    return normalized