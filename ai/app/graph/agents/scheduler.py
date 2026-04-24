from app.graph.state import AppState
from app.graph.agents.helpers import get_proposed_schedule, get_metadata, ai_msg
from app.graph.types import ScheduleItem

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
            }

        event_ids = _schedule_items(calendar_client, schedule_items, metadata)

        return {
            **ai_msg(f"Semua {len(schedule_items)} tugas sudah dijadwalkan di Google Calendar."),
            "metadata": {
                **metadata,
                "scheduled": True,
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
    """
    TODO: implementasi logika create event di Google Calendar.
    Return list of event IDs yang berhasil dibuat.
    """
    raise NotImplementedError