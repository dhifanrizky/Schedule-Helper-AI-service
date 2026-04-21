from app.graph.state import AppState
from app.graph.agents.helpers import get_task_breakdown, get_metadata, ai_msg

# ---------------------------------------------------------------------------
# Agent 4: SchedulerAgent
# Tidak ada HITL - langsung eksekusi setelah task_list diapprove.
# ---------------------------------------------------------------------------


def make_scheduler(llm, calendar_client):
    """
    Factory untuk SchedulerAgent.
    Tugas: buat event di Google Calendar dari task_list yang sudah diapprove.
    """

    def run(state: AppState) -> dict:
        tasks = get_task_breakdown(state)
        metadata = get_metadata(state)

        # TODO: implementasi logika scheduling ke Google Calendar
        event_ids = _schedule_tasks(calendar_client, tasks, metadata)

        return {
            **ai_msg(f"Semua {len(tasks)} tugas sudah dijadwalkan di Google Calendar."),
            "metadata": {
                **metadata,
                "scheduled": True,
                "event_ids": event_ids,
            },
        }

    return run


def _schedule_tasks(calendar_client, tasks: list[dict], metadata: dict) -> list[str]:
    """
    TODO: implementasi logika create event di Google Calendar.
    Return list of event IDs yang berhasil dibuat.
    """
    raise NotImplementedError