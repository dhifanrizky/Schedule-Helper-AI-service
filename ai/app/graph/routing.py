from langgraph.graph import END
from app.graph.state import AppState

# ---------------------------------------------------------------------------
# Mapping intent → node name.
# Tambah intent baru = tambah entry di ROUTING_MAP saja.
# ---------------------------------------------------------------------------

ROUTING_MAP: dict[str, str] = {
    "stress":      "counselor",
    "overload":    "counselor",
    "manage_task": "prioritizer",
    "schedule":    "scheduler",
    "general":     END,
}


def route_by_intent(state: AppState) -> str:
    intent = state.get("intent") or "general"
    return ROUTING_MAP.get(intent, END)