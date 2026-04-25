from app.graph.state import AppState
from app.graph.agents.helpers import get_proposed_schedule, get_metadata, ai_msg
from app.graph.types import ScheduleItem
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Agent 4: SchedulerAgent
# Tidak ada HITL - langsung eksekusi setelah proposed_schedule diapprove.
# ---------------------------------------------------------------------------


def make_scheduler(llm, calendar_client):
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
            event_ids = _schedule_items(calendar_client, normalized_items, metadata)
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
            **ai_msg(f"Semua {len(schedule_items)} tugas sudah dijadwalkan di Google Calendar."),
            "metadata": {
                **metadata,
                "scheduled": True,
                "event_ids": event_ids,
            },
            "api_status": 200,
            "api_payload": {
                "scheduled_count": len(event_ids),
                "event_ids": event_ids,
            },
            "error_message": None,
        }

    return run


def _schedule_items(
    calendar_client,
    schedule_items: list[ScheduleItem],
    metadata: dict
) -> list[str]:
    event_ids: list[str] = []
    timezone_name = metadata.get("timezone") or "UTC"

    for item in schedule_items:
        start_dt = _parse_iso_datetime(item["start_time"])
        end_dt = start_dt + timedelta(minutes=int(item["duration_minutes"]))

        payload = {
            "title": item["task"],
            "description": (
                f"task_id={item['task_id']} | priority={item['priority']} | category={item['category']}"
            ),
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "timezone": timezone_name,
        }

        event_id = calendar_client.create_event(payload)
        event_ids.append(event_id)

    return event_ids


def _parse_iso_datetime(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as err:
        raise ValueError(f"start_time harus ISO-8601 valid: {value}") from err

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _validate_schedule_items(schedule_items: list[ScheduleItem]) -> list[ScheduleItem]:
    if not isinstance(schedule_items, list) or not schedule_items:
        raise ValueError("proposed_schedule harus berupa list dan tidak boleh kosong.")

    normalized: list[ScheduleItem] = []
    required_keys = {"task_id", "task", "priority", "start_time", "duration_minutes", "category"}

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