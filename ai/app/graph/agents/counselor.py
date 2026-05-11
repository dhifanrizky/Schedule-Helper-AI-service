from __future__ import annotations

from uuid import uuid4
from typing import Optional
from pydantic import BaseModel, Field

from langgraph.types import interrupt as _langgraph_interrupt

from app.graph.state import AppState
from app.graph.agents.helpers import last_message, ai_msg, get_hitl_input, get_raw_tasks, get_metadata
from app.graph.types import CategoryType

# =============================================================================
# Agent 2: CounselorAgent
# =============================================================================
#
# ATURAN KERAS:
#   - SATU interrupt per run. Tidak pernah lebih dari 1.
#   - State internal disimpan di hitl_input.
#   - Loop dikendalikan routing.py (counselor_done=False -> panggil lagi).
#
# ALUR:
#   /chat pertama
#     -> router -> counselor(phase=init)
#     -> kalau vague: interrupt discovery (tanya tugas apa aja)
#     -> kalau spesifik: interrupt detail task[0]
#
#   /resume (user jawab)
#     -> counselor(phase=detail atau review)
#     -> detail: parse jawaban, simpan, cari task berikutnya
#       -> ada task lagi: interrupt tanya task berikutnya
#       -> semua lengkap: interrupt review
#     -> review: cek approved
#       -> approved: counselor_done=True
#       -> tidak: update desc, interrupt review baru
#
# HITL PAYLOAD:
#   chat:   {"type":"counselor_chat",   "message":str, "phase":"chat"}
#   review: {"type":"counselor_review", "message":str, "phase":"review", "task_summary":[...]}
#
# RESUME PAYLOAD dari user:
#   chat:   {"additional_context": "jawaban user"}           <- TANPA approved
#   review: {"approved": bool, "additional_context": "..."}  <- ADA approved
#
# =============================================================================

MAX_LOOPS  = 12
MAX_REVIEW = 3
DEBUG      = True


def _log(label: str, data=None):
    if DEBUG:
        print(f"\n[COUNSELOR] {label}")
        if data is not None:
            print(data)


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class DiscoveredTask(BaseModel):
    title: str = Field(description=(
        "Nama task singkat dan jelas. "
        "Contoh: 'Tugas Basis Data', 'Laporan Praktikum Kimia'. "
        "Satu task per item."
    ))
    raw_time: str | None = Field(default=None, description=(
        "Frasa deadline jika user sebutkan. Null jika tidak ada."
    ))
    raw_input: str = Field(description="Kalimat asli user untuk task ini.")
    category: CategoryType = Field(default="biasa", description=(
        "'serius' untuk tugas berat, 'santai' ringan, 'biasa' umum."
    ))


class DiscoveryOutput(BaseModel):
    tasks: list[DiscoveredTask] = Field(description=(
        "Daftar task dari user. Satu item per task berbeda. "
        "'basdat sama RPL' = 2 item terpisah."
    ))


class TaskDetailParsed(BaseModel):
    parsed_description: str | None = Field(default=None, description=(
        "Deskripsi dari jawaban user: output tugas, perasaan user, catatan khusus. "
        "Tulis ulang dengan jelas. Null hanya jika user tidak menyebut apapun."
    ))
    parsed_raw_time: str | None = Field(default=None, description=(
        "Frasa deadline dari user persis: 'besok', 'minggu depan'. "
        "Null jika tidak disebutkan."
    ))
    deadline_confirmed_none: bool = Field(default=False, description=(
        "True HANYA jika user eksplisit bilang: 'ga ada deadline', "
        "'belum tau', 'masih lama', 'ga ada'. "
        "False jika user tidak menyebut soal deadline sama sekali."
    ))


class ReviewEnrichItem(BaseModel):
    task_id: str
    updated_description: str | None = Field(default=None, description=(
        "Gabungan deskripsi lama + info baru. Jangan hapus info lama. "
        "Null jika tidak ada info baru untuk task ini."
    ))
    updated_raw_time: str | None = Field(default=None, description=(
        "Update deadline jika user sebut info raw time / deadline baru. Null jika tidak ada perubahan."
    ))


class ReviewEnrichOutput(BaseModel):
    updates: list[ReviewEnrichItem]


# ── System Prompts ────────────────────────────────────────────────────────────

DISCOVERY_SYSTEM = """Ekstrak setiap task yang disebutkan user menjadi item terpisah.

Aturan:
- Satu task = satu item
- Nama berbeda = item terpisah ('RPL' dan 'basdat' = 2 item)
- Gunakan bahasa persis user untuk title
- Jangan gabungkan task berbeda
- Jangan tambahkan task yang tidak disebutkan user"""

DETAIL_PARSE_SYSTEM = """Ekstrak informasi dari jawaban user tentang sebuah tugas.

Pisahkan:
1. Deskripsi: output/hasil tugas + perasaan user + catatan apapun
2. Deadline: frasa waktu dari ucapan user
3. Konfirmasi tidak ada deadline

Aturan:
- deadline_confirmed_none=True HANYA jika user eksplisit bilang tidak ada deadline
- Jangan asumsikan deadline dari konteks
- Isi parsed_description selengkap mungkin dari apapun yang user ceritakan"""

REVIEW_SYSTEM = """Kamu adalah teman yang hangat dan supportif, membantu user yang lagi overwhelmed dengan kegiatannya.

Gunakan bahasa PERSIS sama dengan user — santai dan gaul kalau user santai, lebih formal kalau user formal.

Output harus berisi DUA bagian dipisah dengan |||:

BAGIAN 1 — Ringkasan yang meyakinkan:
- Buka dengan kalimat yang menegaskan bahwa kamu SUDAH berhasil mencatat semuanya.
  Contoh bagus: "Oke, aku udah catet semua yang lo ceritain tadi ya —"
  Contoh bagus: "Siap, semuanya udah aku rekap nih:"
  Contoh JELEK: "Wah pusing ya..." (jangan mulai dengan validasi perasaan di sini)
- Lanjutkan dengan bullet ringkasan per item: nama kegiatan, apa yang dikerjakan, target/deadline
- Nada: meyakinkan, seperti teman yang bilang "tenang, aku udah pegang semuanya"
- Maksimal 6 kalimat

BAGIAN 2 — Penawaran untuk tambah cerita (BUKAN pertanyaan langsung):
- Ini adalah PENAWARAN, bukan interogasi. User boleh iya boleh tidak.
- WAJIB sebut SEMUA task yang ada di daftar — jangan highlight hanya satu task saja.
  Contoh bagus: "Kalau lo mau ceritain lebih — misalnya soal PEMDAS-nya seberapa susah, atau meeting-nya gimana persiapannya, atau tugas lain yang bikin worried — boleh banget."
  Contoh JELEK: "Mau ceritain soal PEMDAS-nya?" (hanya menyebut satu task, padahal ada lebih dari satu)
- Sebutkan beberapa contoh hal yang bisa ditambahin: perasaan user terhadap masing-masing task, seberapa sulit / mudah, progress udah sampai mana, yang bikin was-was atau stuck — sesuaikan dengan konteks semua task.
- Tutup dengan kalimat yang membebaskan user: kalau udah cukup, bisa langsung lanjut.
  Contoh: "Tapi kalau udah oke dan mau langsung lanjut juga gapapa kok!"
  Contoh: "Atau kalau udah pas semua, kita gas aja langsung!"
- Tone: ringan, tidak memaksa, seperti teman yang nawarin ngobrol lebih lanjut
- Maksimal 3 kalimat

Format output PERSIS: [ringkasan]|||[penawaran]
Tidak ada teks lain di luar format ini."""

FEEDBACK_SYSTEM = """Kamu adalah teman yang supportif merespons cerita tambahan dari user.
 
User baru saja mengirim info tambahan. BACA DULU konteksnya — respons harus sesuai dengan JENIS info yang dikirim.
 
LANGKAH PERTAMA — DETEKSI JENIS PESAN:
A. NETRAL / UPDATE INFO: user hanya update fakta tanpa ekspresi emosi
   Ciri: update deadline, koreksi data, tambah info teknis, tanpa kata stres/panik/capek/susah
   Contoh: "deadlinenya ternyata besok", "eh salah, itu 15 soal bukan 10", "meetingnya jam 3"
   → RESPONS: acknowledge singkat saja, JANGAN tenangin, JANGAN kasih saran apapun
   → Format: 1 kalimat acknowledge yang natural
   → Contoh respons: "Siap, noted!" / "Oke, udah aku update." / "Got it, deadlinenya besok ya."
 
B. KESULITAN / PANIK / STRESS: ada ekspresi emosi negatif yang jelas
   Ciri: ada kata panik, stress, susah, takut, ga bisa, overwhelmed, capek, pusing
   → RESPONS: validasi perasaan (1 kalimat) + saran micro fisik/mental + sebut sistem akan bantu
   → Saran micro yang boleh: tarik napas, minum air, istirahat bentar, tidur sebentar
   → DILARANG: saran cara kerjain tugas, urutan pengerjaan, prioritas — itu tugas agent lain
   → Contoh: "Wajar panik, tapi tarik napas dulu — nanti kita atur bareng sama sistemnya."
 
C. PROGRESS / PENCAPAIAN: user cerita hal positif
   Ciri: udah selesai sebagian, ada progress, pencapaian kecil
   → RESPONS: puji dengan tulus dan spesifik, tidak lebay, 1 kalimat
 
D. CAMPURAN: ada update info sekaligus ekspresi emosi
   → RESPONS: acknowledge updatenya dulu, lalu validasi emosinya — tetap tanpa saran pengerjaan
 
ATURAN KERAS (berlaku untuk semua jenis):
- DILARANG: saran cara mengerjakan tugas, urutan pengerjaan, prioritas
- Gunakan bahasa PERSIS sama dengan user
- Maksimal 2 kalimat, singkat dan genuine
- Jangan ulangi info user secara harfiah
 
Contoh BAGUS:
- "deadlinenya ternyata besok" (netral) → "Siap, noted!"
- "eh salah, meetingnya 2 jam bukan 3" (netral) → "Oke, udah aku koreksi."
- "panik banget deadline besok, belum bisa" (stress) → "Wajar panik, tapi tarik napas dulu — nanti sistemnya bantu atur biar lebih jelas."
- "udah cicil 5 soal" (progress) → "Nice, udah ada progresnya!"
- "ternyata deadlinenya besok dan gua panik" (campuran) → "Noted deadlinenya — wajar panik, tapi tenang, nanti kita atur bareng."
 
Contoh JELEK — JANGAN DITIRU:
- Update deadline → "Tenang ya, pasti bisa kok!" ← JANGAN tenangin kalau tidak perlu
- Update info → "Wah berat juga ya" ← JANGAN dramatisir
- Stress → "Coba kerjain yang gampang dulu" ← DILARANG saran pengerjaan
 
Output hanya kalimat respons saja, tanpa label atau teks tambahan."""

REVIEW_ENRICH_SYSTEM = """Update deskripsi task dari cerita tambahan user.
Gabungkan info lama dengan info baru. Jangan hapus deskripsi lama yang valid.
Hanya update task yang relevan dengan cerita user."""


# ── Generic Utils ─────────────────────────────────────────────────────────────

def _coerce(task) -> dict:
    """Konversi task (Pydantic model atau dict) ke dict biasa."""
    if hasattr(task, "model_dump"):
        return task.model_dump()
    return dict(task) if isinstance(task, dict) else {}


def _get(task, field: str):
    """Ambil field dari task tanpa peduli tipenya (model atau dict)."""
    if hasattr(task, field):
        return getattr(task, field)
    if isinstance(task, dict):
        return task.get(field)
    return None


# ── Task Dict Factory ─────────────────────────────────────────────────────────

def _make_task_dict(
    title: str,
    description: str = "",
    raw_time: str | None = None,
    raw_input: str = "",
    category: str = "biasa",
    task_id: str | None = None,
    deadline_confirmed: bool = False,
    description_filled: bool = False,
) -> dict:
    """
    Satu-satunya tempat schema task dict dibuat.
    Dipakai oleh _parse_discovery, _init_meta, dan _to_tasks.
    """
    return {
        "task_id":            task_id or str(uuid4()),
        "title":              title,
        "description":        description,
        "raw_time":           raw_time,
        "raw_input":          raw_input,
        "category":           category,
        "deadline_confirmed": deadline_confirmed,
        "description_filled": description_filled,
    }


# ── HITL State Builder ────────────────────────────────────────────────────────

def _make_hitl_state(
    phase: str,
    meta: list[dict],
    current_task_index: int = 0,
    review_count: int = 0,
    additional_context: str = "",
) -> dict:
    """
    Satu-satunya tempat hitl_state dict dibentuk.
    Menghilangkan literal dict yang berulang di setiap _chat_return call.
    """
    return {
        "phase":              phase,
        "current_task_index": current_task_index,
        "tasks_with_meta":    meta,
        "review_count":       review_count,
        "additional_context": additional_context,
    }


# ── LLM Invoke Helper ─────────────────────────────────────────────────────────

def _llm_invoke(llm, system: str, user: str):
    """
    Wrapper invoke [system, user] yang diulang di 5+ tempat.
    Mengembalikan objek hasil llm.invoke langsung.
    """
    return llm.invoke([
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ])


# ── Factory ───────────────────────────────────────────────────────────────────

def make_counselor(llm, _interrupt=None, calendar_client=None):
    interrupt_fn  = _interrupt if _interrupt is not None else _langgraph_interrupt
    discovery_llm = llm.with_structured_output(DiscoveryOutput)
    detail_llm    = llm.with_structured_output(TaskDetailParsed)
    enrich_llm    = llm.with_structured_output(ReviewEnrichOutput)  # Fix #2: buat sekali, bukan per-call

    def run(state: AppState) -> dict:
        raw_tasks  = get_raw_tasks(state)
        prev_hitl  = get_hitl_input(state) or {}
        user_msg   = last_message(state)
        # Fix #7: hitung loop hanya dari pesan non-kosong agar transisi antar fase
        # yang return msg="" tidak menghabiskan kuota MAX_LOOPS secara diam-diam.
        loop_count = sum(1 for m in (state.get("counselor_response") or []) if m)

        _log("=== RUN ===", f"loop={loop_count} phase={prev_hitl.get('phase','init')}")

        if loop_count >= MAX_LOOPS:
            return _force_done(raw_tasks)

        phase = prev_hitl.get("phase", "init")

        if phase == "init":
            return _phase_init(raw_tasks, user_msg, prev_hitl,
                               discovery_llm, detail_llm,
                               interrupt_fn)
        elif phase == "detail":
            return _phase_detail(raw_tasks, user_msg, prev_hitl,
                                 detail_llm, interrupt_fn)  # Fix #8: hapus llm yg tidak dipakai
        elif phase == "review":
            return _phase_review(raw_tasks, user_msg, prev_hitl,
                                 llm, enrich_llm, interrupt_fn)
        else:
            return _force_done(raw_tasks)

    return run


# ── Phase: Init ───────────────────────────────────────────────────────────────

def _phase_init(raw_tasks, user_msg, prev_hitl,
                discovery_llm, detail_llm,
                interrupt_fn):
    """
    Loop pertama. Satu interrupt saja.
    Kalau vague: tanya discovery.
    Kalau spesifik: tanya detail task[0].
    """
    _log("PHASE init")

    if _is_vague(raw_tasks):
        msg    = _discovery_msg(user_msg)
        _log("INTERRUPT discovery", msg)
        result = interrupt_fn({"type": "counselor_chat", "message": msg, "phase": "chat"}) or {}

        answer = (result.get("additional_context") or "").strip()
        _log("DISCOVERY ANSWER", answer)

        if not answer:
            return _chat_return(msg, raw_tasks, _make_hitl_state(
                phase="init", meta=[], current_task_index=0, review_count=0,
            ))

        new_tasks = _parse_discovery(discovery_llm, answer)
        _log("PARSED TASKS", new_tasks)

        if not new_tasks:
            retry = (
                "Hmm, aku belum bisa tangkap tugas-tugasnya. "
                "Bisa sebutin lebih jelas? "
                "Contoh: 'ada tugas RPL bikin aplikasi, sama laprak kimia deadline Jumat'"
            )
            # Fix #1: return value interrupt sengaja tidak ditangkap di sini karena
            # jawaban user dari retry akan tiba via run() berikutnya (bukan via nilai
            # kembalian interrupt ini). hitl_state phase="init" memastikan run()
            # berikutnya memproses jawaban dari awal, bukan dari state yang stale.
            interrupt_fn({"type": "counselor_chat", "message": retry, "phase": "chat"})
            return _chat_return(retry, raw_tasks, _make_hitl_state(
                phase="init", meta=[], current_task_index=0, review_count=0,
            ))

        meta = _init_meta(new_tasks)
        return _chat_return("", _to_tasks(meta), _make_hitl_state(
            phase="detail", meta=meta, current_task_index=0, review_count=0,
        ))

    else:
        meta = _init_meta(raw_tasks)
        idx  = _next_incomplete(meta, -1)

        if idx is None:
            return _chat_return("", _to_tasks(meta), _make_hitl_state(
                phase="review", meta=meta, current_task_index=0, review_count=0,
            ))

        msg    = _detail_q(meta[idx], is_first=True, user_msg=user_msg)
        _log("INTERRUPT detail[0]", msg)
        result = interrupt_fn({"type": "counselor_chat", "message": msg, "phase": "chat"}) or {}

        answer = (result.get("additional_context") or "").strip()
        meta   = _apply_answer(detail_llm, meta, idx, answer)
        nxt    = _next_incomplete(meta, idx)

        if nxt is None:
            return _chat_return(msg, _to_tasks(meta), _make_hitl_state(
                phase="review", meta=meta, current_task_index=0, review_count=0,
            ))

        return _chat_return(msg, _to_tasks(meta), _make_hitl_state(
            phase="detail", meta=meta, current_task_index=nxt, review_count=0,
        ))


# ── Phase: Detail ─────────────────────────────────────────────────────────────

def _phase_detail(raw_tasks, user_msg, prev_hitl,
                  detail_llm, interrupt_fn):
    """
    Tanya satu task per loop. Satu interrupt per run.
    """
    _log("PHASE detail")

    meta         = prev_hitl.get("tasks_with_meta") or _init_meta(raw_tasks)
    current_idx  = prev_hitl.get("current_task_index", 0)
    review_count = prev_hitl.get("review_count", 0)

    if current_idx >= len(meta):
        return _chat_return("", _to_tasks(meta), _make_hitl_state(
            phase="review", meta=meta, current_task_index=0, review_count=review_count,
        ))

    msg    = _detail_q(meta[current_idx], is_first=False, user_msg=user_msg)
    _log(f"INTERRUPT detail[{current_idx}]", msg)
    result = interrupt_fn({"type": "counselor_chat", "message": msg, "phase": "chat"}) or {}

    answer = (result.get("additional_context") or "").strip()
    _log("DETAIL ANSWER", answer)

    meta = _apply_answer(detail_llm, meta, current_idx, answer)
    _log("META after apply", meta)

    nxt = _next_incomplete(meta, current_idx)
    _log("NEXT IDX", nxt)

    if nxt is None:
        _log("ALL COMPLETE -> switching to review phase")
        return _chat_return("", _to_tasks(meta), _make_hitl_state(
            phase="review", meta=meta, current_task_index=0, review_count=review_count,
        ))

    return _chat_return(msg, _to_tasks(meta), _make_hitl_state(
        phase="detail", meta=meta, current_task_index=nxt, review_count=review_count,
    ))


# ── Phase: Review ─────────────────────────────────────────────────────────────

def _phase_review(raw_tasks, user_msg, prev_hitl,
                  llm, enrich_llm, interrupt_fn):
    """
    Generate review, interrupt, tunggu approve atau cerita tambahan.
    """
    _log("PHASE review")

    meta         = prev_hitl.get("tasks_with_meta") or _init_meta(raw_tasks)
    review_count = prev_hitl.get("review_count", 0)
    extra        = (prev_hitl.get("additional_context") or "").strip()
    tasks        = _to_tasks(meta)

    feedback_msg = ""
    if extra:
        feedback_msg = _gen_feedback(llm, extra, tasks)
        _log("FEEDBACK MSG", feedback_msg)

        try:
            # Fix #2: enrich_llm diterima sebagai parameter (dibuat sekali di make_counselor)
            task_context = "\n".join(
                f"- task_id={t['task_id']} | {t['title']}: {t.get('description') or '(kosong)'}"
                for t in meta
            )
            res      = _llm_invoke(enrich_llm, REVIEW_ENRICH_SYSTEM,
                                   f"Cerita: {extra}\n\nTask:\n{task_context}")
            task_map = {t["task_id"]: dict(t) for t in meta}
            for u in res.updates:
                if u.task_id in task_map:
                    if u.updated_description:
                        task_map[u.task_id]["description"] = u.updated_description
                    if u.updated_raw_time:
                        task_map[u.task_id]["raw_time"] = u.updated_raw_time
            meta  = list(task_map.values())
            tasks = _to_tasks(meta)
            _log("ENRICHED TASKS", meta)
        except Exception as e:
            _log("ENRICH ERROR", e)

    return _do_review(tasks, meta, user_msg, llm, interrupt_fn, review_count,
                      feedback_msg=feedback_msg)


def _do_review(tasks, meta, user_msg, llm, interrupt_fn, review_count,
               feedback_msg: str = ""):
    """
    Generate review + offer, interrupt, tunggu approve atau cerita tambahan.

    feedback_msg: kalimat feedback dari cerita sebelumnya (ditampilkan sebelum review baru).
                  Kosong di review pertama.
    """
    if review_count >= MAX_REVIEW:
        return _force_done(tasks)

    review_body, offer_msg = _gen_review(llm, tasks, user_msg)
    _log("REVIEW BODY", review_body)
    _log("OFFER MSG", offer_msg)

    full_review = (
        f"{feedback_msg}\n\n{review_body}\n\n{offer_msg}" if feedback_msg
        else f"{review_body}\n\n{offer_msg}"
    )
    _log("FULL REVIEW MSG", full_review)

    task_summary = [
        {"task_id": t.get("task_id",""), "title": t.get("title",""),
         "description": t.get("description",""), "raw_time": t.get("raw_time")}
        for t in tasks
    ]

    result = interrupt_fn({
        "type": "counselor_review",
        "message": full_review,
        "phase": "review",
        "task_summary": task_summary,
    }) or {}

    _log("REVIEW RESULT", result)

    approved = bool(result.get("approved"))
    extra    = (result.get("additional_context") or "").strip()

    if approved:
        bridge   = f"Siap! Sekarang kita atur jadwal buat {len(tasks)} tugas ini ya biar semua kelar tepat waktu."
        full_msg = f"{full_review}\n\n{bridge}"
        return {
            **ai_msg(full_msg),
            "raw_tasks":          tasks,
            "counselor_response": [full_msg],
            "counselor_done":     True,
            "hitl_status":        "approved",
            "hitl_input":         None,
        }

    return _chat_return(full_review, tasks, _make_hitl_state(
        phase="review", meta=meta, current_task_index=0,
        review_count=review_count + 1, additional_context=extra,
    ))


# ── Task Parsing ──────────────────────────────────────────────────────────────

def _parse_discovery(discovery_llm, user_answer: str) -> list[dict]:
    try:
        result = _llm_invoke(
            discovery_llm,
            DISCOVERY_SYSTEM,
            f"User menyebutkan: {user_answer}",
        )
        return [
            _make_task_dict(
                title=t.title,
                raw_time=t.raw_time,
                raw_input=t.raw_input or user_answer,
                category=t.category,
            )
            for t in result.tasks
        ]
    except Exception as e:
        _log("PARSE DISCOVERY ERROR", e)
        return []


def _apply_answer(detail_llm: TaskDetailParsed, meta: list, idx: int, answer: str) -> list:
    """
    Parse jawaban user untuk task[idx] dan update meta.
    Deterministik: kalau LLM gagal, simpan jawaban mentah.
    Selalu set deadline_confirmed=True setelah dipanggil.

    PENTING: detail_llm harus llm.with_structured_output(TaskDetailParsed),
             bukan llm mentah — structured output dibutuhkan untuk parsing field.
    """
    if idx >= len(meta):
        return meta

    result = [dict(t) for t in meta]
    target = result[idx]

    if not answer:
        target["deadline_confirmed"] = True
        target["description_filled"] = True
        result[idx] = target
        return result

    try:
        parsed = _llm_invoke(
            detail_llm,
            DETAIL_PARSE_SYSTEM,
            (
                f"Task: {target.get('title','task ini')}\n"
                f"Jawaban user: {answer}\n\n"
                f"Ekstrak deskripsi + deadline."
            ),
        )

        old_desc = target.get("description") or ""
        if parsed.parsed_description and parsed.parsed_description.strip():
            new_desc = parsed.parsed_description.strip()
            target["description"] = f"{old_desc}. {new_desc}".strip(". ") if old_desc else new_desc
        elif answer:
            target["description"] = answer if not old_desc else f"{old_desc}. {answer}"

        if parsed.parsed_raw_time and parsed.parsed_raw_time.strip():
            target["raw_time"] = parsed.parsed_raw_time.strip()

    except Exception as e:
        _log("APPLY ANSWER ERROR", e)
        old_desc = target.get("description") or ""
        target["description"] = f"{old_desc}. {answer}".strip(". ") if old_desc else answer

    target["deadline_confirmed"] = True
    target["description_filled"] = True
    result[idx] = target
    return result


# ── Review Generation ─────────────────────────────────────────────────────────

def _gen_review(llm, tasks: list, user_msg: str) -> tuple[str, str]:
    """
    Returns (review_body, offer_message).
    review_body: ringkasan task
    offer_message: tawaran curhat yang spesifik dan kontekstual
    """
    try:
        task_lines = [
            f"- {t.get('title','Task')}: {t.get('description') or '(belum ada deskripsi)'}, "
            f"deadline: {t.get('raw_time') or 'belum ada deadline'}"
            for t in tasks
        ]
        result = _llm_invoke(
            llm,
            REVIEW_SYSTEM,
            f"Pesan awal user: {user_msg}\n\nTask:\n" + "\n".join(task_lines),
        )
        raw = str(result.content) if hasattr(result, "content") else str(result)

        if "|||" in raw:
            parts = raw.split("|||", 1)
            return parts[0].strip(), parts[1].strip()

        return raw.strip(), _fallback_offer(tasks)

    except Exception as e:
        _log("REVIEW GEN ERROR", e)
        return _fallback_review(tasks), _fallback_offer(tasks)


def _gen_feedback(llm, extra: str, tasks: list) -> str:
    """
    Generate feedback hangat dari cerita tambahan user.
    Dipanggil sebelum review terbaru ditampilkan.
    """
    try:
        task_context = ", ".join(t.get("title","task") for t in tasks)
        result = _llm_invoke(
            llm,
            FEEDBACK_SYSTEM,
            f"Task user: {task_context}\nCerita tambahan user: {extra}",
        )
        return str(result.content).strip() if hasattr(result, "content") else str(result).strip()
    except Exception as e:
        _log("FEEDBACK GEN ERROR", e)
        return "Makasih udah cerita lebih!"


def _fallback_offer(tasks: list) -> str:
    """Fallback tawaran curhat kalau LLM gagal — sebut semua task."""
    if not tasks:
        return "Ada yang mau ditambahin atau diubah?"
    titles = [t.get("title", "tugas ini") for t in tasks]
    if len(titles) == 1:
        task_str = titles[0]
    elif len(titles) == 2:
        task_str = f"{titles[0]} dan {titles[1]}"
    else:
        task_str = ", ".join(titles[:-1]) + f", dan {titles[-1]}"
    return (
        f"Kalau lo mau ceritain lebih — misalnya soal {task_str}, "
        f"perasaan lo terhadap salah satunya, atau langkah yang udah ada di pikiran — boleh banget. "
        f"Tapi kalau udah oke semua, kita gas aja langsung!"
    )


def _fallback_review(tasks: list) -> str:
    lines = [
        f"\u2022 {t.get('title','Task')}: {t.get('description') or 'belum ada detail'}, "
        f"deadline {t.get('raw_time') or 'belum ada'}"
        for t in tasks
    ]
    return (
        "Oke, ini yang aku tangkap dari tugasmu:\n"
        + "\n".join(lines)
        + "\n\nKalau ada detail lain yang mau ditambahin — perasaanmu, langkah-langkah, "
        "atau apapun — boleh ceritain. Atau kalau udah oke, langsung approve aja!"
    )


# ── Meta Helpers ──────────────────────────────────────────────────────────────

def _is_vague(raw_tasks: list) -> bool:
    if not raw_tasks:
        return True
    vague_kw = [
        "belum jelas","tidak disebutkan","tidak diketahui","banyak tugas",
        "tugas numpuk","belum ditentukan","tidak ada detail","tidak tahu",
    ]
    if len(raw_tasks) == 1:
        t       = raw_tasks[0]
        title   = (_get(t,"title") or "").lower()
        desc    = (_get(t,"description") or "").lower()
        generic = ["banyak tugas","tugas","kerjaan","task","banyak kerjaan","pekerjaan"]
        if any(g == title for g in generic):
            return True
        if any(kw in desc for kw in vague_kw):
            return True
    # Fix #4: pakai any() bukan all() — kalau ADA SATU task yang vague,
    # discovery tetap perlu dijalankan. all() sebelumnya menyebabkan task
    # dengan deskripsi kosong lolos ke review tanpa pernah ditanya.
    return any(
        any(kw in (_get(t,"description") or "").lower() for kw in vague_kw)
        for t in raw_tasks
    )


def _init_meta(raw_tasks: list) -> list[dict]:
    result = []
    for t in raw_tasks:
        d        = _coerce(t)
        desc     = d.get("description") or ""
        vague    = ["belum jelas","tidak disebutkan","tidak diketahui"]
        has_desc = len(desc) > 15 and not any(kw in desc.lower() for kw in vague)
        result.append(_make_task_dict(
            title               = d.get("title", ""),
            description         = desc,
            raw_time            = d.get("raw_time"),
            raw_input           = d.get("raw_input", ""),
            category            = d.get("category", "biasa"),
            task_id             = d.get("task_id") or str(uuid4()),
            deadline_confirmed  = d.get("deadline_confirmed", d.get("raw_time") is not None),
            description_filled  = d.get("description_filled", has_desc),
        ))
    return result


def _next_incomplete(meta: list, after: int) -> int | None:
    """
    Cari index task pertama yang belum lengkap setelah posisi `after`.
    Gunakan after=-1 untuk scan dari awal (semua task dicek).

    Fix #5: fungsi ini selalu dipanggil dengan after=idx (bukan after=-1)
    setelah apply_answer, sehingga hanya task SETELAH idx yang dicek.
    Task sebelum idx dijamin sudah lengkap karena diproses secara sequential.
    """
    for i, t in enumerate(meta):
        if i <= after:
            continue
        if not t.get("description_filled") or not t.get("deadline_confirmed"):
            return i
    return None


def _to_tasks(meta: list) -> list[dict]:
    """
    Proyeksi meta ke task dict publik (tanpa field internal deadline_confirmed
    dan description_filled).

    Fix #6: JANGAN pakai hasil _to_tasks() sebagai pengganti meta di hitl_state.
    tasks_with_meta di hitl_state harus selalu berisi meta lengkap (dengan field
    internal), karena _init_meta() yang menerima tasks tanpa field ini akan
    menganggap semua task belum lengkap dan memicu ulang fase detail.
    """
    return [
        _make_task_dict(
            title       = t.get("title", ""),
            description = t.get("description", ""),
            raw_time    = t.get("raw_time"),
            raw_input   = t.get("raw_input", ""),
            category    = t.get("category", "biasa"),
            task_id     = t.get("task_id") or str(uuid4()),
        )
        for t in meta
    ]


# ── Message Builders ──────────────────────────────────────────────────────────

def _discovery_msg(user_msg: str) -> str:
    has_stress = _stress(user_msg)
    if has_stress:
        opening = (
            "Oke, tenang dulu — wajar banget kok ngerasa kayak gitu kalau semuanya dateng barengan. "
            "Kita urai pelan-pelan bareng-bareng ya, biar kepala lo ga makin mumet."
        )
    else:
        opening = (
            "Oke, aku bantu atur semuanya ya. "
            "Kita lihat dulu apa aja yang lagi ada."
        )
    ask = (
        "Coba ceritain dulu — ada kegiatan atau kewajiban apa aja yang lagi numpuk? "
        "(contoh: 'tugas basdat, meeting sama klien, olahraga rutin, laprak kimia')"
    )
    return f"{opening} {ask}"


def _detail_q(task_meta: dict, is_first: bool, user_msg: str) -> str:
    title     = task_meta.get("title", "yang ini")
    is_stress = _stress(user_msg)

    if is_first:
        warmup = (
            "Oke, kita bedah satu-satu pelan-pelan ya — "
            "biar semuanya keliatan lebih manageable dan ga bikin kepala penuh. "
        ) if is_stress else "Oke, kita mulai dari yang pertama ya. "
        prefix = f"{warmup}Sekarang ceritain dulu soal **{title}**:"
    else:
        prefix = f"Oke noted! Sekarang **{title}**:"

    return (
        f"{prefix} "
        f"kira-kira ini ngerjain apa dan ada target selesainya kapan? "
        f"(contoh: 'bikin laporan analisis, target Jumat' atau "
        f"'bikin ERD database, belum ada deadline tapi masih perlu belajar konsepnya dulu')"
    )


def _stress(msg: str) -> bool:
    signals = [
        "pusing","stress","stres","capek","cape","overwhelmed","ga tau","gak tau",
        "bingung","panik","lelah","penat","mumet","galau","ga sanggup","gak sanggup",
        "burnout","anjay","anjir","gila","ga kuat","susah","berat",
    ]
    lower = msg.lower()
    return any(s in lower for s in signals)


# ── Return Helpers ────────────────────────────────────────────────────────────

def _chat_return(msg: str, raw_tasks: list, hitl_state: dict) -> dict:
    return {
        **ai_msg(msg),
        "raw_tasks":           raw_tasks,
        "counselor_response":  [msg] if msg else [],
        "counselor_done":      False,
        "hitl_status":         "rejected",
        "hitl_input":          hitl_state,
    }


def _force_done(raw_tasks: list) -> dict:
    titles   = [_get(t,"title") or "task" for t in raw_tasks]
    task_str = " dan ".join(titles) if len(titles) <= 2 else ", ".join(titles[:-1]) + f", dan {titles[-1]}"
    msg      = f"Oke, aku udah catat semuanya. Yuk kita langsung atur jadwal buat {task_str}!"
    return {
        **ai_msg(msg),
        "raw_tasks":           raw_tasks,
        "counselor_response":  [msg],
        "counselor_done":      True,
        "hitl_status":         "approved",
        "hitl_input":          None,
    }


# ── Calendar Context (opsional — hanya untuk konteks prompt) ─────────────────

def _fetch_schedule_context(calendar_client, state: AppState) -> str:
    """Ambil jadwal existing dari calendar untuk konteks LLM. Return string kosong jika gagal."""
    if calendar_client is None:
        return ""

    metadata = get_metadata(state) or {}
    token    = _extract_auth_token(metadata)

    try:
        schedules = calendar_client.list_schedules(token=token)
    except Exception as err:
        _log("CALENDAR CONTEXT ERROR", err)
        return ""

    return _format_schedule_context(schedules) if schedules else "(tidak ada jadwal)"


def _format_schedule_context(schedules: list[dict]) -> str:
    """Format daftar jadwal jadi string ringkas untuk konteks prompt."""
    lines: list[str] = []
    for item in schedules[:5]:
        title      = str(item.get("title") or "(tanpa judul)")
        start_time = item.get("startTime") or item.get("start_time")
        deadline   = item.get("deadline") or item.get("endTime")
        status     = item.get("status") or "pending"
        time_bits  = []
        if start_time:
            time_bits.append(f"mulai: {start_time}")
        if deadline:
            time_bits.append(f"selesai: {deadline}")
        time_part = f" ({', '.join(time_bits)})" if time_bits else ""
        lines.append(f"- {title} [{status}]{time_part}")
    return "".join(lines)


def _extract_auth_token(metadata: dict) -> str | None:
    """Ekstrak auth token dari metadata jika ada."""
    for key in ("auth_token", "access_token", "authorization"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None