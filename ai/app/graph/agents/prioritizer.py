# ---------------------------------------------------------------------------
# Agent 3: PrioritizerAgent
# HITL aktif di sini - user bisa edit/hapus/tambah task sebelum dijadwalkan.
# ---------------------------------------------------------------------------
from datetime import datetime, timedelta

from langgraph.types import interrupt
from app.graph.state import AppState
from app.graph.agents.helpers import ai_msg, get_raw_tasks
from app.graph.types import RawTask, TaskBreakdown, ScheduleItem

WINDOW_START = {
    "pagi": 8 * 60,
    "siang": 13 * 60,
    "sore": 16 * 60,
    "malam": 19 * 60,
    "bebas": 9 * 60,
}


def make_prioritizer(llm):
    def run(state: AppState) -> dict:
        raw_tasks = get_raw_tasks(state)

        if not raw_tasks:
            return {
                **ai_msg("Aku belum menemukan tugas yang bisa diprioritaskan."),
                "task_breakdown": [],
                "proposed_schedule": [],
                "error_message": "raw_tasks kosong.",
            }

        task_breakdown = build_task_breakdown(raw_tasks)
        proposed_schedule = build_proposed_schedule(task_breakdown)

        hitl_result = interrupt({
            "type": "task_review",
            "message": "Cek dan edit daftar tugas sebelum dijadwalkan.",
            "tasks": task_breakdown,
            "proposed_schedule": proposed_schedule,
        }) or {}

        final_tasks = hitl_result.get("tasks") or task_breakdown
        final_schedule = hitl_result.get("proposed_schedule") or proposed_schedule

        return {
            **ai_msg(f"Siap, {len(final_tasks)} tugas akan dijadwalkan."),
            "task_breakdown": final_tasks,
            "proposed_schedule": final_schedule,
            "error_message": None,
            "hitl_status": "approved",
            "hitl_input": None,
        }

    return run


def source_text(task: RawTask) -> str:
    return (task.get("raw_input") or task.get("title") or "").strip()


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def detect_preferred_window(task: str) -> str:
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


def detect_category(task: str) -> str:
    text = task.lower()

    if any(k in text for k in ["kuliah", "kelas", "materi", "belajar", "dokumentasi", "langgraph"]):
        return "kuliah"

    if any(k in text for k in ["istirahat", "break", "main game", "main", "rebahan"]):
        return "istirahat"

    if any(k in text for k in ["meeting", "organisasi", "rapat"]):
        return "lainnya"

    return "tugas"


def estimate_duration(task: str) -> int:
    text = task.lower()

    if any(k in text for k in ["laporan", "proposal"]):
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

    if any(k in text for k in ["deadline", "besok", "hari ini", "urgent", "segera"]):
        score += 4
    if any(k in text for k in ["demo", "presentasi", "ujian"]):
        score += 4
    if any(k in text for k in ["bug", "error", "fix", "hotfix"]):
        score += 3
    if any(k in text for k in ["laporan", "proposal", "revisi"]):
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

    return None


def build_task_breakdown(raw_tasks: list[RawTask]) -> list[TaskBreakdown]:
    breakdown: list[TaskBreakdown] = []

    for idx, raw in enumerate(raw_tasks, start=1):
        cleaned = normalize_text(source_text(raw))
        task_id = raw.get("task_id") or f"task_{idx:03d}"
        title = raw.get("title") or cleaned

        breakdown.append({
            "task_id": task_id,
            "title": title,
            "subtasks": [cleaned],
            "estimated_minutes": estimate_duration(cleaned),
            "deadline": extract_deadline(cleaned),
            "priority": estimate_priority(cleaned),
            "category": detect_category(cleaned),
            "preferred_window": detect_preferred_window(cleaned),
        })

    breakdown.sort(
        key=lambda x: (
            x["priority"],
            -x["estimated_minutes"],
            x["task_id"],
        )
    )

    return breakdown


def minutes_to_iso(total_minutes: int, base_date: str) -> str:
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{base_date}T{hour:02d}:{minute:02d}:00"


def build_proposed_schedule(task_breakdown: list[TaskBreakdown]) -> list[ScheduleItem]:
    proposed_schedule: list[ScheduleItem] = []
    current_time = 9 * 60
    base_date = datetime.now().strftime("%Y-%m-%d")

    for idx, item in enumerate(task_breakdown, start=1):
        preferred_window = item.get("preferred_window", "bebas")
        preferred_start = WINDOW_START.get(preferred_window, 9 * 60)
        start_time_minutes = max(current_time, preferred_start)

        proposed_schedule.append({
            "task_id": item["task_id"],
            "task": item["subtasks"][0] if item["subtasks"] else item["title"],
            "priority": item["priority"],
            "start_time": minutes_to_iso(start_time_minutes, base_date),
            "duration_minutes": item["estimated_minutes"],
            "category": item["category"],
        })

        current_time = start_time_minutes + item["estimated_minutes"]

    return proposed_schedule