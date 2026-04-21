from pydantic import BaseModel, Field

from app.graph.types import ScheduleItem


# ── Request schemas ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:   str = Field(..., min_length=1)
    user_id:   str
    thread_id: str | None = None   # None = buat thread baru


class HITLResumeRequest(BaseModel):
    """
    Payload dari NestJS setelah user approve/edit di frontend.
    Format approved_data tergantung agent yang sedang interrupt:

    Counselor:
        {"approved": true, "edited_draft": "..." | null}

    Prioritizer:
        {"tasks": [{"task": "...", "priority": 1, "deadline": "..."}]}
    """
    approved_data: dict


# ── Response schemas ──────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    thread_id:    str
    status:       str          # "waiting_hitl" | "done"
    next_node:    list[str]    # node mana yang akan jalan setelah resume
    hitl_payload: dict | None  # data yang perlu ditampilkan ke user


class ResumeResponse(BaseModel):
    thread_id:    str
    status:       str          # "waiting_hitl" | "done"
    next_node:    list[str]
    hitl_payload: dict | None


class StateResponse(BaseModel):
    thread_id:         str
    pending_hitl:      bool
    next_node:         list[str]
    current_intent:    str | None
    raw_tasks:         list[str]
    counselor_response: list[str]
    counselor_done:     bool
    task_breakdown:    list[dict]
    proposed_schedule: list[ScheduleItem]
    api_status:        int | None
    api_payload:       dict | None
    final_message:     str | None
    error_message:     str | None
    hitl_payload:      dict | None
