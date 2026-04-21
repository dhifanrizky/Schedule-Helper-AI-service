from app.graph.state import AppState
from app.graph.agents.helpers import last_message

# ---------------------------------------------------------------------------
# Isi INTENT_MAP dan logic _classify() sesuai kebutuhanmu.
# Tambah intent baru = tambah key baru di INTENT_MAP, tidak perlu ubah lain.
# ---------------------------------------------------------------------------

type IntentMap = dict[str, list[str]]


def make_router(intent_map: IntentMap):
    """
    Factory untuk RouterAgent.
    Tugas: klasifikasi intent dari pesan user → update state["intent"].
    """

    def run(state: AppState) -> dict:
        text = last_message(state)
        intent = _classify(text, intent_map)
        return {"intent": intent}

    return run


def _classify(text: str, intent_map: IntentMap) -> str:
    """
    TODO: implementasi logika klasifikasi intent-mu di sini.
    Bisa pakai keyword matching, LLM call, atau classifier model.
    Harus return salah satu key dari intent_map, atau "general" sebagai fallback.
    """
    raise NotImplementedError