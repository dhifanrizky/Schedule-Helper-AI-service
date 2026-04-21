from langchain_core.messages import AIMessage
from app.graph.state import AppState
from app.graph.types import RawTask, ScheduleItem, TaskBreakdown


def last_message(state: AppState) -> str:
    user_input = state.get("user_input")
    if isinstance(user_input, str) and user_input.strip():
        return user_input

    messages = state.get("messages") or []
    if not messages:
        return ""

    content = messages[-1].content

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


def get_current_intent(state: AppState) -> str | None:
    return state.get("current_intent") 


def get_intent(state: AppState) -> str | None:
    return get_current_intent(state)


def get_raw_tasks(state: AppState) -> list[RawTask]:
    return state.get("raw_tasks") or []


def get_task_breakdown(state: AppState) -> list[TaskBreakdown]:
    return state.get("task_breakdown") or []


def get_proposed_schedule(state: AppState) -> list[ScheduleItem]:
    return state.get("proposed_schedule") or []


def get_api_status(state: AppState) -> int | None:
    return state.get("api_status")


def get_api_payload(state: AppState) -> dict | None:
    return state.get("api_payload")


def get_final_message(state: AppState) -> str | None:
    return state.get("final_message")


def get_error_message(state: AppState) -> str | None:
    return state.get("error_message")


def get_counselor_response(state: AppState) -> list[str]:
    return state.get("counselor_response") or []


def get_counselor_done(state: AppState) -> bool:
    return bool(state.get("counselor_done"))


def get_metadata(state: AppState) -> dict:
    return state.get("metadata") or {}


def get_hitl_input(state: AppState) -> dict | None:
    return state.get("hitl_input")
