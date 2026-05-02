from typing import Annotated, Literal, Optional, TypedDict
import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

CategoryType = Literal["serius", "santai", "biasa", "lainnya"]
PreferredWindow = Literal["pagi", "siang", "sore", "malam", "bebas"]
IntentType = Literal["stress", "overload", "manage_task", "schedule"]
class ScheduleItem(TypedDict):
    task_id: str
    task: str
    priority: int
    start_time: str
    duration_minutes: int
    category: CategoryType

class RawTask(BaseModel):
    task_id: str = Field(
        default="",
        description="ID yang ditetapkan sistem setelah routing, misalnya UUID atau format lain yang tidak dibuat LLM",
    )
    title: str = Field(description="Judul singkat dalam bahasa user")
     
    description: str = Field(
        description="JANGAN sekadar merangkum! Kamu WAJIB mendeskripsikan 2 hal secara eksplisit menggunakan bahasa user: (1) Apa perasaan/tingkat urgensi user (jika tidak ada, tulis 'Perasaan tidak disebutkan eksplisit'), (2) Detail apa yang masih belum jelas atau tidak disebutkan (misal: nama matkul, detail topik)."
    )
    
    raw_time: Optional[str] = Field(description="Frasa waktu dari ucapan user, atau null jika tidak ada")
    raw_input: str = Field(description="Kalimat asli yang diucapkan user")
    category: CategoryType

class TaskBreakdown(TypedDict):
    task_id: str          # foreign key ke RawTask
    title: str
    subtasks: list[str]
    estimated_minutes: int
    deadline: str | None  # ISO 8601
    priority: int         # 1 = tertinggi
    category: CategoryType
    preferred_window: PreferredWindow

class RouterOutput(TypedDict):
    current_intent: IntentType | None
    raw_tasks: list[RawTask]

class GraphState(RouterOutput, total=False):
    # conversation
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str

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