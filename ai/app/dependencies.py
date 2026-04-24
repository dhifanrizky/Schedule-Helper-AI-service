from functools import lru_cache
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

@lru_cache
def get_graph() -> CompiledStateGraph:
    """
    Inisialisasi dan compile graph sekali — di-cache selama app hidup.
    Tiap agent di-inject dengan model LLM yang paling optimal untuk tugasnya.
    """
    
    # 1. Router: Butuh speed & JSON akurat -> Pakai Groq (Llama 3 8B), Temp 0
    router_llm = get_llm(
        provider="groq",
        model="llama-3.1-8b-instant", 
        temperature=0.1
    )
    
    # 2. Counselor: Butuh empati tinggi -> Pakai OpenAI (GPT-4o-mini), Temp 0.7
    counselor_llm = get_llm("openai", "gpt-4o-mini", temperature=0.7)
    
    # 3. Prioritizer: Butuh logika urutan mantap -> Pakai Gemini Flash, Temp 0.2
    prioritizer_llm = get_llm("openai", "gemini-1.5-flash", temperature=0.2)
    
    # 4. Scheduler: Butuh function calling konsisten -> Pakai OpenAI/Groq, Temp 0
    scheduler_llm = get_llm("openai", "gpt-4o-mini", temperature=0.0)

    agents = {
        "router":      make_router(INTENT_MAP, router_llm),
        "counselor":   make_counselor(counselor_llm),
        "prioritizer": make_prioritizer(prioritizer_llm),
        "scheduler":   make_scheduler(scheduler_llm, get_calendar_client()),
    }
    
    return build_graph(agents, checkpointer=get_checkpointer())