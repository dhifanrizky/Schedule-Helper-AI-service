from __future__ import annotations

from langgraph.types import interrupt as _langgraph_interrupt
from pydantic import BaseModel, Field
from typing import Optional
from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg, get_hitl_input, get_raw_tasks, get_metadata
from app.graph.types import CategoryType

# ---------------------------------------------------------------------------
# Agent 2: CounselorAgent — Sequential Per-Task Version
#
# ALUR:
#   Loop 0 (pertama):
#     - Validasi perasaan user HANYA jika ada ekspresi stres/pusing
#     - Kalimat penenang singkat
#     - Tanya task PERTAMA yang belum lengkap (output/hasil + deadline)
#
#   Loop 1..N (selanjutnya):
#     - Acknowledge jawaban user dengan hangat (tanpa validasi perasaan lagi)
#     - Enrich task yang baru dijawab
#     - Kalau masih ada task lain yang belum → tanya task berikutnya
#     - Kalau semua sudah → tampilkan ringkasan + minta konfirmasi
#
#   Loop konfirmasi (all_complete=True):
#     - User approve → counselor_done=True → lanjut prioritizer
#     - User ada tambahan/koreksi → enrich + done
#
# TASK is_complete = True jika:
#   - Sudah tahu OUTPUT/HASIL AKHIRNYA apa (laporan, database, presentasi, dll)
#   - Deadline sudah ada ATAU user konfirmasi belum ada
#   Tidak perlu: format, jumlah halaman, peserta, detail teknis
#
# HITL payload:
#   { "type": "counselor_chat", "message": "...", "is_confirmation": bool,
#     "current_task_index": int, "asked_questions": [...] }
#
# HITL resume:
#   { "approved": true/false, "additional_context": "teks balasan user" }
# ---------------------------------------------------------------------------

MAX_COUNSELOR_LOOPS = 5
DEBUG = True


def _debug(label: str, data):
    if DEBUG:
        print(f"\n[COUNSELOR DEBUG] {label}")
        print(data)


# ── Schema ────────────────────────────────────────────────────────────────────

class TaskEnrichment(BaseModel):
    task_id: str
    updated_title: Optional[str] = Field(
        default=None,
        description=(
            "Perjelas title jika user memberi info spesifik. "
            "Contoh: 'Tugas Basdat' → 'Bikin Database ERD'. Null jika sudah oke."
        )
    )
    updated_description: Optional[str] = Field(
        default=None,
        description=(
            "Isi dengan GABUNGAN deskripsi lama + info baru. Jangan buang info yang sudah ada."
            "Tulis: (1) output/hasil akhir yang diketahui, (2) deadline jika ada, "
            "(3) hal yang masih belum jelas. "
            "Null HANYA jika user tidak menyebut info baru sama sekali."
        )
    )
    updated_raw_time: Optional[str] = Field(
        default=None,
        description=(
            "Update HANYA jika user menyebut waktu/deadline baru. "
            "Tulis frasa persis user (misal: 'besok', 'minggu depan'). "
            "Null jika tidak ada info waktu baru."
        )
    )
    updated_category: Optional[CategoryType] = Field(
        default=None,
        description="Update jika konteks berubah. Null jika tidak ada perubahan."
    )
    is_complete: bool = Field(
        description=(
            "True jika task sudah punya: "
            "(1) output/hasil akhir yang jelas (laporan, database, presentasi, dll) "
            "DAN (2) deadline sudah ada ATAU user sudah bilang belum ada/tidak tahu. "
            "True juga jika user jawab singkat atau bilang 'ga tau', 'udah itu aja' — jangan paksa. "
            "False HANYA jika output task benar-benar tidak bisa diinfer sama sekali."
        )
    )


class CounselorOutput(BaseModel):
    enrichments: list[TaskEnrichment]
    all_complete: bool = Field(
        description="True jika SEMUA task is_complete=True."
    )
    reply: str = Field(
        description=(
            "Teks bubble chat ke user. Bahasa SAMA PERSIS dengan user.\n\n"
            "LOOP PERTAMA (is_first_loop=True di prompt):\n"
            "  1. Kalau user express stres/pusing: validasi perasaan 1 kalimat yang genuine\n"
            "     Contoh BAGUS: 'Tenang, kita bedah satu-satu biar kamu ga overwhelmed'\n"
            "     Contoh JELEK: 'Iya aku tau kamu pusing banget'\n"
            "  2. Kalau user tidak express stres: langsung ke poin 3\n"
            "  3. Kalimat penenang singkat + ajakan bantu\n"
            "     Contoh: 'Aku bantu atur ya, kita mulai dari [task pertama] dulu'\n"
            "  4. Tanya task PERTAMA: output/hasil + deadline dalam 1-2 kalimat natural\n"
            "     Contoh: 'Tugas basdat-nya ngerjain apa? (misal: bikin ERD, query SQL, laporan?) "
            "Terus deadline-nya kapan?'\n\n"
            "LOOP SELANJUTNYA (bukan first loop, belum all_complete):\n"
            "  1. Acknowledge jawaban user, 1 kalimat hangat — TANPA validasi perasaan lagi\n"
            "     Contoh: 'Oke, noted buat [task]!'\n"
            "  2. Langsung tanya task BERIKUTNYA yang belum lengkap\n"
            "     Format sama: output/hasil + deadline dalam 1 kalimat\n\n"
            "LOOP KONFIRMASI (all_complete=True):\n"
            "  1. Acknowledge jawaban terakhir, 1 kalimat\n"
            "  2. Tampilkan ringkasan semua task (title + output + deadline)\n"
            "  3. Tutup dengan: 'Udah bener semua? Atau ada yang mau diubah/ditambahin?'\n\n"
            "LARANGAN:\n"
            "  - JANGAN tulis 'Kesimpulan ini udah pas?' di loop non-konfirmasi\n"
            "  - JANGAN validasi perasaan lebih dari sekali\n"
            "  - JANGAN tanya lebih dari 1 task per loop\n"
            "  - JANGAN tanya: durasi, prioritas, peserta, format teknis\n"
            "  - Maks 5 kalimat total"
        )
    )
    next_incomplete_task_id: Optional[str] = Field(
        default=None,
        description=(
            "task_id dari task BERIKUTNYA yang belum is_complete=True. "
            "Null jika semua sudah lengkap."
        )
    )
    task_summary: str = Field(
        description=(
            "Ringkasan untuk ditampilkan saat konfirmasi akhir. "
            "Format: '• [Title]: [output/hasil], deadline: [waktu atau belum ada]' per baris."
        )
    )
    bridge: str = Field(
        description=(
            "1-2 kalimat ajakan ke penjadwalan. Ditampilkan HANYA saat approved. "
            "Sebutkan semua task. Energik tapi tidak lebay."
        )
    )


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Kamu adalah teman yang hangat dan helpful yang bantu user melengkapi info tugasnya.

FILOSOFI:
Kamu tahu user lagi overwhelmed. Tugasmu bukan interogasi — tapi bantu user merasa didengar
dan pelan-pelan keluarkan info yang diperlukan buat jadwalin tugasnya.

KAPAN TASK DIANGGAP LENGKAP (is_complete=True):
Task cukup kalau sudah ada DUA hal ini:
1. Output/hasil akhir yang jelas → "bikin laporan", "buat database ERD", "presentasi 10 menit"
2. Deadline → sudah disebutkan ATAU user bilang "belum ada", "ga tau", "masih lama"

Yang TIDAK perlu ditanya:
- Format file, jumlah halaman, template → tidak mempengaruhi penjadwalan
- Peserta meeting → tidak relevan
- Cara mengerjakan, tools yang dipakai → urusan user sendiri
- Prioritas → itu tugas Prioritizer

ATURAN TANYA:
- Satu task per giliran, jangan bombardir user dengan banyak pertanyaan
- Tanya output + deadline dalam satu napas yang natural
- Selalu kasih contoh jawaban dalam kurung
  BAD: "Bisa ceritain tugasnya lebih detail?"
  GOOD: "Tugas RPL-nya bikin apa? (misal: aplikasi, laporan, atau presentasi?) Terus deadline-nya kapan?"
- Kalau user jawab singkat atau ga lengkap tapi ada gambaran → is_complete=True, lanjut
- Kalau user bilang "ga tau" / "udah itu aja" → is_complete=True, jangan kejar

BAHASA:
Ikuti persis bahasa user. Santai dan gaul kalau user santai. Formal kalau user formal.
Jangan terlalu banyak tanda seru. Jangan lebay."""


# ── Factory ───────────────────────────────────────────────────────────────────

def make_counselor(llm, _interrupt=None, calendar_client=None):
    interrupt_fn = _interrupt if _interrupt is not None else _langgraph_interrupt
    counselor_llm = llm.with_structured_output(CounselorOutput)

    def run(state: AppState) -> dict:
        user_msg = last_message(state)
        raw_tasks = get_raw_tasks(state)
        previous_hitl = get_hitl_input(state) or {}
        loop_count = len(state.get("counselor_response") or [])

        _debug("LOOP", loop_count)
        _debug("USER MSG", user_msg)
        _debug("RAW TASKS (before enrich)", raw_tasks)

        # Safety: paksa selesai setelah MAX loop
        if loop_count >= MAX_COUNSELOR_LOOPS:
            _debug("FORCED COMPLETE", f"loop={loop_count}")
            forced_msg = _build_forced_completion_msg(raw_tasks, user_msg)
            return {
                **ai_msg(forced_msg),
                "counselor_response": [forced_msg],
                "counselor_done": True,
                "hitl_status": "approved",
                "hitl_input": None,
            }

        additional_context = previous_hitl.get("additional_context", "")
        # FIX bug 2: asked_questions pakai TITLE task, bukan UUID
        asked_questions = previous_hitl.get("asked_questions", [])
        current_task_index = previous_hitl.get("current_task_index", 0)
        is_first_loop = loop_count == 0

        # FIX bug 1: enrich DULU sebelum bangun prompt
        # Supaya LLM lihat deskripsi yang sudah terupdate, bukan yang lama
        if additional_context and raw_tasks:
            raw_tasks = _apply_pre_enrich(raw_tasks, additional_context, current_task_index)
            _debug("PRE-ENRICHED TASKS", raw_tasks)

        schedule_context = _fetch_schedule_context(calendar_client, state)

        # Prompt ke LLM — sekarang pakai raw_tasks yang sudah dienrich
        prompt_content = _build_prompt(
            user_msg=user_msg,
            raw_tasks=raw_tasks,
            additional_context=additional_context,
            asked_questions=asked_questions,
            current_task_index=current_task_index,
            is_first_loop=is_first_loop,
            loop_count=loop_count,
            schedule_context=schedule_context,
        )
        _debug("PROMPT", prompt_content)

        try:
            output = counselor_llm.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content},
            ])
        except Exception as e:
            _debug("LLM ERROR", e)
            output = _fallback_output(raw_tasks, is_first_loop)

        _debug("LLM OUTPUT", output)

        # Apply enrichment dari output LLM ke raw_tasks yang sudah pre-enriched
        updated_tasks = _apply_enrichments(raw_tasks, output.enrichments)
        _debug("UPDATED TASKS", updated_tasks)

        # FIX bug 3: cari next_index dari updated_tasks langsung, bukan dari enrichments
        next_index = _find_next_incomplete_from_tasks(updated_tasks, output.enrichments, current_task_index)

        # FIX bug 2: simpan TITLE task ke asked_questions, bukan UUID
        new_asked = list(asked_questions)
        if output.next_incomplete_task_id:
            # Cari title task berdasarkan task_id
            asked_title = next(
                (_get_field(t, "title") for t in updated_tasks
                 if _get_field(t, "task_id") == output.next_incomplete_task_id),
                output.next_incomplete_task_id  # fallback ke id jika tidak ketemu
            )
            if asked_title not in new_asked:
                new_asked.append(asked_title)

        is_confirmation = output.all_complete

        # HITL interrupt
        hitl_result = interrupt_fn({
            "type": "counselor_chat",
            "message": output.reply,
            "is_confirmation": is_confirmation,
            "current_task_index": next_index,
            "asked_questions": new_asked,
        }) or {}

        approved = bool(hitl_result.get("approved"))
        final_context = hitl_result.get("additional_context", "")

        if not approved:
            return {
                **ai_msg(output.reply),
                "raw_tasks": updated_tasks,
                "counselor_response": [output.reply],
                "counselor_done": False,
                "hitl_status": "rejected",
                "hitl_input": {
                    **hitl_result,
                    "asked_questions": new_asked,
                    "current_task_index": next_index,
                },
            }

        # Approved — enrich sekali lagi kalau ada info tambahan dari pesan approve
        final_tasks = updated_tasks
        if final_context and final_context.strip():
            final_tasks = _apply_final_context(counselor_llm, updated_tasks, final_context)
            _debug("FINAL TASKS (after enrich)", final_tasks)

        full_response = (
            f"{output.reply}\n\n"
            f"Ini catatan tugasnya:\n{output.task_summary}\n\n"
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


# ── Prompt Builder ────────────────────────────────────────────────────────────

def _build_prompt(
    user_msg: str,
    raw_tasks: list,
    additional_context: str,
    asked_questions: list[str],
    current_task_index: int,
    is_first_loop: bool,
    loop_count: int,
    schedule_context: str,
) -> str:
    task_context = _format_task_context(raw_tasks)
    n_tasks = len(raw_tasks)

    parts = [
        f"Pesan user: {user_msg}",
    ]

    if additional_context:
        parts.append(f"Jawaban/info tambahan dari user: {additional_context}")

    if schedule_context:
        parts.append(f"\nKonteks jadwal existing (jangan ubah):\n{schedule_context}")

    parts.append(f"\nTotal task terdeteksi: {n_tasks}")
    parts.append(f"Task list:\n{task_context}")

    if is_first_loop:
        parts.append("\n[INI LOOP PERTAMA — validasi perasaan jika ada ekspresi stres, lalu tanya task ke-1]")
    else:
        parts.append(f"\n[Loop ke-{loop_count + 1}. Task yang baru dijawab index ke-{current_task_index}.]")
        parts.append("Acknowledge jawaban user dulu, lalu lanjut tanya task berikutnya yang belum lengkap.")

    if asked_questions:
        parts.append(
            "\nTask yang sudah ditanyakan (jangan tanya lagi, lanjut ke task berikutnya):\n"
            + "\n".join(f"- {q}" for q in asked_questions)
        )

    if loop_count >= MAX_COUNSELOR_LOOPS - 1:
        parts.append(f"\n[LOOP TERAKHIR — set all_complete=True untuk semua task]")

    return "\n".join(parts)


def _fetch_schedule_context(calendar_client, state: AppState) -> str:
    if calendar_client is None:
        return ""

    metadata = get_metadata(state) or {}
    token = _extract_auth_token(metadata)

    try:
        schedules = calendar_client.list_schedules(token=token)
    except Exception as err:
        _debug("CALENDAR CONTEXT ERROR", err)
        return ""

    if not schedules:
        return "(tidak ada jadwal)"

    return _format_schedule_context(schedules)


def _format_schedule_context(schedules: list[dict]) -> str:
    lines: list[str] = []
    for item in schedules[:5]:
        title = str(item.get("title") or "(tanpa judul)")
        start_time = item.get("startTime") or item.get("start_time")
        deadline = item.get("deadline") or item.get("endTime")
        status = item.get("status") or "pending"
        time_bits = []
        if start_time:
            time_bits.append(f"mulai: {start_time}")
        if deadline:
            time_bits.append(f"selesai: {deadline}")
        time_part = f" ({', '.join(time_bits)})" if time_bits else ""
        lines.append(f"- {title} [{status}]{time_part}")

    return "\n".join(lines)


# ── Enrichment ────────────────────────────────────────────────────────────────

def _apply_enrichments(raw_tasks: list, enrichments: list[TaskEnrichment]) -> list:
    task_map: dict[str, dict] = {
        _get_field(t, "task_id"): _to_dict(t)
        for t in raw_tasks
        if _get_field(t, "task_id")
    }

    for e in enrichments:
        tid = e.task_id
        if tid not in task_map:
            continue
        ex = task_map[tid]

        if e.updated_title and e.updated_title.strip():
            ex["title"] = e.updated_title.strip()

        if e.updated_description and e.updated_description.strip():
            ex["description"] = e.updated_description.strip()

        if e.updated_raw_time is not None:
            ex["raw_time"] = e.updated_raw_time.strip() if e.updated_raw_time.strip() else None

        if e.updated_category is not None:
            ex["category"] = e.updated_category

        task_map[tid] = ex

    return list(task_map.values())


def _apply_final_context(counselor_llm, raw_tasks: list, final_context: str) -> list:
    """Enrich dengan info yang user kasih saat approve (misal koreksi atau tambahan)."""

    class QuickItem(BaseModel):
        task_id: str
        updated_description: Optional[str] = Field(default=None)
        updated_raw_time: Optional[str] = Field(default=None)

    class QuickOut(BaseModel):
        tasks: list[QuickItem]

    try:
        result = counselor_llm.with_structured_output(QuickOut).invoke([
            {"role": "system", "content": "Update task dengan info koreksi/tambahan dari user. Jangan overwrite data valid yang sudah ada."},
            {"role": "user", "content": (
                f"Info koreksi/tambahan: {final_context}\n\n"
                f"Tasks:\n{_format_task_context(raw_tasks)}"
            )},
        ])
        task_map = {_get_field(t, "task_id"): _to_dict(t) for t in raw_tasks if _get_field(t, "task_id")}
        for item in result.tasks:
            if item.task_id not in task_map:
                continue
            ex = task_map[item.task_id]
            if item.updated_description and item.updated_description.strip():
                ex["description"] = item.updated_description.strip()
            if item.updated_raw_time is not None:
                ex["raw_time"] = item.updated_raw_time.strip() if item.updated_raw_time.strip() else None
            task_map[item.task_id] = ex
        return list(task_map.values())
    except Exception:
        return raw_tasks


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_next_incomplete_index(enrichments: list[TaskEnrichment], current_index: int) -> int:
    """Cari index task berikutnya yang belum complete, mulai dari current+1."""
    for i, e in enumerate(enrichments):
        if i > current_index and not e.is_complete:
            return i
    return current_index


def _apply_pre_enrich(raw_tasks: list, additional_context: str, current_task_index: int) -> list:
    """
    FIX bug 1: Update deskripsi task yang BARU DITANYA (index = current_task_index)
    dengan jawaban user (additional_context) sebelum prompt dibuat.
    Ini deterministik — tidak pakai LLM, cukup append ke description yang ada.
    LLM enrich yang lebih canggih tetap dilakukan via _apply_enrichments setelahnya.
    """
    if not raw_tasks or not additional_context:
        return raw_tasks

    target_idx = min(current_task_index, len(raw_tasks) - 1)
    result = [_to_dict(t) for t in raw_tasks]
    target = result[target_idx]

    current_desc = target.get("description") or ""
    # Append jawaban user ke deskripsi — LLM akan refinement setelahnya
    if current_desc and additional_context not in current_desc:
        target["description"] = f"{current_desc}; jawaban user: {additional_context}"
    elif not current_desc:
        target["description"] = additional_context

    result[target_idx] = target
    return result


def _find_next_incomplete_from_tasks(
    updated_tasks: list,
    enrichments: list[TaskEnrichment],
    current_index: int,
) -> int:
    """
    FIX bug 3: Cari index task berikutnya yang belum complete.
    Pakai is_complete dari enrichments yang di-map ke task_id,
    lalu cari task di updated_tasks mulai dari current_index + 1.
    """
    # Buat map task_id -> is_complete dari enrichments
    complete_map: dict[str, bool] = {e.task_id: e.is_complete for e in enrichments}

    for i, t in enumerate(updated_tasks):
        if i <= current_index:
            continue
        tid = _get_field(t, "task_id")
        # Kalau tidak ada di complete_map, anggap belum complete
        if not complete_map.get(tid, False):
            return i

    return current_index  # semua sudah complete atau tidak ada yang lebih tinggi


def _build_forced_completion_msg(raw_tasks: list, user_msg: str) -> str:
    titles = [_get_field(t, "title") or "task" for t in raw_tasks]
    task_list = " dan ".join(titles) if len(titles) <= 2 else ", ".join(titles[:-1]) + f", dan {titles[-1]}"
    return (
        f"Oke, aku udah catat semuanya. "
        f"Yuk kita langsung atur jadwal buat {task_list}!"
    )


def _format_task_context(raw_tasks: list) -> str:
    if not raw_tasks:
        return "(tidak ada task)"
    lines = []
    for i, t in enumerate(raw_tasks):
        tid = _get_field(t, "task_id") or "?"
        title = _get_field(t, "title") or "(no title)"
        desc = _get_field(t, "description") or "(belum ada deskripsi)"
        raw_time = _get_field(t, "raw_time")
        category = _get_field(t, "category") or "biasa"
        time_str = f"deadline: {raw_time}" if raw_time else "deadline: BELUM ADA"
        lines.append(
            f"[{i}] task_id={tid} | {title} | kategori: {category} | {time_str}\n"
            f"     deskripsi: {desc}"
        )
    return "\n".join(lines)


def _fallback_output(raw_tasks: list, is_first_loop: bool) -> CounselorOutput:
    titles = [_get_field(t, "title") or "task" for t in raw_tasks]
    task_list = " dan ".join(titles[:2])
    first_task = titles[0] if titles else "tugasmu"

    reply = (
        f"Tenang, aku bantu atur ya. Kita mulai dari {first_task} dulu — "
        f"kira-kira ngerjain apa dan deadline-nya kapan?"
        if is_first_loop else
        f"Makasih, noted! Lanjut ke task berikutnya ya — "
        f"kira-kira ngerjain apa dan deadline-nya kapan?"
    )

    return CounselorOutput(
        enrichments=[
            TaskEnrichment(
                task_id=_get_field(t, "task_id") or "?",
                is_complete=False,
            )
            for t in raw_tasks
        ],
        all_complete=False,
        reply=reply,
        next_incomplete_task_id=_get_field(raw_tasks[0], "task_id") if raw_tasks else None,
        task_summary="\n".join(
            f"• {_get_field(t, 'title') or 'Task'}: {(_get_field(t, 'description') or '-')[:60]}"
            for t in raw_tasks
        ),
        bridge=f"Yuk kita jadwalin {task_list} sekarang.",
    )


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


def _extract_auth_token(metadata: dict) -> str | None:
    for key in ("auth_token", "access_token", "authorization"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
