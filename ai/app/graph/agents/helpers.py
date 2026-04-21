from langchain_core.messages import AIMessage
from app.graph.state import AppState


def last_message(state: AppState) -> str:
    content = state["messages"][-1].content
    
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return " ".join(
            item if isinstance(item, str) else str(item)
            for item in content
        )
    
    return str(content)

def ai_msg(text: str) -> dict:
    """Shorthand untuk return AIMessage ke messages."""
    return {"messages": [AIMessage(content=text)]}


def get_intent(state: AppState) -> str | None:
    return state.get("intent")


def get_task_list(state: AppState) -> list[dict]:
    return state.get("task_list") or []


def get_metadata(state: AppState) -> dict:
    return state.get("metadata") or {}


def get_hitl_input(state: AppState) -> dict | None:
    return state.get("hitl_input")