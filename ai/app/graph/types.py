from typing import Annotated, Literal, TypedDict
import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ScheduleItem(TypedDict):
    task_id: int
    task: str
    priority: int
    start_time: str
    duration_minutes: int
    category: Literal["kuliah", "tugas", "istirahat", "lainnya"]


class GraphState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str
    current_intent: str | None
    intent: str | None
    raw_tasks: Annotated[list[str], operator.add]
    task_list: Annotated[list[dict], operator.add]
    counselor_response: Annotated[list[str], operator.add]
    counselor_done: bool
    task_breakdown: Annotated[list[dict], operator.add]
    proposed_schedule: list[ScheduleItem]
    api_status: int | None
    api_payload: dict | None
    final_message: str | None
    error_message: str | None
    metadata: dict
    hitl_status: str | None
    hitl_input: dict | None
