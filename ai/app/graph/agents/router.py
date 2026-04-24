from typing import TypedDict

from langchain_core.language_models import BaseChatModel

from app.graph.state import AppState
from app.graph.agents.helpers import last_message
from app.graph.types import GraphState

# ---------------------------------------------------------------------------
# Isi INTENT_MAP dan logic _classify() sesuai kebutuhanmu.
# Tambah intent baru = tambah key baru di INTENT_MAP, tidak perlu ubah lain.
# ---------------------------------------------------------------------------

type IntentMap = dict[str, list[str]]

SYSTEM_PROMPT="""
    You are a router agent. your job is to output *ONLY JSON* that have this structure:

"""

class RouterOutput(TypedDict):
    current_intent: GraphState.
    raw_tasks: list[RawTask]

def make_router(intent_map: IntentMap, llm:BaseChatModel):
    """
    Factory untuk RouterAgent.
    Tugas: klasifikasi intent dari pesan user -> update state["current_intent"].
    """

    structured_output = llm.with_structured_output(RouterOutput)
    def run(state: AppState) -> dict:
        text = last_message(state)
        intent = _classify(text, intent_map)
        return {"current_intent": intent}

    return run


def _classify(text: str, intent_map: IntentMap) -> str:
    """
    TODO: implementasi logika klasifikasi intent-mu di sini.
    Bisa pakai keyword matching, LLM call, atau classifier model.
    Harus return salah satu key dari intent_map, atau "general" sebagai fallback.
    """
    
    raise NotImplementedError