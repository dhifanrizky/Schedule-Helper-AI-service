# ---------------------------------------------------------------------------
# Agent 3: PrioritizerAgent
# Tugas:
# 1. Menerima raw_tasks dari Router/Agent 1.
# 2. Memakai LLM untuk memecah task, estimasi durasi, deadline, dan konteks.
# 3. Menghitung prioritas dengan rumus eksplisit agar explainable.
# 4. Membuat draft proposed_schedule.
# 5. HITL aktif: user bisa approve/edit sebelum lanjut ke scheduler.
# ---------------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langgraph.types import interrupt
from pydantic import BaseModel, Field, ValidationError

from app.graph.state import AppState
from app.graph.agents.helpers import ai_msg, get_raw_tasks
from app.graph.types import RawTask, TaskBreakdown, ScheduleItem


CategoryType = Literal["serius", "santai", "biasa", "lainnya"]
PreferredWindow = Literal["pagi", "siang", "sore", "malam", "bebas"]


WINDOW_START = {
    "pagi": 8 * 60,
    "siang": 13 * 60,
    "sore": 16 * 60,
    "malam": 19 * 60,
    "bebas": 9 * 60,
}


class LLMTaskItem(BaseModel):
    task_id: str = Field(description="ID task yang sama dengan raw_tasks, contoh: task_001")
    title: str = Field(description="Judul singkat task dalam bahasa user")
    subtasks: list[str] = Field(
        default_factory=list,
        description="Pecahan langkah kerja konkret. Minimal 1 subtask.",
    )
    estimated_minutes: int = Field(
        ge=15,
        le=360,
        description="Estimasi durasi total task dalam menit.",
    )
    deadline: str | None = Field(
        default=None,
        description="Deadline dalam format ISO-8601 jika ada. Jika tidak jelas, null.",
    )
    category: CategoryType = Field(default="biasa")
    preferred_window: PreferredWindow = Field(default="bebas")

    urgency: int = Field(
        ge=1,
        le=5,
        description="Skor 1-5. 5 berarti sangat mendesak.",
    )
    importance: int = Field(
        ge=1,
        le=5,
        description="Skor 1-5. 5 berarti sangat penting.",
    )
    effort: int = Field(
        ge=1,
        le=5,
        description="Skor 1-5. 5 berarti sangat berat/sulit.",
    )
    energy_fit: int = Field(
        ge=1,
        le=5,
        description="Skor 1-5. 5 berarti cocok dikerjakan segera dengan kondisi user.",
    )


class LLMTaskBreakdownResponse(BaseModel):
    tasks: list[LLMTaskItem]


SYSTEM_PROMPT = """
Kamu adalah Agent 3: Action Translator, Prioritizer, dan Scheduler Draft Builder.

Konteks:
- Input berasal dari Agent 1/router dalam bentuk raw_tasks.
- Tugasmu bukan sekadar membuat ringkasan, tetapi mengubah input user menjadi daftar pekerjaan yang bisa dieksekusi.
- Bahasa output harus mengikuti bahasa user. Jika user memakai bahasa Indonesia santai, gunakan Indonesia santai tetapi tetap jelas.

Tugas utama:
1. Baca setiap raw_task.
2. Buat task breakdown:
   - title
   - subtasks konkret
   - estimated_minutes
   - deadline jika bisa disimpulkan
   - category
   - preferred_window
   - urgency, importance, effort, energy_fit
3. Jika detail belum jelas, tetap buat task yang masuk akal dan tulis subtask awal seperti "klarifikasi detail tugas".
4. Jangan membuat task fiktif yang tidak didukung input.
5. Jika user bilang deadline "hari ini", "besok", atau "minggu ini", gunakan itu sebagai sinyal urgency tinggi.

Panduan scoring:
- urgency:
  5 = deadline hari ini/besok/sangat mepet
  4 = minggu ini atau perlu segera
  3 = ada deadline tapi tidak sangat mepet
  2 = tidak terlalu mendesak
  1 = santai/tidak ada urgensi

- importance:
  5 = berdampak besar ke akademik/kerja/proyek utama
  4 = tugas penting yang harus selesai
  3 = tugas biasa
  2 = aktivitas pendukung
  1 = aktivitas ringan

- effort:
  5 = sangat berat/kompleks
  4 = butuh fokus tinggi
  3 = sedang
  2 = ringan
  1 = sangat ringan

- energy_fit:
  5 = cocok dikerjakan segera sebagai fokus utama
  4 = cocok dikerjakan setelah quick planning
  3 = netral
  2 = lebih cocok nanti
  1 = tidak cocok dikerjakan sekarang

Kategori wajib salah satu:
- serius
- santai
- biasa
- lainnya

Preferred window wajib salah satu:
- pagi
- siang
- sore
- malam
- bebas
"""

def apply_hitl_edits(
    hitl_result: dict,
    task_breakdown: list[TaskBreakdown],
    proposed_schedule: list[ScheduleItem],
) -> tuple[list[TaskBreakdown], list[ScheduleItem]]:
    """
    Memastikan hasil edit dari user benar-benar dipakai.

    Aturan:
    - Jika user mengirim tasks hasil edit, pakai tasks itu.
    - Jika tasks diedit tapi proposed_schedule tidak dikirim,
      bangun ulang proposed_schedule dari tasks edit.
    - Jika user mengirim proposed_schedule edit, pakai itu.
    - Jika tidak ada edit, pakai hasil awal.
    """
    edited_tasks = hitl_result.get("tasks")
    edited_schedule = hitl_result.get("proposed_schedule")

    final_tasks = edited_tasks or task_breakdown

    if edited_tasks and not edited_schedule:
        final_schedule = build_proposed_schedule(final_tasks)
    else:
        final_schedule = edited_schedule or proposed_schedule

    return final_tasks, final_schedule

def make_prioritizer(llm: BaseChatModel):
    structured_llm = llm.with_structured_output(LLMTaskBreakdownResponse)

    def run(state: AppState) -> dict:
        previous_status = state.get("hitl_status")
        existing_tasks = state.get("task_breakdown") or []
        existing_schedule = state.get("proposed_schedule") or []

        # Kalau sebelumnya user reject/edit, jangan mulai ulang dari raw_tasks.
        # Pakai hasil task_breakdown dan proposed_schedule terakhir.
        if previous_status == "rejected" and existing_tasks:
            task_breakdown = existing_tasks
            proposed_schedule = existing_schedule or build_proposed_schedule(task_breakdown)

        else:
            raw_tasks = get_raw_tasks(state)

            if not raw_tasks:
                return {
                    **ai_msg("Aku belum menemukan tugas yang bisa diprioritaskan."),
                    "task_breakdown": [],
                    "proposed_schedule": [],
                    "error_message": "raw_tasks kosong.",
                }

            try:
                task_breakdown = build_task_breakdown_with_llm(raw_tasks, structured_llm)
                print("[Agent 3] LLM prioritizer berhasil dipakai.")
            except Exception as err:
                print(f"[Agent 3] LLM prioritizer gagal, fallback dipakai: {type(err).__name__}: {err}")
                task_breakdown = build_task_breakdown_rule_based(raw_tasks)

            proposed_schedule = build_proposed_schedule(task_breakdown)

        hitl_result = interrupt({
            "type": "task_review",
            "message": "Cek dulu daftar tugas dan draft jadwal ini. Kamu bisa approve, edit, tambah, atau hapus sebelum dijadwalkan.",
            "tasks": task_breakdown,
            "proposed_schedule": proposed_schedule,
        }) or {}

        approved = bool(hitl_result.get("approved"))

        final_tasks, final_schedule = apply_hitl_edits(
            hitl_result=hitl_result,
            task_breakdown=task_breakdown,
            proposed_schedule=proposed_schedule,
        )

        if not approved:
            return {
                **ai_msg("Baik, jadwal belum disetujui. Silakan edit dulu daftar tugasnya."),
                "task_breakdown": final_tasks,
                "proposed_schedule": final_schedule,
                "error_message": None,
                "hitl_status": "rejected",
                "hitl_input": hitl_result,
            }

        return {
            **ai_msg(f"Siap, {len(final_tasks)} tugas sudah disetujui dan akan lanjut ke penjadwalan."),
            "task_breakdown": final_tasks,
            "proposed_schedule": final_schedule,
            "error_message": None,
            "hitl_status": "approved",
            "hitl_input": hitl_result,
        }

    return run


def build_task_breakdown_with_llm(raw_tasks: list[RawTask], structured_llm) -> list[TaskBreakdown]:
    normalized_raw_tasks = [_raw_task_to_dict(task, idx) for idx, task in enumerate(raw_tasks, start=1)]

    today = datetime.now().strftime("%Y-%m-%d")

    result = structured_llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Tanggal hari ini: {today}\n\n"
                "Ubah raw_tasks berikut menjadi task breakdown terstruktur:\n"
                f"{normalized_raw_tasks}"
            ),
        },
    ])

    if hasattr(result, "model_dump"):
        result = result.model_dump()

    if not isinstance(result, dict):
        raise ValueError("Output LLM bukan dict.")

    tasks = result.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("Output LLM tidak memiliki tasks.")

    breakdown: list[TaskBreakdown] = []

    for idx, item in enumerate(tasks, start=1):
        try:
            parsed = LLMTaskItem.model_validate(item)
        except ValidationError as err:
            raise ValueError(f"Format task dari LLM tidak valid: {err}") from err

        priority = calculate_priority(
            urgency=parsed.urgency,
            importance=parsed.importance,
            effort=parsed.effort,
            energy_fit=parsed.energy_fit,
        )

        subtasks = [s.strip() for s in parsed.subtasks if str(s).strip()]
        if not subtasks:
            subtasks = [parsed.title]

        breakdown.append({
            "task_id": parsed.task_id or f"task_{idx:03d}",
            "title": parsed.title,
            "subtasks": subtasks,
            "estimated_minutes": int(parsed.estimated_minutes),
            "deadline": parsed.deadline,
            "priority": priority,
            "category": parsed.category,
            "preferred_window": parsed.preferred_window,
        })

    breakdown.sort(
        key=lambda x: (
            x["priority"],
            _deadline_sort_value(x.get("deadline")),
            -int(x["estimated_minutes"]),
            x["task_id"],
        )
    )

    return breakdown


def calculate_priority(urgency: int, importance: int, effort: int, energy_fit: int) -> int:
    """
    Rumus prioritas explainable.

    priority_score =
    0.45 * urgency
    + 0.30 * importance
    + 0.15 * (6 - effort)
    + 0.10 * energy_fit

    Keterangan:
    - urgency paling besar karena sistem membantu user saat deadline/overload.
    - importance menjaga tugas penting tetap naik.
    - effort dibalik dengan (6 - effort), supaya quick win bisa naik.
    - energy_fit membantu menyesuaikan dengan kesiapan user.
    """
    score = (
        0.45 * urgency
        + 0.30 * importance
        + 0.15 * (6 - effort)
        + 0.10 * energy_fit
    )

    if score >= 4.0:
        return 1
    if score >= 2.7:
        return 2
    return 3


def _raw_task_to_dict(task: Any, idx: int) -> dict:
    if hasattr(task, "model_dump"):
        data = task.model_dump()
    elif isinstance(task, dict):
        data = dict(task)
    else:
        data = {}

    return {
        "task_id": data.get("task_id") or f"task_{idx:03d}",
        "title": data.get("title") or "",
        "description": data.get("description") or "",
        "raw_time": data.get("raw_time"),
        "raw_input": data.get("raw_input") or data.get("title") or "",
        "category": data.get("category") or "biasa",
    }


def source_text(task: Any, idx: int = 1) -> str:
    data = _raw_task_to_dict(task, idx)
    return (
        data.get("raw_input")
        or data.get("description")
        or data.get("title")
        or ""
    ).strip()


def normalize_text(text: str) -> str:
    return " ".join(str(text).strip().split())


def detect_preferred_window(task: str) -> PreferredWindow:
    text = task.lower()

    if "pagi" in text:
        return "pagi"
    if "siang" in text:
        return "siang"
    if "sore" in text:
        return "sore"
    if "malam" in text:
        return "malam"

    return "bebas"


def detect_category(task: str) -> CategoryType:
    text = task.lower()

    if any(k in text for k in ["kuliah", "kelas", "materi", "belajar", "project", "proyek", "laporan", "proposal", "ujian"]):
        return "serius"

    if any(k in text for k in ["istirahat", "break", "main game", "main", "rebahan"]):
        return "santai"

    if any(k in text for k in ["meeting", "organisasi", "rapat"]):
        return "lainnya"

    return "biasa"


def estimate_duration(task: str) -> int:
    text = task.lower()

    if any(k in text for k in ["laporan", "proposal", "skripsi", "makalah"]):
        return 120
    if any(k in text for k in ["project", "proyek", "capstone"]):
        return 120
    if any(k in text for k in ["demo", "presentasi"]):
        return 90
    if any(k in text for k in ["ui", "dashboard", "fitur", "integrasi"]):
        return 120
    if any(k in text for k in ["bug", "error", "fix", "hotfix"]):
        return 60
    if any(k in text for k in ["meeting", "rapat"]):
        return 60
    if any(k in text for k in ["dokumentasi", "langgraph", "belajar", "ngulik"]):
        return 60

    return 60


def estimate_priority(task: str) -> int:
    text = task.lower()
    score = 0

    if any(k in text for k in ["deadline", "besok", "hari ini", "urgent", "segera", "mepet"]):
        score += 4
    if "minggu ini" in text:
        score += 3
    if any(k in text for k in ["demo", "presentasi", "ujian"]):
        score += 4
    if any(k in text for k in ["bug", "error", "fix", "hotfix"]):
        score += 3
    if any(k in text for k in ["laporan", "proposal", "revisi", "project", "proyek"]):
        score += 3
    if any(k in text for k in ["meeting", "rapat"]):
        score += 2
    if any(k in text for k in ["ngulik", "belajar", "dokumentasi", "langgraph"]):
        score += 1
    if "minor" in text:
        score -= 1

    if score >= 6:
        return 1
    if score >= 3:
        return 2
    return 3


def extract_deadline(task: str) -> str | None:
    text = task.lower()
    now = datetime.now()

    if "hari ini" in text:
        return now.replace(hour=23, minute=59, second=0, microsecond=0).isoformat()

    if "besok" in text:
        due = now + timedelta(days=1)
        return due.replace(hour=23, minute=59, second=0, microsecond=0).isoformat()

    if "minggu ini" in text:
        due = now + timedelta(days=7)
        return due.replace(hour=23, minute=59, second=0, microsecond=0).isoformat()

    return None


def build_task_breakdown_rule_based(raw_tasks: list[RawTask]) -> list[TaskBreakdown]:
    breakdown: list[TaskBreakdown] = []

    for idx, raw in enumerate(raw_tasks, start=1):
        data = _raw_task_to_dict(raw, idx)
        cleaned = normalize_text(source_text(raw, idx))
        task_id = data.get("task_id") or f"task_{idx:03d}"
        title = data.get("title") or cleaned or f"Tugas {idx}"

        if not cleaned:
            cleaned = title

        breakdown.append({
            "task_id": task_id,
            "title": title,
            "subtasks": build_basic_subtasks(cleaned),
            "estimated_minutes": estimate_duration(cleaned),
            "deadline": extract_deadline(cleaned),
            "priority": estimate_priority(cleaned),
            "category": detect_category(cleaned),
            "preferred_window": detect_preferred_window(cleaned),
        })

    breakdown.sort(
        key=lambda x: (
            x["priority"],
            _deadline_sort_value(x.get("deadline")),
            -int(x["estimated_minutes"]),
            x["task_id"],
        )
    )

    return breakdown


def build_basic_subtasks(task_text: str) -> list[str]:
    text = task_text.strip()
    lower_text = text.lower()

    if any(k in lower_text for k in ["meeting", "rapat", "ketemu", "janji", "kelas", "kuliah"]):
        return [
            text
        ]

    if any(k in lower_text for k in ["belum jelas", "ga jelas", "tidak jelas", "bingung"]):
        return [
            "Klarifikasi detail tugas yang belum jelas",
            "Tentukan bagian yang paling mendesak",
            "Kerjakan bagian pertama yang paling mudah dimulai",
        ]

    return [
        f"Mulai kerjakan: {text}",
        "Lanjutkan bagian utama yang paling penting",
        "Cek hasil dan rapikan sebelum selesai",
    ]


def _deadline_sort_value(deadline: str | None) -> str:
    return deadline or "9999-12-31T23:59:59"


def minutes_to_iso(total_minutes: int, base_date: str) -> str:
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{base_date}T{hour:02d}:{minute:02d}:00"


def build_proposed_schedule(task_breakdown: list[TaskBreakdown]) -> list[ScheduleItem]:
    proposed_schedule: list[ScheduleItem] = []

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = 9 * 60

    for item in task_breakdown:
        preferred_window = item.get("preferred_window", "bebas")
        preferred_start = WINDOW_START.get(preferred_window, 9 * 60)

        deadline = item.get("deadline")
        deadline_dt = None

        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline)
            except ValueError:
                deadline_dt = None

        if deadline_dt:
            base_date = deadline_dt.strftime("%Y-%m-%d")
            deadline_minutes = deadline_dt.hour * 60 + deadline_dt.minute

            # Jika tanggal berubah, reset jam kerja ke awal window.
            if base_date != current_date:
                current_date = base_date
                current_time = preferred_start

            # Deadline jam 23:59 berarti hanya batas akhir hari,
            # bukan berarti task harus dimulai jam 23:59.
            is_end_of_day_deadline = deadline_dt.hour == 23 and deadline_dt.minute >= 55

            if is_end_of_day_deadline:
                start_time_minutes = max(current_time, preferred_start)
            else:
                # Untuk event fixed-time seperti meeting jam 09:00,
                # gunakan jam deadline sebagai start time.
                start_time_minutes = max(current_time, deadline_minutes, preferred_start)
        else:
            base_date = current_date
            start_time_minutes = max(current_time, preferred_start)

        main_task = item["title"]

        proposed_schedule.append({
            "task_id": item["task_id"],
            "task": main_task,
            "priority": int(item["priority"]),
            "start_time": minutes_to_iso(start_time_minutes, base_date),
            "duration_minutes": int(item["estimated_minutes"]),
            "category": item["category"],
        })

        current_time = start_time_minutes + int(item["estimated_minutes"]) + 10

    return proposed_schedule