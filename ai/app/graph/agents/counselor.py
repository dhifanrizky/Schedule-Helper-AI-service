from __future__ import annotations

from langgraph.types import interrupt as _langgraph_interrupt
from pydantic import BaseModel, Field
from typing import Optional
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg, get_hitl_input, get_raw_tasks
from app.graph.types import CategoryType

# ---------------------------------------------------------------------------
# Agent 2: CounselorAgent
#
# TUGAS:
#   Lengkapi RawTask dari Router sebelum diteruskan ke Prioritizer.
#   RawTask yang perlu dilengkapi: title (jika vague) dan description
#   (jika scope/konteks belum jelas). Field lain (raw_time, category,
#   raw_input) TIDAK ditanya — bisa diinfer atau memang opsional.
#
# ALUR PER LOOP:
#   Step A — Gap check  : evaluasi field mana yang masih kurang
#   Step B — Draft      : buat respons dengan pertanyaan spesifik
#   HITL                : pause, kirim draft ke user, tunggu /resume
#   Jika approved       : enrich + selesai
#   Jika rejected       : enrich + loop lagi (HANYA tanya yang belum dijawab)
#
# ANTI-LOOP BERULANG:
#   Gap check WAJIB cek riwayat pertanyaan sebelumnya (asked_questions).
#   Kalau user sudah jawab → tandai is_complete=True, JANGAN tanya lagi.
#   Kalau user bilang "ga ada info lain" / "udah itu aja" → is_complete=True.
#
# KOMPONEN RawTask yang bisa dilengkapi Counselor:
#   - title       : perjelas jika masih vague ("banyak tugas" → "Tugas RPL chapter 3")
#   - description : isi scope/konteks yang sebelumnya kosong atau "tidak diketahui"
#   - raw_time    : update HANYA jika user menyebut waktu baru
#   - category    : update jika konteks berubah
#   (task_id dan raw_input TIDAK diubah)
# ---------------------------------------------------------------------------

MAX_COUNSELOR_LOOPS = 3


# ── Schema Gap Analysis ───────────────────────────────────────────────────────

class TaskGapItem(BaseModel):
    task_id: str
    title: str
    is_complete: bool = Field(
        description=(
            "True jika task sudah punya title yang jelas DAN description yang cukup "
            "untuk dijadwalkan. True juga jika user sudah menjawab pertanyaan sebelumnya "
            "tentang task ini (walau singkat), atau user bilang tidak ada info tambahan."
        )
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description=(
            "Hanya isi jika is_complete=False. "
            "Satu item = satu pertanyaan yang akan ditanyakan ke user. "
            "JANGAN duplikat pertanyaan yang sudah ada di asked_questions. "
            "JANGAN tanya: deadline/waktu, durasi, prioritas — itu urusan Prioritizer. "
            "Yang valid: scope task jika benar-benar tidak jelas sama sekali, "
            "jenis output jika tidak bisa diinfer sama sekali dari konteks."
        )
    )


class TaskGapAnalysis(BaseModel):
    gaps: list[TaskGapItem]
    overall_complete: bool = Field(
        description="True jika semua task is_complete=True."
    )


# ── Schema Draft ──────────────────────────────────────────────────────────────

class CounselorDraft(BaseModel):
    draft: str = Field(
        description=(
            "Respons ke user. Struktur:\n"
            "1. Empati singkat (1 kalimat, genuine, tidak generik)\n"
            "2. Sebutkan semua task yang sudah dipahami\n"
            "3. JIKA ada yang kurang: tanya SATU hal per task — sebut nama tasknya\n"
            "4. JIKA semua lengkap: ringkasan singkat semua task (title + info utama)\n"
            "5. Tutup dengan: 'Kesimpulan ini udah pas, atau mau tambahin sesuatu dulu?'\n"
            "Bahasa = sama persis dengan user. Maks 7 kalimat. Jangan kasih solusi."
        )
    )
    bridge: str = Field(
        description=(
            "1-2 kalimat ajakan ke penjadwalan. Ditampilkan HANYA saat approved. "
            "Sebutkan semua task yang akan dijadwalkan. Bukan pertanyaan."
        )
    )
    task_summary: str = Field(
        description=(
            "Ringkasan singkat semua task dalam format yang mudah dibaca user. "
            "Format: '• [Nama Task]: [info utama yang sudah terkumpul]' per baris. "
            "Ini ditampilkan saat approved agar user bisa konfirmasi semua data sudah benar. "
            "Sertakan: title, scope/deskripsi singkat, waktu jika ada. "
            "Contoh: '• Tugas RPL - Membuat Aplikasi: scope bikin CRUD sederhana, deadline besok'"
        )
    )


# ── Schema Enrichment ─────────────────────────────────────────────────────────

class EnrichedTaskItem(BaseModel):
    task_id: str
    title: str = Field(description="Perjelas jika sebelumnya vague. Pertahankan jika sudah oke.")
    description: str = Field(
        description=(
            "Update dengan info baru dari user. "
            "Sertakan: apa yang harus dikerjakan, feeling user, hal yang masih belum jelas. "
            "Jika user bilang tidak ada info tambahan, tulis deskripsi terbaik dari data yang ada."
        )
    )
    raw_time: Optional[str] = Field(
        default=None,
        description="Update HANYA jika user menyebut waktu/deadline baru. Null jika tidak."
    )
    category: CategoryType


class EnrichedTasksOutput(BaseModel):
    enriched_tasks: list[EnrichedTaskItem]


# ── Factory ───────────────────────────────────────────────────────────────────

def make_counselor(llm, _interrupt=None):
    interrupt_fn = _interrupt if _interrupt is not None else _langgraph_interrupt
    gap_llm = llm.with_structured_output(TaskGapAnalysis)
    draft_llm = llm.with_structured_output(CounselorDraft)
    enrichment_llm = llm.with_structured_output(EnrichedTasksOutput)

    def run(state: AppState) -> dict:
        user_msg = last_message(state)
        raw_tasks = get_raw_tasks(state)
        previous_hitl = get_hitl_input(state) or {}
        loop_count = len(state.get("counselor_response") or [])

        # Safety: paksa selesai setelah MAX loop
        if loop_count >= MAX_COUNSELOR_LOOPS:
            forced_msg = (
                "Oke, aku udah cukup paham situasimu. "
                "Yuk kita mulai atur satu per satu!"
            )
            return {
                **ai_msg(forced_msg),
                "counselor_response": [forced_msg],
                "counselor_done": True,
                "hitl_status": "approved",
                "hitl_input": None,
            }

        additional_context = previous_hitl.get("additional_context", "")
        # Kumpulkan riwayat pertanyaan yang sudah pernah ditanyakan
        asked_questions = previous_hitl.get("asked_questions", [])

        # Enrich tasks dulu kalau ada info baru dari loop sebelumnya
        current_tasks = raw_tasks
        if additional_context and raw_tasks:
            current_tasks = _enrich_tasks(
                enrichment_llm, raw_tasks, additional_context, user_msg
            )

        # Step A: evaluasi gap — dengan konteks pertanyaan yang sudah ditanya
        gap_analysis = _evaluate_gaps(
            gap_llm, current_tasks, user_msg, additional_context, asked_questions
        )

        # Step B: generate draft dengan data gap eksplisit
        output = _generate_draft(
            draft_llm, user_msg, current_tasks, gap_analysis, additional_context
        )

        has_missing = not gap_analysis.overall_complete
        missing_per_task = [
            {"task_id": g.task_id, "title": g.title, "missing": g.missing_info}
            for g in gap_analysis.gaps
            if not g.is_complete
        ]

        # Kumpulkan pertanyaan yang baru ditanyakan di loop ini
        new_questions = [
            f"{g.title}: {', '.join(g.missing_info)}"
            for g in gap_analysis.gaps
            if not g.is_complete and g.missing_info
        ]
        all_asked = asked_questions + new_questions

        hitl_result = interrupt_fn({
            "type": "counselor_review",
            "draft": output.draft,
            "message": (
                "Ada info yang perlu dilengkapi. Jawab yuk!"
                if has_missing
                else "Semua info sudah lengkap. Lanjut ke penjadwalan?"
            ),
            "has_missing_info": has_missing,
            "missing_per_task": missing_per_task,
            "asked_questions": all_asked,
        }) or {}

        approved = bool(hitl_result.get("approved"))

        if not approved:
            return {
                **ai_msg(
                    "Makasih udah mau cerita lebih! "
                    "Aku update catatannya ya."
                ),
                "raw_tasks": current_tasks,
                "counselor_response": [output.draft],
                "counselor_done": False,
                "hitl_status": "rejected",
                "hitl_input": {
                    **hitl_result,
                    "asked_questions": all_asked,  # teruskan riwayat ke loop berikutnya
                },
            }

        # Approved — enrich sekali lagi kalau ada context baru dari approved
        final_context = hitl_result.get("additional_context", "")
        final_tasks = current_tasks
        if final_context and current_tasks:
            final_tasks = _enrich_tasks(
                enrichment_llm, current_tasks, final_context, user_msg
            )

        # Pesan akhir: draft + task summary + bridge
        full_response = (
            f"{output.draft}\n\n"
            f"Ini ringkasan task yang akan dijadwalkan:\n{output.task_summary}\n\n"
            f"{output.bridge}"
        )
        return {
            **ai_msg(full_response),
            "raw_tasks": final_tasks,
            "counselor_response": [full_response],
            "counselor_done": True,
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


# ── Step A: Gap Evaluation ────────────────────────────────────────────────────

def _evaluate_gaps(
    gap_llm,
    raw_tasks: list,
    user_msg: str,
    additional_context: str,
    asked_questions: list[str],
) -> TaskGapAnalysis:
    task_context = _format_task_context(raw_tasks)
    extra = f"\nInfo tambahan dari user: {additional_context}" if additional_context else ""
    asked_str = (
        "\nPertanyaan yang SUDAH ditanyakan sebelumnya (JANGAN tanya lagi):\n"
        + "\n".join(f"- {q}" for q in asked_questions)
        if asked_questions else ""
    )

    prompt = f"""Evaluasi apakah setiap task sudah cukup untuk dijadwalkan.

Curhatan user: {user_msg}{extra}

Tasks:
{task_context}{asked_str}

ATURAN:
- is_complete = True jika title jelas DAN description cukup menggambarkan apa yang harus dikerjakan
- is_complete = True jika user sudah menjawab pertanyaan sebelumnya (walau singkat/tidak lengkap)
- is_complete = True jika user bilang "udah itu aja", "ga ada lagi", "cuma itu" dst
- missing_info: HANYA isi hal yang benar-benar tidak bisa diinfer sama sekali
- JANGAN tanya lagi hal yang ada di "Pertanyaan yang SUDAH ditanyakan"
- JANGAN tanya: waktu/deadline, durasi, prioritas — itu urusan Prioritizer"""

    try:
        return gap_llm.invoke([
            {"role": "system", "content": "Evaluasi kelengkapan task untuk penjadwalan."},
            {"role": "user", "content": prompt},
        ])
    except Exception:
        return TaskGapAnalysis(
            gaps=[
                TaskGapItem(
                    task_id=_get_field(t, "task_id") or "?",
                    title=_get_field(t, "title") or "Task",
                    is_complete=True,
                    missing_info=[],
                )
                for t in raw_tasks
            ],
            overall_complete=True,
        )


# ── Step B: Draft Generation ──────────────────────────────────────────────────

def _generate_draft(
    draft_llm,
    user_msg: str,
    raw_tasks: list,
    gap_analysis: TaskGapAnalysis,
    additional_context: str,
) -> CounselorDraft:
    task_context = _format_task_context(raw_tasks)
    extra = f"\nInfo tambahan dari user: {additional_context}" if additional_context else ""

    incomplete = [g for g in gap_analysis.gaps if not g.is_complete]
    if incomplete:
        gap_summary = "Task yang BELUM lengkap — tanyakan ini:\n" + "\n".join(
            f"- {g.title}: tanyakan → {', '.join(g.missing_info)}"
            for g in incomplete
        )
    else:
        gap_summary = "Semua task sudah lengkap — buat ringkasan dan minta konfirmasi."

    task_titles = [_get_field(t, "title") for t in raw_tasks if _get_field(t, "title")]
    task_list_str = ", ".join(task_titles) if task_titles else "tugas-tugasmu"

    prompt = f"""Kamu teman curhat yang empatik dan membantu user melengkapi info tugasnya.
Bahasa: SAMA dengan user (informal jika user informal).

User: {user_msg}{extra}

Tasks terdeteksi:
{task_context}

Hasil evaluasi:
{gap_summary}

INSTRUKSI DRAFT:
1. Empati genuine 1 kalimat (bukan "Oh ya" atau "Wah")
2. Sebutkan semua task yang sudah dipahami
3. Jika ada yang belum lengkap: tanya SATU hal per task yang belum — sebut nama tasknya
4. Jika semua lengkap: buat ringkasan singkat semua task beserta info yang sudah terkumpul
5. Tutup dengan: "Kesimpulan ini udah pas, atau mau tambahin sesuatu dulu?"

TASK_SUMMARY (untuk ditampilkan saat approved):
Buat ringkasan per task dalam format bullet. Sertakan: title, scope, waktu jika ada.
Contoh: "• Tugas RPL: bikin aplikasi CRUD, deadline besok"

BRIDGE:
Ajakan konkret ke penjadwalan. Sebutkan "{task_list_str}"."""

    try:
        return draft_llm.invoke([
            {"role": "system", "content": "Asisten empatik yang membantu user melengkapi info tugas."},
            {"role": "user", "content": prompt},
        ])
    except Exception:
        return CounselorDraft(
            draft=(
                f"Berat banget ya, {task_list_str} semua numpuk. "
                "Bisa ceritain lebih detail biar aku bisa bantu? "
                "Kesimpulan ini udah pas, atau mau tambahin sesuatu dulu?"
            ),
            bridge=f"Yuk sekarang kita atur {task_list_str} satu per satu.",
            task_summary="\n".join(
                f"• {_get_field(t, 'title') or 'Task'}: {_get_field(t, 'description') or '-'}"
                for t in raw_tasks
            ),
        )


# ── Enrichment ────────────────────────────────────────────────────────────────

def _enrich_tasks(
    enrichment_llm,
    raw_tasks: list,
    additional_context: str,
    original_user_msg: str,
) -> list:
    task_context = _format_task_context(raw_tasks)

    prompt = f"""Update field task berdasarkan info baru dari user.

ATURAN:
- Hanya update field yang berubah/bertambah dari info baru
- Pertahankan data yang sudah valid
- title: perjelas jika sebelumnya vague dan info baru memungkinkan
- description: update dengan info baru, sertakan apa yang masih belum diketahui
- raw_time: update HANYA jika user sebut waktu baru yang spesifik
- Jika user bilang "udah itu aja" atau tidak ada info baru: pertahankan data lama,
  hanya update description untuk mencerminkan bahwa ini memang batasnya info yang ada

Info awal: {original_user_msg}
Info baru: {additional_context}

Tasks saat ini:
{task_context}"""

    try:
        result = enrichment_llm.invoke([
            {"role": "system", "content": "Update task berdasarkan info baru. Jangan overwrite data valid."},
            {"role": "user", "content": prompt},
        ])
        enriched = result.enriched_tasks if hasattr(result, "enriched_tasks") else []
        if not enriched:
            return raw_tasks

        task_map = {_get_field(t, "task_id"): _to_dict(t) for t in raw_tasks}
        for item in enriched:
            tid = item.task_id
            if tid not in task_map:
                continue
            existing = task_map[tid]
            if item.title and item.title.strip():
                existing["title"] = item.title
            if item.description and item.description.strip():
                existing["description"] = item.description
            if item.raw_time is not None:
                existing["raw_time"] = item.raw_time
            if item.category:
                existing["category"] = item.category
            task_map[tid] = existing

        return list(task_map.values())
    except Exception:
        return raw_tasks


# ── Utilities ─────────────────────────────────────────────────────────────────

def _get_field(task, field: str):
    if hasattr(task, field):
        return getattr(task, field)
    if isinstance(task, dict):
        return task.get(field)
    return None


def _to_dict(task) -> dict:
    if hasattr(task, "model_dump"):
        return task.model_dump()
    if isinstance(task, dict):
        return dict(task)
    return {}


def _format_task_context(raw_tasks: list) -> str:
    if not raw_tasks:
        return "(tidak ada task)"
    lines = []
    for t in raw_tasks:
        tid = _get_field(t, "task_id") or "?"
        title = _get_field(t, "title") or "(no title)"
        desc = _get_field(t, "description") or "(belum ada deskripsi)"
        raw_time = _get_field(t, "raw_time")
        category = _get_field(t, "category") or "biasa"
        time_str = f", waktu: {raw_time}" if raw_time else ""
        lines.append(
            f"- [{tid}] {title} (kategori: {category}{time_str})\n"
            f"  deskripsi: {desc}"
        )
    return "\n".join(lines)