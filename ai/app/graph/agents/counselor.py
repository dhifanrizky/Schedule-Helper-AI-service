from langgraph.types import interrupt
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg, get_hitl_input

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
        previous_feedback = get_hitl_input(state) or {}

        # Jika loop dari reject sebelumnya, pakai feedback user sebagai konteks tambahan.
        feedback_note = previous_feedback.get("feedback") or previous_feedback.get("reason") or ""
        draft = _generate_response(llm, user_msg, feedback_note)

        # graph pause di sini — tunggu user approve/edit dari frontend
        hitl_result = interrupt({
            "type": "counselor_review",
            "message": "Apakah rangkuman ini sudah sesuai dengan yang kamu rasakan?",
            "draft": draft,
            "hint": "Kirim approved=false + feedback supaya counselor bisa membedah lagi.",
        }) or {}

        approved = bool(hitl_result.get("approved"))
        if not approved:
            return {
                **ai_msg("Siap, kita bedah lagi pelan-pelan sampai ketemu kebutuhan utamamu."),
                "counselor_response": [draft],
                "counselor_done": False,
                "hitl_status": "rejected",
                "hitl_input": hitl_result,
            }

        final = hitl_result.get("edited_draft") or draft
        return {
            **ai_msg(final),
            "counselor_response": [final],
            "counselor_done": True,
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


def _generate_response(llm, user_msg: str, feedback_note: str = "") -> str:
    """
    Buat draft respons empatik + membantu user menemukan kebutuhan utama.
    """
    prompt = (
        "Kamu adalah counselor yang empatik dan ringkas. "
        "Tugasmu: validasi perasaan user, bedah inti masalah, lalu rumuskan kebutuhan praktis yang bisa ditindaklanjuti.\n\n"
        f"Curhatan user: {user_msg}\n"
    )
    if feedback_note:
        prompt += f"Feedback tambahan dari user: {feedback_note}\n"
    prompt += (
        "Akhiri dengan 1 pertanyaan konfirmasi yang konkret agar user bisa approve atau minta revisi."
    )

    try:
        response = llm.invoke(prompt)
        content = getattr(response, "content", response)
        if isinstance(content, str) and content.strip():
            return content.strip()
        return str(content)
    except Exception:
        # Fallback aman jika provider LLM error.
        return (
            "Aku paham ini lagi berat. Dari ceritamu, kebutuhan utamanya adalah menata langkah kecil "
            "yang paling mendesak dulu supaya kamu tidak kewalahan."
        )