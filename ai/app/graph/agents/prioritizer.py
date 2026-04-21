from langgraph.types import interrupt
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg
from app.graph.types import RawTask, TaskBreakdown

# ---------------------------------------------------------------------------
# Agent 3: PrioritizerAgent
# HITL aktif di sini - user bisa edit/hapus/tambah task sebelum dijadwalkan.
# ---------------------------------------------------------------------------


def make_prioritizer(llm):
    """
    Factory untuk PrioritizerAgent.
    Tugas: pecah dan urutkan tugas -> minta konfirmasi user sebelum ke scheduler.

    HITL payload yang dikirim ke frontend:
    {
        "type": "task_review",
        "message": str,
        "tasks": list[dict],   # list task hasil ekstraksi LLM
    }

    Input dari /resume (hitl_input) yang diharapkan:
    {
        "tasks": list[dict]   # task final setelah user edit
    }
    """

    def run(state: AppState) -> dict:
        user_msg = last_message(state)

        # TODO: implementasi logika ekstraksi dan prioritisasi task
        tasks = _extract_tasks(llm, user_msg)

        # graph pause â€” user review dan edit daftar task
        hitl_result = interrupt({
            "type": "task_review",
            "message": "Cek dan edit daftar tugas sebelum dijadwalkan.",
            "tasks": tasks,
        })

        final_tasks = hitl_result.get("tasks") or tasks
        final_raw_tasks = _build_raw_tasks(final_tasks)
        return {
            "raw_tasks": final_raw_tasks,
            "task_breakdown": final_tasks,
            **ai_msg(f"Siap, {len(final_tasks)} tugas akan dijadwalkan."),
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


def _extract_tasks(llm, user_msg: str) -> list[TaskBreakdown]:
    """
    TODO: implementasi logika ekstraksi task dari pesan user.
    Return format mengikuti TaskBreakdown.
    """
    raise NotImplementedError


def _build_raw_tasks(tasks: list[TaskBreakdown]) -> list[RawTask]:
    raw_tasks: list[RawTask] = []
    for idx, task in enumerate(tasks, start=1):
        task_id = task.get("task_id") or f"task_{idx:03d}"
        title = task.get("title") or ""
        raw_tasks.append(
            {
                "task_id": task_id,
                "title": title,
                "raw_input": title,
                "category": "lainnya",
            }
        )
    return raw_tasks