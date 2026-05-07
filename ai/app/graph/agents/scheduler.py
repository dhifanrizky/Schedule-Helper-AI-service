from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.graph.state import AppState
from app.graph.agents.helpers import get_proposed_schedule, get_metadata, ai_msg
from app.graph.types import ScheduleItem


# ---------------------------------------------------------------------------
# Agent 4: SchedulerAgent
#
# Tugas:
# 1. Menerima proposed_schedule final dari Agent 3.
# 2. Memastikan jadwal sudah di-approve user.
# 3. Validasi format proposed_schedule.
# 4. Mapping proposed_schedule ke format CreateCalendarDto untuk BE.
# 5. Memanggil calendar_client.create_schedule() agar BE upload ke Google Calendar.
#
# Catatan:
# - Agent 4 tidak menghitung prioritas lagi.
# - Agent 4 tidak membuat jadwal ulang.
# - Agent 4 hanya mengeksekusi proposed_schedule yang sudah final.
# ---------------------------------------------------------------------------


DEFAULT_TIMEZONE = "Asia/Jakarta"


def make_scheduler(llm=None, calendar_client=None):
    """
    Factory untuk Agent 4 / Scheduler.

    llm dibuat optional karena Scheduler tidak perlu LLM lagi.
    Agent 4 cukup mapping proposed_schedule ke payload BE.
    """

    def run(state: AppState) -> dict:
        metadata = get_metadata(state) or {}
        schedule_items = get_proposed_schedule(state)

        # Safety check.
        # Secara normal, graph baru masuk Scheduler setelah user approve.
        # Tapi ini tetap dicek agar aman jika Scheduler dipanggil manual.
        if state.get("hitl_status") != "approved":
            return {
                **ai_msg("Jadwal belum di-approve user, jadi belum bisa dikirim ke Calendar."),
                "error_message": "Jadwal belum di-approve user.",
                "api_status": 400,
                "api_payload": {
                    "error": "Jadwal belum di-approve user.",
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
                **ai_msg("Calendar client belum tersedia, jadi jadwal belum bisa dikirim ke BE."),
                "error_message": "calendar_client tidak tersedia.",
                "api_status": 500,
                "api_payload": {
                    "error": "calendar_client tidak tersedia.",
                },
                "final_message": None,
            }

        try:
            normalized_items = _validate_schedule_items(schedule_items)
            calendar_payloads = _build_calendar_payloads(
                schedule_items=normalized_items,
                metadata=metadata,
            )
            auth_token = _extract_auth_token(metadata)

            created_events = _send_to_backend_calendar(
                calendar_client=calendar_client,
                calendar_payloads=calendar_payloads,
                auth_token=auth_token,
            )

        except ValueError as err:
            return {
                **ai_msg("Format jadwal belum valid. Mohon perbaiki dulu sebelum dikirim ke Calendar."),
                "error_message": str(err),
                "api_status": 400,
                "api_payload": {
                    "error": str(err),
                },
                "final_message": None,
            }

        except Exception as err:
            return {
                **ai_msg("Gagal mengirim jadwal ke Google Calendar. Coba lagi sebentar ya."),
                "error_message": str(err),
                "api_status": 500,
                "api_payload": {
                    "error": str(err),
                },
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
            "error_message": None,
            "final_message": f"Berhasil menjadwalkan {len(created_events)} kegiatan ke Google Calendar.",
        }

    return run


def _validate_schedule_items(schedule_items: list[ScheduleItem]) -> list[ScheduleItem]:
    """
    Validasi proposed_schedule dari Agent 3.

    Field wajib dari Agent 3:
    - task_id
    - task
    - priority
    - start_time
    - duration_minutes
    - category
    """

    if not isinstance(schedule_items, list) or not schedule_items:
        raise ValueError("proposed_schedule harus berupa list dan tidak boleh kosong.")

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
            raise ValueError(f"Item ke-{idx} harus berupa object/dict.")

        missing = required_keys - set(item.keys())
        if missing:
            raise ValueError(
                f"Item ke-{idx} missing field: {', '.join(sorted(missing))}."
            )

        task_id = str(item.get("task_id") or "").strip()
        task = str(item.get("task") or "").strip()
        start_time = str(item.get("start_time") or "").strip()
        category = str(item.get("category") or "biasa").strip() or "biasa"

        if not task_id:
            raise ValueError(f"Item ke-{idx} task_id kosong.")

        if not task:
            raise ValueError(f"Item ke-{idx} task kosong.")

        if not start_time:
            raise ValueError(f"Item ke-{idx} start_time kosong.")

        try:
            duration_minutes = int(item.get("duration_minutes"))
        except (TypeError, ValueError) as err:
            raise ValueError(f"Item ke-{idx} duration_minutes harus angka.") from err

        if duration_minutes <= 0:
            raise ValueError(f"Item ke-{idx} duration_minutes harus lebih dari 0.")

        try:
            priority = int(item.get("priority"))
        except (TypeError, ValueError) as err:
            raise ValueError(f"Item ke-{idx} priority harus angka.") from err

        if priority not in [1, 2, 3]:
            raise ValueError(f"Item ke-{idx} priority harus 1, 2, atau 3.")

        # Validasi ISO datetime.
        _parse_iso_datetime(start_time)

        normalized_items.append({
            "task_id": task_id,
            "task": task,
            "priority": priority,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "category": category,
        })

    return normalized_items


def _build_calendar_payloads(
    schedule_items: list[ScheduleItem],
    metadata: dict,
) -> list[dict]:
    """
    Mapping proposed_schedule ke format CreateCalendarDto milik BE.

    Dari Agent 3:
    - task
    - start_time
    - duration_minutes
    - priority
    - category
    - task_id

    Menjadi DTO BE:
    - title
    - description
    - category
    - estimatedMinutes
    - priority
    - deadline
    - startTime
    - status
    """

    timezone_name = metadata.get("timezone") or DEFAULT_TIMEZONE
    calendar_payloads: list[dict] = []

    for item in schedule_items:
        start_dt = _parse_iso_datetime(item["start_time"], timezone_name)
        end_dt = start_dt + timedelta(minutes=int(item["duration_minutes"]))

        payload = {
            "title": item["task"],
            "description": (
                f"Generated by Scheduler Agent. "
                f"task_id={item['task_id']} | "
                f"priority={item['priority']} | "
                f"category={item['category']}"
            ),
            "category": item["category"],
            "estimatedMinutes": int(item["duration_minutes"]),
            "priority": int(item["priority"]),
            "deadline": end_dt.isoformat(),
            "startTime": start_dt.isoformat(),
            "status": "pending",
        }

        calendar_payloads.append(payload)

    return calendar_payloads


def _send_to_backend_calendar(
    calendar_client,
    calendar_payloads: list[dict],
    auth_token: str | None,
) -> list[dict]:
    """
    Kirim payload ke BE lewat calendar_client.

    Fungsi yang dipakai:
    calendar_client.create_schedule(payload, token=auth_token)
    """

    created_events: list[dict] = []

    for payload in calendar_payloads:
        response = calendar_client.create_schedule(payload, token=auth_token)
        event_id = _extract_event_id(response)

        created_events.append({
            "event_id": event_id,
            "title": payload["title"],
            "startTime": payload["startTime"],
            "deadline": payload["deadline"],
            "estimatedMinutes": payload["estimatedMinutes"],
            "priority": payload["priority"],
            "category": payload["category"],
            "raw_response": response,
        })

    return created_events


def _extract_event_id(response) -> str:
    """
    Ambil ID event dari response BE.

    Dibuat fleksibel karena response BE bisa beda bentuk:
    - {"id": "..."}
    - {"event_id": "..."}
    - {"data": {"id": "..."}}
    - {"data": {"event_id": "..."}}
    """

    if isinstance(response, dict):
        if response.get("id") is not None:
            return str(response["id"])

        if response.get("event_id") is not None:
            return str(response["event_id"])

        data = response.get("data")
        if isinstance(data, dict):
            if data.get("id") is not None:
                return str(data["id"])

            if data.get("event_id") is not None:
                return str(data["event_id"])

    return ""


def _parse_iso_datetime(value: str, timezone_name: str = DEFAULT_TIMEZONE) -> datetime:
    """
    Parse ISO datetime.

    Kalau belum ada timezone, otomatis pakai Asia/Jakarta.
    Kalau ZoneInfo Asia/Jakarta error di Windows, fallback ke UTC+7.
    """

    if not isinstance(value, str) or not value.strip():
        raise ValueError("Datetime kosong atau bukan string.")

    normalized_value = value.strip().replace("Z", "+00:00")

    try:
        dt = datetime.fromisoformat(normalized_value)
    except ValueError as err:
        raise ValueError(f"Datetime harus ISO-8601 valid: {value}") from err

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_get_tzinfo(timezone_name))

    return dt


def _get_tzinfo(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name == DEFAULT_TIMEZONE:
            return timezone(timedelta(hours=7))
        return timezone.utc


def _extract_auth_token(metadata: dict) -> str | None:
    """
    Ambil token dari metadata state.

    FE/BE bisa menyimpan token dengan salah satu key ini:
    - auth_token
    - access_token
    - authorization
    """

    for key in ("auth_token", "access_token", "authorization"):
        value = metadata.get(key)

        if isinstance(value, str) and value.strip():
            token = value.strip()

            # Kalau sudah Bearer, biarkan.
            if token.lower().startswith("bearer "):
                return token

            return token

    return None