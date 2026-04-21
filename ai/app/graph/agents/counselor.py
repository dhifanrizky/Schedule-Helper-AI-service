from langgraph.types import interrupt
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg

# ---------------------------------------------------------------------------
# Agent 2: CounselorAgent
# HITL aktif di sini — graph akan pause dan tunggu /resume sebelum lanjut.
# ---------------------------------------------------------------------------


def make_counselor(llm):
    """
    Factory untuk CounselorAgent.
    Tugas: empati + brain dump → minta konfirmasi user sebelum lanjut.

    HITL payload yang dikirim ke frontend:
    {
        "type": "counselor_review",
        "message": str,   # pertanyaan konfirmasi untuk user
        "draft": str,     # draft respons dari LLM
    }

    Input dari /resume (hitl_input) yang diharapkan:
    {
        "approved": bool,
        "edited_draft": str | None   # jika user ingin edit draft
    }
    """

    def run(state: AppState) -> dict:
        user_msg = last_message(state)

        # TODO: implementasi logika counselor-mu di sini
        draft = _generate_response(llm, user_msg)

        # graph pause di sini — tunggu user approve/edit dari frontend
        hitl_result = interrupt({
            "type": "counselor_review",
            "message": "Apakah rangkuman ini sudah sesuai dengan yang kamu rasakan?",
            "draft": draft,
        })

        final = hitl_result.get("edited_draft") or draft
        return {
            **ai_msg(final),
            "counselor_response": [final],
            "counselor_done": True,
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


def _generate_response(llm, user_msg: str) -> str:
    """
    TODO: implementasi logika LLM call untuk counselor.
    Bisa pakai system prompt empati, brain dump template, dll.
    """
    raise NotImplementedError