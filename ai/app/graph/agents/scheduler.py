from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import json
import logging

from app.graph.state import GraphState
from app.graph.agents.helpers import get_proposed_schedule, get_metadata, ai_msg
from app.graph.types import CategoryType, ScheduleItem


# ---------------------------------------------------------------------------
# Agent 4: SchedulerAgent
#
# Tugas:
# 1. Menerima proposed_schedule final dari Agent 3.
# 2. Memastikan jadwal sudah di-approve user (cek hitl_status atau hitl_input).
# 3. Validasi format proposed_schedule.
# 4. Mapping proposed_schedule ke format CreateCalendarDto untuk BE.
# 5. Memanggil calendar_client.create_schedule() agar BE upload ke Google Calendar.
#
# Reasoning:
# - Tidak menambah field baru.
# - Alasan penjadwalan dimasukkan ke field "description" yang sudah ada.
# ---------------------------------------------------------------------------


DEFAULT_TIMEZONE = "Asia/Jakarta"
logger = logging.getLogger(__name__)


def make_scheduler(llm=None, calendar_client=None):
    """
    Factory untuk Agent 4 / Scheduler.
    """

    def run(state: GraphState) -> dict:
        metadata = get_metadata(state) or {}
        schedule_items = get_proposed_schedule(state)

        hitl_status = state.get("hitl_status")
        hitl_input = state.get("hitl_input") or {}

        is_approved = (hitl_status == "approved") or (hitl_input.get("approved") is True)

        if not is_approved:
            return {
                **ai_msg("Jadwal belum di-approve user, jadi belum bisa dikirim ke Calendar."),
                "error_message": "Jadwal belum di-approve user.",
                "api_status": 400,
                "api_payload": {
                    "error": "Jadwal belum di-approve user.",
                    "hitl_status": hitl_status,
                },
                "final_message": None,
            }

        if not schedule_items:
            return {
                **ai_msg("Belum ada proposed_schedule yang bisa dijadwalkan."),
                "error_message": "proposed_schedule kosong.",
                "api_status": 400,
                "api_payload": {
                    "error": "proposed_schedule kosong.",
                },
                "final_message": None,
            }

        if calendar_client is None:
            return {
                **ai_msg("Calendar client belum tersedia."),
                "error_message": "calendar_client tidak tersedia.",
                "api_status": 500,
                "api_payload": {
                    "error": "calendar_client tidak tersedia.",
                },
                "final_message": None,
            }

        try:
            normalized_items = _validate_schedule_items(schedule_items)

        except ValueError as validation_err:
            if llm is not None:
                try:
                    fixed_items = _fix_format_with_llm(
                        llm,
                        schedule_items,
                        str(validation_err),
                    )
                    normalized_items = _validate_schedule_items(fixed_items)

                except Exception as llm_err:
                    return {
                        **ai_msg("Format jadwal sangat tidak beraturan dan sistem AI gagal memformat ulang secara otomatis."),
                        "error_message": f"Init Error: {validation_err} | LLM Auto-Fix Error: {llm_err}",
                        "api_status": 400,
                        "api_payload": {
                            "error": f"LLM fix failed: {llm_err}",
                        },
                        "final_message": None,
                    }

            else:
                return {
                    **ai_msg("Format jadwal belum valid. Mohon perbaiki dulu."),
                    "error_message": str(validation_err),
                    "api_status": 400,
                    "api_payload": {
                        "error": str(validation_err),
                    },
                    "final_message": None,
                }

        try:
            calendar_payloads = _build_calendar_payloads(
                schedule_items=normalized_items,
                metadata=metadata,
            )

            logger.info("[scheduler] calendar_payloads=%s", json.dumps(calendar_payloads))

            auth_token = _extract_auth_token(metadata) or _extract_auth_token(hitl_input)

            logger.info(
                "[scheduler] auth_token_present=%s base_url=%s",
                bool(auth_token),
                getattr(calendar_client, "base_url", None),
            )

            created_events = _send_to_backend_calendar(
                calendar_client=calendar_client,
                calendar_payloads=calendar_payloads,
                auth_token=auth_token,
            )

        except ValueError as err:
            logger.exception("[scheduler] build payload error: %s", err)
            return {
                **ai_msg("Terdapat kesalahan fatal pada format tanggal saat mempersiapkan data jadwal."),
                "error_message": str(err),
                "api_status": 400,
                "api_payload": {
                    "error": str(err),
                },
                "final_message": None,
            }

        except Exception as err:
            logger.exception("[scheduler] backend send error: %s", err)
            return {
                **ai_msg(
                    f"Gagal mengirim ke Google Calendar. Error: {str(err)}. Sistem siap mencoba ulang, silakan klik 'Coba Lagi'."
                ),
                "error_message": str(err),
                "api_status": 500,
                "api_payload": {
                    "error": str(err),
                    "retryable": True,
                },
                "status": "waiting_hitl",
                "hitl_status": "pending",
                "final_message": None,
            }

        event_ids = [event["event_id"] for event in created_events]

        return {
            **ai_msg(f"Berhasil menjadwalkan {len(created_events)} kegiatan ke Google Calendar."),
            "metadata": {
                **metadata,
                "scheduled": True,
                "event_ids": event_ids,
            },
            "api_status": 200,
            "api_payload": {
                "scheduled_count": len(created_events),
                "event_ids": event_ids,
                "calendar_items": calendar_payloads,
                "created_events": created_events,
            },
            "hitl_status": None,
            "hitl_input": None,
            "error_message": None,
            "final_message": f"Berhasil menjadwalkan {len(created_events)} kegiatan ke Google Calendar.",
        }

    return run


def _fix_format_with_llm(llm, raw_items: list, error_msg: str) -> list:
    """
    Menggunakan LLM untuk memperbaiki format schedule yang tidak valid menjadi JSON list murni.
    """
    prompt = f"""
    Anda adalah sistem data-formatting. Data array jadwal di bawah ini gagal divalidasi oleh sistem.
    Alasan error: {error_msg}

    Data saat ini:
    {json.dumps(raw_items, indent=2)}

    Tugas Anda: Perbaiki data tersebut dan kembalikan HANYA array JSON (list of objects).
    Setiap object HARUS memiliki key berikut:
    - "task_id": string
    - "task": string
    - "priority": integer
    - "start_time": string format ISO 8601
    - "duration_minutes": integer
    - "category": string, salah satu: "serius", "santai", "biasa", "lainnya"

    Jika ada field "subtasks", pertahankan sebagai list string.
    Jangan berikan penjelasan apa pun, output harus JSON murni tanpa markdown.
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())


def _validate_schedule_items(schedule_items: list[ScheduleItem]) -> list[ScheduleItem]:
    """
    Validasi proposed_schedule sesuai tipe data ScheduleItem.
    """
    if not isinstance(schedule_items, list) or not schedule_items:
        raise ValueError("proposed_schedule kosong.")

    required_keys = {
        "task_id",
        "task",
        "priority",
        "start_time",
        "duration_minutes",
        "category",
    }

    normalized_items: list[ScheduleItem] = []

    for idx, item in enumerate(schedule_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Item {idx} harus berupa object/dict.")

        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(f"Item {idx} missing field: {', '.join(sorted(missing))}")

        raw_cat = str(item.get("category") or "biasa").strip().lower()
        if raw_cat not in ["serius", "santai", "biasa", "lainnya"]:
            raw_cat = "biasa"

        category = cast(CategoryType, raw_cat)

        try:
            duration = int(item["duration_minutes"])
            priority = int(item["priority"])
        except (TypeError, ValueError) as err:
            raise ValueError(f"Item {idx}: priority/duration harus angka.") from err

        if duration <= 0:
            raise ValueError(f"Item {idx}: duration_minutes harus lebih dari 0.")

        if priority not in [1, 2, 3]:
            raise ValueError(f"Item {idx}: priority harus 1, 2, atau 3.")

        _parse_iso_datetime(str(item["start_time"]))

        normalized_items.append({
            "task_id": str(item["task_id"]),
            "task": str(item["task"]),
            "priority": priority,
            "start_time": str(item["start_time"]),
            "duration_minutes": duration,
            "category": category,
            "subtasks": item.get("subtasks", []),
        })

    return normalized_items


def _build_calendar_payloads(
    schedule_items: list[ScheduleItem],
    metadata: dict,
) -> list[dict]:
    timezone_name = metadata.get("timezone") or DEFAULT_TIMEZONE
    payloads: list[dict] = []

    for item in schedule_items:
        start_dt = _parse_iso_datetime(item["start_time"], timezone_name)
        start_dt = start_dt.replace(microsecond=0)

        end_dt = start_dt + timedelta(minutes=item["duration_minutes"])
        end_dt = end_dt.replace(microsecond=0)

        title = item["task"].strip() if item["task"].strip() else "Untitled Task"

        reasoning = _build_calendar_reasoning(
            item=item,
            start_dt=start_dt,
            end_dt=end_dt,
        )

        payloads.append({
            "title": title,
            "description": (
                f"ID: {item['task_id']} | "
                f"Priority: {item['priority']} | "
                f"Reasoning: {reasoning}"
            ),
            "category": item["category"],
            "estimatedMinutes": item["duration_minutes"],
            "priority": item["priority"],
            "deadline": end_dt.isoformat(),
            "startTime": start_dt.isoformat(),
            "status": "pending",
            "subtasks": item.get("subtasks", []),
        })

    return payloads


def _build_calendar_reasoning(
    item: ScheduleItem,
    start_dt: datetime,
    end_dt: datetime,
) -> str:
    """
    Membuat reasoning tanpa mengubah struktur payload.

    Reasoning dimasukkan ke field description yang sudah ada.
    """
    task_name = item.get("task") or "Tugas"
    priority = item.get("priority")
    duration = item.get("duration_minutes")
    category = item.get("category") or "biasa"

    return (
        f"{task_name} dijadwalkan pada {start_dt.strftime('%Y-%m-%d %H:%M')} "
        f"sampai {end_dt.strftime('%H:%M')} berdasarkan proposed_schedule final "
        f"yang sudah disetujui user. Durasi mengikuti estimasi {duration} menit, "
        f"dengan priority {priority} dan kategori {category}."
    )


def _send_to_backend_calendar(
    calendar_client,
    calendar_payloads: list[dict],
    auth_token: str | None,
) -> list[dict]:
    events: list[dict] = []

    for payload in calendar_payloads:
        response = calendar_client.create_schedule(payload, token=auth_token)

        events.append({
            "event_id": _extract_event_id(response),
            **payload,
            "raw_response": response,
        })

    return events


def _extract_event_id(response) -> str:
    if isinstance(response, dict):
        for key in ("id", "event_id"):
            if response.get(key):
                return str(response[key])

        data = response.get("data")
        if isinstance(data, dict):
            for key in ("id", "event_id"):
                if data.get(key):
                    return str(data[key])

    return ""


def _parse_iso_datetime(value: str, timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")

    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as err:
        raise ValueError(f"ISO format invalid: {value}") from err

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_get_tzinfo(timezone_name))

    return dt


def _get_tzinfo(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=7)) if timezone_name == DEFAULT_TIMEZONE else timezone.utc


def _extract_auth_token(metadata: dict) -> str | None:
    for key in ("auth_token", "access_token", "authorization"):
        value = metadata.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None