from langgraph.types import interrupt as _langgraph_interrupt
from pydantic import BaseModel, Field
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg, get_hitl_input, get_raw_tasks

# ---------------------------------------------------------------------------
# Agent 2: CounselorAgent
# HITL aktif di sini — graph pause dan tunggu /resume sebelum lanjut.
#
# TUGAS:
#   1. Validasi perasaan user secara empatik dan hangat
#   2. Identifikasi masalah utama + tugas-tugas yang dihadapi user
#   3. Rumuskan kebutuhan praktis user yang actionable
#   4. Tanya ke user — kesimpulan udah pas, atau mau tambahin cerita?
#   5. Loop sampai user merasa dipahami, baru lanjut ke Prioritizer
#
# HITL PAYLOAD yang dikirim ke frontend via /chat (execution_complete):
#   {
#     "type": "counselor_review",
#     "draft": str,      # respons empatik dari LLM — ditampilkan ke user
#     "message": str,    # pertanyaan konfirmasi di bawah draft
#   }
#
# INPUT dari /resume (hitl_input) yang diharapkan:
#   {
#     "approved": bool,          # True = user puas, lanjut ke Prioritizer
#     "additional_context": str  # Kalau False, user tambahin cerita/konteks baru
#   }
#
# LOOP:
#   - approved=True  → counselor_done=True → graph lanjut ke Prioritizer
#   - approved=False → counselor_done=False → counselor jalan lagi dengan
#                      additional_context sebagai konteks tambahan
# ---------------------------------------------------------------------------

MAX_COUNSELOR_LOOPS = 3


# ---------------------------------------------------------------------------
# Structured output schema — satu LLM call menghasilkan draft + bridge
# sekaligus, sehingga tidak ada round-trip tambahan saat approved.
# bridge hanya ditampilkan ke user ketika approved=True.
# ---------------------------------------------------------------------------
class CounselorOutput(BaseModel):
    draft: str = Field(
        description=(
            "Respons empatik: validasi perasaan, sebutkan tugas yang terdeteksi, "
            "identifikasi sumber stress, rumuskan kebutuhan praktis. "
            "Akhiri SELALU dengan: 'Kesimpulan ini udah pas sama kondisi kamu, "
            "atau mau tambahin sesuatu dulu?'"
        )
    )
    bridge: str = Field(
        description=(
            "1-2 kalimat transisi dari sesi konseling ke tahap penjadwalan. "
            "Hanya ditampilkan ke user jika user approve (puas). "
            "Boleh kasih saran micro (istirahat sebentar, tarik napas) sebelum "
            "tawarin jadwal. Jangan ulangi validasi. Jangan terlalu semangat/salesy. "
            "Akhiri dengan tawaran konkret ke jadwal, bukan pertanyaan."
        )
    )


def make_counselor(llm, _interrupt=None):
    """
    Factory untuk CounselorAgent.

    Args:
        llm: LLM instance (BaseChatModel).
        _interrupt: Override interrupt — HANYA untuk testing. Di production biarkan None.
    """
    interrupt_fn = _interrupt if _interrupt is not None else _langgraph_interrupt
    structured_llm = llm.with_structured_output(CounselorOutput)

    def run(state: AppState) -> dict:
        user_msg = last_message(state)
        raw_tasks = get_raw_tasks(state)
        previous_hitl = get_hitl_input(state) or {}
        loop_count = len(state.get("counselor_response") or [])

        # Safety: paksa selesai kalau sudah terlalu banyak loop
        if loop_count >= MAX_COUNSELOR_LOOPS:
            forced_msg = (
                "Oke, aku udah paham situasimu sekarang. "
                "Yuk kita mulai atur satu per satu supaya lebih manageable!"
            )
            return {
                **ai_msg(forced_msg),
                "counselor_response": [forced_msg],
                "counselor_done": True,
                "hitl_status": "approved",
                "hitl_input": None,
            }

        # Ambil konteks tambahan dari loop sebelumnya (kalau ada)
        additional_context = previous_hitl.get("additional_context", "")

        # Satu LLM call → draft (untuk HITL) + bridge (untuk approved path)
        output = _generate_response(structured_llm, user_msg, raw_tasks, additional_context)

        # Graph pause di sini — tunggu /resume dari NestJS
        hitl_result = interrupt_fn({
            "type": "counselor_review",
            "draft": output.draft,
            "message": (
                "Kesimpulan ini udah sesuai sama kondisi kamu? "
                "Atau mau tambahin cerita dulu sebelum kita lanjut?"
            ),
        }) or {}

        approved = bool(hitl_result.get("approved"))

        if not approved:
            # User mau tambahin cerita — simpan konteksnya, loop ulang
            bridge_msg = (
                "Oke, makasih udah mau cerita lebih! "
                "Aku coba rangkum ulang ya dengan info yang baru kamu kasih."
            )
            return {
                **ai_msg(bridge_msg),
                "counselor_response": [output.draft],
                "counselor_done": False,
                "hitl_status": "rejected",
                "hitl_input": hitl_result,
            }

        # User puas — tampilkan draft + bridge sebagai jembatan ke Prioritizer
        full_response = f"{output.draft}\n\n{output.bridge}"
        return {
            **ai_msg(full_response),
            "counselor_response": [full_response],
            "counselor_done": True,
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


def _generate_response(
    structured_llm,
    user_msg: str,
    raw_tasks: list,
    additional_context: str = "",
) -> CounselorOutput:
    """
    Satu LLM call menghasilkan CounselorOutput(draft, bridge) sekaligus.

    Args:
        structured_llm: llm.with_structured_output(CounselorOutput).
        user_msg: Pesan asli dari user.
        raw_tasks: Task yang sudah diekstrak Router.
        additional_context: Cerita tambahan dari user di loop sebelumnya.

    Returns:
        CounselorOutput dengan field draft dan bridge.
        Fallback ke CounselorOutput statis jika LLM error.
    """
    task_context = ""
    if raw_tasks:
        task_lines = "\n".join(
            f"- {t.get('title', t.get('raw_input', ''))}"
            for t in raw_tasks
        )
        task_context = f"\nTugas yang sudah terdeteksi dari cerita user:\n{task_lines}"

    extra_context = ""
    if additional_context:
        extra_context = f"\nInformasi tambahan dari user: {additional_context}"

    task_titles = [t.get("title", "") for t in raw_tasks if t.get("title")]
    task_list_str = ", ".join(task_titles[:3]) if task_titles else "tugas-tugasmu"

    prompt = f"""Kamu adalah teman curhat yang empatik, hangat, dan mudah diajak ngobrol.
Gunakan bahasa yang SAMA dengan user — kalau user pakai bahasa informal/gaul Indonesia, balas dengan gaya yang sama. Jangan kaku.

Kamu akan menghasilkan dua bagian sekaligus:

=== BAGIAN 1: draft ===
Respons empatik (maksimal 5-6 kalimat):
1. Validasi perasaan user — akui bahwa kondisinya memang berat, jangan langsung kasih solusi
2. Sebutkan masalah/tugas yang kamu tangkap dari ceritanya
3. Identifikasi apa yang paling bikin dia stress — deadline mepet? terlalu banyak? ga tau mulai dari mana?
4. Rumuskan kebutuhan praktisnya dalam 1 kalimat yang konkret
5. Akhiri SELALU dengan: "Kesimpulan ini udah pas sama kondisi kamu, atau mau tambahin sesuatu dulu?"

=== BAGIAN 2: bridge ===
1-2 kalimat transisi ke tahap penjadwalan. Ditampilkan HANYA jika user approve.
- Boleh kasih saran micro dulu (istirahat sebentar, tarik napas) sebelum tawarin jadwal
- Jangan ulangi validasi dari draft
- Jangan terlalu semangat/salesy
- Akhiri dengan tawaran konkret ke jadwal: sebutkan "{task_list_str}" secara natural
- Bukan pertanyaan — ini pernyataan/ajakan

JANGAN di draft:
- Langsung kasih solusi atau jadwal
- Terlalu formal atau terkesan seperti chatbot
- Lebih dari 6 kalimat

Curhatan user:
{user_msg}{task_context}{extra_context}"""

    try:
        return structured_llm.invoke([
            {"role": "system", "content": "Kamu asisten empatik yang membantu user mengelola stress dan tugas."},
            {"role": "user", "content": prompt},
        ])
    except Exception:
        task_mention = f" — {task_list_str}" if task_titles else ""
        return CounselorOutput(
            draft=(
                f"Waduh, kedengarannya berat banget nih{task_mention}. "
                "Wajar banget kalo kamu ngerasa overwhelmed, apalagi semuanya kayak dateng barengan. "
                "Yang paling penting sekarang adalah tau dulu mana yang paling mendesak buat diselesaiin. "
                "Kesimpulan ini udah pas sama kondisi kamu, atau mau tambahin sesuatu dulu?"
            ),
            bridge=(
                f"Oke, yuk sekarang kita susun {task_list_str} satu per satu "
                "biar ga semuanya kepikiran barengan."
            ),
        )