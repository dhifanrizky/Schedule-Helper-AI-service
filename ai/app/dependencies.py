from functools import lru_cache
from app.services.llm import get_llm
from app.services.calendar import get_calendar_client
from app.services.checkpointer import get_checkpointer
from app.graph.agents.router import make_router
from app.graph.agents.counselor import make_counselor
from app.graph.agents.prioritizer import make_prioritizer
from app.graph.agents.scheduler import make_scheduler
from app.graph.builder import build_graph

# ---------------------------------------------------------------------------
# Intent map — tambah intent baru di sini, tidak perlu ubah file lain.
# ---------------------------------------------------------------------------

INTENT_MAP: dict[str, list[str]] = {
    "stress":      ["stres", "overwhelmed", "pusing", "anxious"],
    "overload":    ["kewalahan", "numpuk", "banyak banget", "tidak sanggup"],
    "manage_task": ["tugas", "deadline", "prioritas", "kerjaan"],
    "schedule":    ["jadwalkan", "kalender", "reminder", "meeting"],
}


@lru_cache
def get_graph():
    """
    Inisialisasi dan compile graph sekali — di-cache selama app hidup.
    Semua dependency di-inject di sini.
    """
    llm = get_llm()
    agents = {
        "router":      make_router(INTENT_MAP),
        "counselor":   make_counselor(llm),
        "prioritizer": make_prioritizer(llm),
        "scheduler":   make_scheduler(llm, get_calendar_client()),
    }
    return build_graph(agents, checkpointer=get_checkpointer())