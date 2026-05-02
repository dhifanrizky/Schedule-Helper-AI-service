import asyncio
from app.services.llm import get_llm
from app.services.calendar import get_calendar_client
from app.services.checkpointer import get_checkpointer
from app.graph.agents.router import make_router
from app.graph.agents.counselor import make_counselor
from app.graph.agents.prioritizer import make_prioritizer
from app.graph.agents.scheduler import make_scheduler
from app.graph.builder import build_graph
from langgraph.graph.state import CompiledStateGraph

INTENT_MAP: dict[str, list[str]] = {
    "stress":      ["stres", "overwhelmed", "pusing", "anxious"],
    "overload":    ["kewalahan", "numpuk", "banyak banget", "tidak sanggup"],
    "manage_task": ["tugas", "deadline", "prioritas", "kerjaan"],
    "schedule":    ["jadwalkan", "kalender", "reminder", "meeting"],
}

ROUTER_LLM_PROVIDER = "groq"
ROUTER_LLM_MODEL = "openai/gpt-oss-120b"
ROUTER_LLM_TEMPERATURE = 0.3

_graph: CompiledStateGraph | None = None
_graph_lock = asyncio.Lock()


def clear_graph_cache() -> None:
    global _graph
    _graph = None

async def get_graph() -> CompiledStateGraph:
    """
    Inisialisasi dan compile graph sekali — di-cache selama app hidup.
    Tiap agent di-inject dengan model LLM yang paling optimal untuk tugasnya.
    """
    
    global _graph
    if _graph is not None:
        return _graph

    async with _graph_lock:
        if _graph is not None:
            return _graph

        # 1. Router: Butuh speed & JSON akurat 
        router_llm = get_llm(
            provider=ROUTER_LLM_PROVIDER,
            model=ROUTER_LLM_MODEL,
            temperature=ROUTER_LLM_TEMPERATURE,
        )
    
        # 2. Counselor: Butuh empati tinggi 
        counselor_llm = get_llm("gemini", "gemini-2.5-flash", temperature=0.7)
    
        # 3. Prioritizer: Butuh logika urutan mantap 
        prioritizer_llm = get_llm("gemini", "gemini-1.5-flash", temperature=0.2)
    
        # 4. Scheduler: Butuh function calling konsisten 
        scheduler_llm = get_llm("gemini", "gemini-2.5-flash", temperature=0.0)

        agents = {
            "router":      make_router(INTENT_MAP, router_llm),
            "counselor":   make_counselor(counselor_llm),
            "prioritizer": make_prioritizer(prioritizer_llm),
            "scheduler":   make_scheduler(scheduler_llm, get_calendar_client()),
        }

        _graph = build_graph(agents, checkpointer=await get_checkpointer())

        return _graph