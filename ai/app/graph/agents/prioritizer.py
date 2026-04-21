from langgraph.types import interrupt
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg

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
        final_raw_tasks = [task.get("task", "") for task in final_tasks if isinstance(task, dict)]
        return {
            "raw_tasks": final_raw_tasks,
            "task_list": final_tasks,
            "task_breakdown": final_tasks,
            **ai_msg(f"Siap, {len(final_tasks)} tugas akan dijadwalkan."),
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


def _extract_tasks(llm, user_msg: str) -> list[dict]:
    """
    TODO: implementasi logika ekstraksi task dari pesan user.
    Return format: [{"task": str, "priority": int, "deadline": str | None}]
    """
    raise NotImplementedError