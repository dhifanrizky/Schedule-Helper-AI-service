from typing import Annotated, Literal, TypedDict
import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

category=Literal["kuliah", "tugas", "istirahat", "lainnya"]

class ScheduleItem(TypedDict):
    task_id: int
    task: str
    priority: int
    start_time: str
    duration_minutes: int
    category: category

class RawTask(TypedDict):
    task_id: str          # "task_001"
    title: str
    raw_input: str        # persis kata user
    category: category

class TaskBreakdown(TypedDict):
    task_id: str          # foreign key ke RawTask
    title: str
    subtasks: list[str]
    estimated_minutes: int
    deadline: str | None  # ISO 8601
    priority: int         # 1 = tertinggi

class GraphState(TypedDict, total=False):
    # conversation
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str

    # agent 1
    current_intent: Literal["stress", "overload", "manage_task", "schedule"] | None
    raw_tasks: list[RawTask]       

    # agent 2
    counselor_response: Annotated[list[str], operator.add] 
    counselor_done: bool

    # agent 3
    task_breakdown: list[TaskBreakdown]  
    proposed_schedule: list[ScheduleItem]

    # agent 4
    api_payload: dict | None
    api_status: int | None
    final_message: str | None
    error_message: str | None

    # kontrol
    hitl_status: Literal["pending", "approved", "rejected"] | None
    hitl_input: dict | None
    metadata: dict