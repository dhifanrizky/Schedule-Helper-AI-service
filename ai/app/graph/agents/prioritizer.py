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
from app.graph.agents.helpers import ai_msg, get_raw_tasks, get_metadata
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
    task_id: str = Field(
        description="ID task yang sama dengan raw_tasks, contoh: task_001"
    )
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
- PENTING: Field 'description' pada raw_tasks memuat 2 hal krusial dari obrolan user: (1) perasaan/tingkat urgensi user, dan (2) detail yang belum jelas. PERHATIKAN INI BAIK-BAIK.
- Tugasmu bukan sekadar membuat ringkasan, tetapi mengubah input user menjadi daftar pekerjaan yang bisa dieksekusi.
- Bahasa output harus mengikuti bahasa user. Jika user memakai bahasa Indonesia santai, gunakan Indonesia santai tetapi tetap jelas.

Tugas utama:
1. Baca setiap raw_task. Jadikan catatan perasaan user (stress/overload) di field 'description' sebagai pertimbangan utama untuk menentukan skor 'energy_fit' dan 'effort'.
2. Buat task breakdown:
   - title
   - subtasks konkret (jika 'description' menyebutkan ada detail ambigu, jadikan subtask awal "Klarifikasi detail: ...")
   - estimated_minutes (Beri waktu ekstra jika user terdeteksi sedang stress/lelah di 'description')
   - deadline jika bisa disimpulkan
   - category
   - preferred_window
   - urgency, importance, effort, energy_fit
3. Jangan membuat task fiktif yang tidak didukung input.
4. Jika user bilang deadline "hari ini", "besok", atau "minggu ini", gunakan itu sebagai sinyal urgency tinggi.

Panduan scoring:
- urgency: 5 = deadline hari ini/besok/sangat mepet, 1 = santai/tidak ada urgensi
- importance: 5 = berdampak besar, 1 = aktivitas ringan
- effort: 5 = sangat berat/kompleks, 1 = sangat ringan
- energy_fit: 5 = cocok dikerjakan segera, 1 = tidak cocok dikerjakan sekarang (misal: user sedang burnout/stress di description)
"""


def build_review_reasoning_message(
    task_breakdown: list[TaskBreakdown],
    proposed_schedule: list[ScheduleItem],
) -> str:
    if not proposed_schedule:
        return (
            "Cek dulu daftar tugas dan draft jadwal ini. "
            "Jadwal belum terbentuk karena proposed_schedule masih kosong. "
            "Kamu bisa approve, edit, tambah, atau hapus sebelum dijadwalkan."
        )

    task_map = {
        str(task.get("task_id")): task
        for task in task_breakdown
        if isinstance(task, dict)
    }

    reason_lines: list[str] = []

    for idx, schedule in enumerate(proposed_schedule, start=1):
        task_id = str(schedule.get("task_id"))
        task_detail = task_map.get(task_id, {})

        task_title = schedule.get("task") or task_detail.get("title") or f"Tugas {idx}"
        start_time_raw = schedule.get("start_time")
        start_time = _format_schedule_time(start_time_raw)

        duration = (
            schedule.get("duration_minutes")
            or task_detail.get("estimated_minutes")
            or "-"
        )
        priority = schedule.get("priority") or task_detail.get("priority") or "-"
        preferred_window = task_detail.get("preferred_window") or "bebas"
        deadline = task_detail.get("deadline")

        reason = _build_single_schedule_reason(
            start_time=start_time_raw,
            deadline=deadline,
            preferred_window=preferred_window,
            index=idx,
        )

        reason_lines.append(
            f"{idx}. {task_title} dijadwalkan pada {start_time} "
            f"karena {reason}. Durasi {duration} menit dan priority {priority}."
        )

    return (
        "Cek dulu daftar tugas dan draft jadwal ini.\n\n"
        "Alasan penjadwalan:\n"
        + "\n".join(reason_lines)
        + "\n\nKamu bisa approve, edit, tambah, atau hapus sebelum dijadwalkan."
    )


def _format_schedule_time(value: str | None) -> str:
    if not value:
        return "waktu yang tersedia"
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(value)


def _build_single_schedule_reason(
    start_time: str | None,
    deadline: str | None,
    preferred_window: str,
    index: int,
) -> str:
    return "mengikuti urutan prioritas dan slot waktu kosong di kalender"


def apply_hitl_edits(
    hitl_result: dict,
    task_breakdown: list[TaskBreakdown],
    proposed_schedule: list[ScheduleItem],
    existing_schedules: list[dict] = None,
) -> tuple[list[TaskBreakdown], list[ScheduleItem]]:
    edited_tasks = hitl_result.get("tasks")
    edited_schedule = hitl_result.get("proposed_schedule")

    final_tasks = edited_tasks or task_breakdown

    if edited_tasks and not edited_schedule:
        final_schedule = build_proposed_schedule(final_tasks, existing_schedules)
    else:
        final_schedule = edited_schedule or proposed_schedule

    return final_tasks, final_schedule


def make_prioritizer(llm: BaseChatModel, calendar_client=None):
    structured_llm = llm.with_structured_output(LLMTaskBreakdownResponse)

    def run(state: AppState) -> dict:
        previous_status = state.get("hitl_status")
        existing_tasks = state.get("task_breakdown") or []
        existing_schedule = state.get("proposed_schedule") or []

        # Ambil intent user secara umum
        current_intent = state.get("current_intent", "manage_task")

        # Ambil Jadwal Mentah untuk algoritma jadwal
        raw_schedules = _fetch_raw_schedules(calendar_client, state)
        schedule_context = (
            _format_schedule_context(raw_schedules) if raw_schedules else ""
        )

        if previous_status == "rejected" and existing_tasks:
            task_breakdown = existing_tasks
            proposed_schedule = existing_schedule or build_proposed_schedule(
                task_breakdown, raw_schedules
            )
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
                task_breakdown = build_task_breakdown_with_llm(
                    raw_tasks,
                    structured_llm,
                    schedule_context=schedule_context,
                    intent=current_intent,
                )
                print("[Agent 3] LLM prioritizer berhasil dipakai.")
            except Exception as err:
                print(
                    f"[Agent 3] LLM prioritizer gagal, fallback dipakai: {type(err).__name__}: {err}"
                )
                task_breakdown = build_task_breakdown_rule_based(raw_tasks)

            # Passing raw_schedules ke algoritma scheduling
            proposed_schedule = build_proposed_schedule(task_breakdown, raw_schedules)

        hitl_result = (
            interrupt(
                {
                    "type": "task_review",
                    "message": build_review_reasoning_message(
                        task_breakdown=task_breakdown,
                        proposed_schedule=proposed_schedule,
                    ),
                    "tasks": task_breakdown,
                    "proposed_schedule": proposed_schedule,
                }
            )
            or {}
        )

        # PENYESUAIAN: Menerima "approved_data" atau "approved" untuk validasi cURL nested
        approved_val = hitl_result.get("approved")
        if approved_val is None:
            approved_val = hitl_result.get("approved_data")

        # Kalau formatnya dictionary {"approved_data": true} dari nested cURL
        if isinstance(approved_val, dict):
            approved = bool(
                approved_val.get("approved", approved_val.get("approved_data"))
            )
        else:
            approved = bool(approved_val)

        final_tasks, final_schedule = apply_hitl_edits(
            hitl_result=hitl_result,
            task_breakdown=task_breakdown,
            proposed_schedule=proposed_schedule,
            existing_schedules=raw_schedules,
        )

        if not approved:
            return {
                **ai_msg(
                    "Baik, jadwal belum disetujui. Silakan edit dulu daftar tugasnya."
                ),
                "task_breakdown": final_tasks,
                "proposed_schedule": final_schedule,
                "error_message": None,
                "hitl_status": "rejected",
                "hitl_input": hitl_result,
            }

        return {
            **ai_msg(
                f"Siap, {len(final_tasks)} tugas sudah disetujui dan akan lanjut ke penjadwalan."
            ),
            "task_breakdown": final_tasks,
            "proposed_schedule": final_schedule,
            "error_message": None,
            "hitl_status": "approved",
            "hitl_input": hitl_result,
        }

    return run


def build_task_breakdown_with_llm(
    raw_tasks: list[RawTask],
    structured_llm,
    schedule_context: str = "",
    intent: str = "manage_task",
) -> list[TaskBreakdown]:

    normalized_raw_tasks = [
        _raw_task_to_dict(task, idx) for idx, task in enumerate(raw_tasks, start=1)
    ]

    today = datetime.now().strftime("%Y-%m-%d")

    # Prompt dipangkas dan difokuskan ke raw_tasks beserta description-nya
    prompt_content = (
        f"Tanggal hari ini: {today}\n\n"
        f"Kondisi Mental/Intent User secara keseluruhan: {intent}\n\n"
        + (
            f"Konteks jadwal existing kalender:\n{schedule_context}\n\n"
            if schedule_context
            else ""
        )
        + "Ubah raw_tasks berikut menjadi task breakdown terstruktur:\n"
        f"{normalized_raw_tasks}"
    )

    result = structured_llm.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content},
        ]
    )

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

        breakdown.append(
            {
                "task_id": parsed.task_id or f"task_{idx:03d}",
                "title": parsed.title,
                "subtasks": subtasks,
                "estimated_minutes": int(parsed.estimated_minutes),
                "deadline": parsed.deadline,
                "priority": priority,
                "category": parsed.category,
                "preferred_window": parsed.preferred_window,
            }
        )

    breakdown.sort(
        key=lambda x: (
            x["priority"],
            _deadline_sort_value(x.get("deadline")),
            -int(x["estimated_minutes"]),
            x["task_id"],
        )
    )

    return breakdown


def calculate_priority(
    urgency: int, importance: int, effort: int, energy_fit: int
) -> int:
    score = 0.45 * urgency + 0.30 * importance + 0.15 * (6 - effort) + 0.10 * energy_fit
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
        data.get("raw_input") or data.get("description") or data.get("title") or ""
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
    if any(
        k in text
        for k in [
            "kuliah",
            "kelas",
            "materi",
            "belajar",
            "project",
            "proyek",
            "laporan",
            "proposal",
            "ujian",
        ]
    ):
        return "serius"
    if any(k in text for k in ["istirahat", "break", "main game", "main", "rebahan"]):
        return "santai"
    if any(k in text for k in ["meeting", "organisasi", "rapat"]):
        return "lainnya"
    return "biasa"


def estimate_duration(task: str) -> int:
    text = task.lower()
    if any(
        k in text
        for k in [
            "laporan",
            "proposal",
            "skripsi",
            "makalah",
            "project",
            "proyek",
            "capstone",
            "ui",
            "dashboard",
        ]
    ):
        return 120
    if any(k in text for k in ["demo", "presentasi"]):
        return 90
    return 60


def estimate_priority(task: str) -> int:
    text = task.lower()
    score = 0
    if any(
        k in text
        for k in [
            "deadline",
            "besok",
            "hari ini",
            "urgent",
            "segera",
            "mepet",
            "demo",
            "presentasi",
            "ujian",
        ]
    ):
        score += 4
    elif "minggu ini" in text or any(
        k in text
        for k in [
            "bug",
            "error",
            "fix",
            "hotfix",
            "laporan",
            "proposal",
            "revisi",
            "project",
        ]
    ):
        score += 3
    elif any(k in text for k in ["meeting", "rapat"]):
        score += 2
    else:
        score += 1

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
        return (
            (now + timedelta(days=1))
            .replace(hour=23, minute=59, second=0, microsecond=0)
            .isoformat()
        )
    if "minggu ini" in text:
        return (
            (now + timedelta(days=7))
            .replace(hour=23, minute=59, second=0, microsecond=0)
            .isoformat()
        )
    return None


def build_task_breakdown_rule_based(raw_tasks: list[RawTask]) -> list[TaskBreakdown]:
    breakdown: list[TaskBreakdown] = []
    for idx, raw in enumerate(raw_tasks, start=1):
        data = _raw_task_to_dict(raw, idx)
        cleaned = normalize_text(source_text(raw, idx))
        title = data.get("title") or cleaned or f"Tugas {idx}"
        breakdown.append(
            {
                "task_id": data.get("task_id") or f"task_{idx:03d}",
                "title": title,
                "subtasks": build_basic_subtasks(cleaned),
                "estimated_minutes": estimate_duration(cleaned),
                "deadline": extract_deadline(cleaned),
                "priority": estimate_priority(cleaned),
                "category": detect_category(cleaned),
                "preferred_window": detect_preferred_window(cleaned),
            }
        )
    breakdown.sort(
        key=lambda x: (
            x["priority"],
            _deadline_sort_value(x.get("deadline")),
            -int(x["estimated_minutes"]),
            x["task_id"],
        )
    )
    return breakdown


def _fetch_raw_schedules(calendar_client, state: AppState) -> list[dict]:
    if calendar_client is None:
        return []
    metadata = get_metadata(state) or {}
    token = _extract_auth_token(metadata)
    try:
        schedules = calendar_client.list_schedules(token=token)
        return schedules if schedules else []
    except Exception as err:
        print(f"[Agent 3] Calendar context error: {err}")
        return []


def _fetch_schedule_context(calendar_client, state: AppState) -> str:
    schedules = _fetch_raw_schedules(calendar_client, state)
    if not schedules:
        return "(tidak ada jadwal)"
    return _format_schedule_context(schedules)


def _format_schedule_context(schedules: list[dict]) -> str:
    lines = []
    for item in schedules[:5]:
        title = str(item.get("title") or "(tanpa judul)")
        start_time = item.get("startTime") or item.get("start_time")
        deadline = item.get("endTime") or item.get("deadline")
        status = item.get("status") or "pending"
        time_part = f" ({start_time} - {deadline})" if start_time else ""
        lines.append(f"- {title} [{status}]{time_part}")
    return "\n".join(lines)


def build_basic_subtasks(task_text: str) -> list[str]:
    return [
        f"Mulai kerjakan: {task_text.strip()}",
        "Lanjutkan bagian utama",
        "Cek hasil dan rapikan",
    ]


def _deadline_sort_value(deadline: str | None) -> str:
    return deadline or "9999-12-31T23:59:59"


def _extract_auth_token(metadata: dict) -> str | None:
    for key in ("auth_token", "access_token", "authorization"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def minutes_to_iso(total_minutes: int, base_date: str) -> str:
    hour = total_minutes // 60
    minute = total_minutes % 60

    # PERBAIKAN: Menangani jam lembur hingga lintas hari (melewati 24:00)
    if hour >= 24:
        extra_days = hour // 24
        hour = hour % 24
        base_dt = datetime.fromisoformat(base_date) + timedelta(days=extra_days)
        base_date = base_dt.strftime("%Y-%m-%d")

    return f"{base_date}T{hour:02d}:{minute:02d}:00"


def _get_busy_slots(schedules: list[dict], target_date: str) -> list[tuple[int, int]]:
    busy = []
    for s in schedules:
        start_str = s.get("startTime") or s.get("start_time")
        end_str = s.get("endTime") or s.get("deadline")
        if not start_str or not end_str:
            continue

        try:
            # PERBAIKAN: Jadikan aware datetime agar aman dibandingan
            st = datetime.fromisoformat(str(start_str).replace("Z", "+00:00"))
            if st.tzinfo is None:
                st = st.astimezone()

            ed = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
            if ed.tzinfo is None:
                ed = ed.astimezone()

            if st.strftime("%Y-%m-%d") == target_date:
                start_min = st.hour * 60 + st.minute
                end_min = ed.hour * 60 + ed.minute
                busy.append((start_min, end_min))
        except ValueError:
            pass
    return sorted(busy, key=lambda x: x[0])


def _find_free_slot(
    start_search: int, duration: int, busy_slots: list[tuple[int, int]]
) -> int:
    current_attempt = start_search
    for b_start, b_end in busy_slots:
        if current_attempt + duration <= b_start:
            return current_attempt
        if current_attempt < b_end:
            current_attempt = b_end + 5
    return current_attempt


def build_proposed_schedule(
    task_breakdown: list[TaskBreakdown], existing_schedules: list[dict] = None
) -> list[ScheduleItem]:
    proposed_schedule: list[ScheduleItem] = []
    if existing_schedules is None:
        existing_schedules = []

    # PERBAIKAN: Jadikan 'now' offset-aware lokal agar tidak crash saat diadu dengan deadline
    now = datetime.now().astimezone()
    current_date_dt = now

    for item in task_breakdown:
        duration = int(item.get("estimated_minutes", 60))
        preferred_window = item.get("preferred_window", "bebas")

        deadline = item.get("deadline")
        deadline_dt = None
        if deadline:
            try:
                parsed_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                # Pastikan deadline_dt juga offset-aware lokal
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.astimezone()
                else:
                    parsed_dt = parsed_dt.astimezone()
                deadline_dt = parsed_dt
            except ValueError:
                pass

        ideal_dt = now + timedelta(minutes=15)

        if deadline_dt:
            latest_start_dt = deadline_dt - timedelta(minutes=duration)

            if latest_start_dt < now:
                ideal_dt = now + timedelta(minutes=15)
            else:
                pref_mins = WINDOW_START.get(preferred_window, 9 * 60)
                pref_dt = deadline_dt.replace(
                    hour=pref_mins // 60, minute=pref_mins % 60, second=0, microsecond=0
                )

                # LOGIKA BARU: Tarik mundur ke H-1 (malam) kalau mepet banget (sebelum jam 8 pagi)
                if latest_start_dt.hour < 8:
                    prev_day = deadline_dt - timedelta(days=1)
                    ideal_dt = prev_day.replace(
                        hour=19, minute=0, second=0, microsecond=0
                    )

                # LOGIKA BARU: Kalau preferred window bikin nabrak deadline
                elif pref_dt + timedelta(minutes=duration) > deadline_dt:
                    if preferred_window in ["malam", "sore"]:
                        # Geser ke sore/malam hari sebelumnya
                        prev_day = deadline_dt - timedelta(days=1)
                        ideal_dt = prev_day.replace(
                            hour=pref_mins // 60,
                            minute=pref_mins % 60,
                            second=0,
                            microsecond=0,
                        )
                    else:
                        ideal_dt = latest_start_dt
                else:
                    ideal_dt = pref_dt
        else:
            pref_mins = WINDOW_START.get(preferred_window, 9 * 60)
            pref_dt = current_date_dt.replace(
                hour=pref_mins // 60, minute=pref_mins % 60, second=0, microsecond=0
            )

            if pref_dt < now:
                ideal_dt = now + timedelta(minutes=15)
            else:
                ideal_dt = pref_dt

        # Pastikan tidak menjadwalkan di masa lalu
        if ideal_dt < now:
            ideal_dt = now + timedelta(minutes=15)

        base_date_str = ideal_dt.strftime("%Y-%m-%d")

        # Tarik slot sibuk
        busy_slots = _get_busy_slots(existing_schedules, base_date_str)
        for p in proposed_schedule:
            try:
                # PERBAIKAN: Samakan perlakuannya dengan data existing_schedules
                p_dt = datetime.fromisoformat(p["start_time"].replace("Z", "+00:00"))
                if p_dt.tzinfo is None:
                    p_dt = p_dt.astimezone()

                if p_dt.strftime("%Y-%m-%d") == base_date_str:
                    p_start = p_dt.hour * 60 + p_dt.minute
                    p_end = p_start + p["duration_minutes"] + 5
                    busy_slots.append((p_start, p_end))
            except ValueError:
                pass
        busy_slots.sort(key=lambda x: x[0])

        start_search_mins = ideal_dt.hour * 60 + ideal_dt.minute
        start_time_minutes = _find_free_slot(start_search_mins, duration, busy_slots)

        start_iso = minutes_to_iso(start_time_minutes, base_date_str)

        proposed_schedule.append(
            {
                "task_id": item["task_id"],
                "task": item["title"],
                "priority": int(item["priority"]),
                "start_time": start_iso,
                "duration_minutes": duration,
                "category": item["category"],
                "subtasks": item["subtasks"],
            }
        )

        # Update urutan waktu untuk task beruntun supaya gak numpuk
        scheduled_start_dt = datetime.fromisoformat(start_iso)
        current_date_dt = scheduled_start_dt + timedelta(minutes=duration + 10)

    return proposed_schedule
