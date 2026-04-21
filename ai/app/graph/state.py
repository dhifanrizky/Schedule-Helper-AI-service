from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AppState(TypedDict):
    messages:    Annotated[list[BaseMessage], add_messages]
    intent:      str | None
    task_list:   list[dict]
    metadata:    dict
    hitl_status: str | None   # "waiting" | "approved" | None
    hitl_input:  dict | None  # data yang dikirim dari /resume