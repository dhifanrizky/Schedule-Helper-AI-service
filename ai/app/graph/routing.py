from langgraph.graph import END
from app.graph.state import AppState

# ---------------------------------------------------------------------------
# Mapping intent -> node name.
# Tambah intent baru = tambah entry di ROUTING_MAP saja.
# ---------------------------------------------------------------------------

ROUTING_MAP: dict[str, str] = {
    "stress":      "counselor",
    "overload":    "counselor",
    "manage_task": "prioritizer",
    "schedule":    "prioritizer",
    "general":     END,
}


def route_by_intent(state: AppState) -> str:
    intent = state.get("current_intent") or "general"
    return ROUTING_MAP.get(intent, END)


def route_after_counselor(state: AppState) -> str:
    """
    Counselor loop:
    - counselor_done=True  -> lanjut ke prioritizer
    - counselor_done=False -> ulang counselor
    """
    return "prioritizer" if state.get("counselor_done") else "counselor"


def route_after_prioritizer(state: AppState) -> str:
    """
    Prioritizer gate:
    - hitl_status=approved -> lanjut ke scheduler
    - selain itu           -> ulang prioritizer untuk review ulang
    """
    return "scheduler" if state.get("hitl_status") == "approved" else "prioritizer"
