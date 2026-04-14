"""
Agent 1: Mind Dump Interpreter
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any, List, Literal, Optional, cast
import uuid

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_qwq import ChatQwen
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from pydantic import BaseModel, ConfigDict, Field, field_validator
import getpass

# Ensure project root (folder containing util/) is importable when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain.agents.middleware import HumanInTheLoopMiddleware
from util.calendar_service import CalendarService


if not os.getenv("DASHSCOPE_API_KEY"):
    os.environ["DASHSCOPE_API_KEY"] = getpass.getpass("Enter your Dashscope API key: ")
load_dotenv()


TODAY = date.today().isoformat()
MAX_CLARIFICATION_ROUNDS = 10
calendar_service = CalendarService()

class ClarificationQuestion(BaseModel):
    """Represents a specific question asked by the AI to clarify missing details."""
    task_id: str = Field(description="The ID of the task this question refers to")
    missing_field: str = Field(description="The specific field that is missing (e.g., 'duration', 'deadline')")
    question_text: str = Field(description="The actual question to ask the user, tailored to their mood/context")

class Task(BaseModel):
    """Represents a single parsed task from the mind dump."""
    id: str = Field(description="Sequential ID starting from '1' or a UUID")
    name: str = Field(description="Clean and concise name of the task")
    description: str = Field(description="Detailed explanation of the task")
    
    # --- Time Context ---
    scheduled_time: Optional[str] = Field(
        default=None, 
        description="Specific time the task is scheduled to happen (e.g., '10:00 AM', 'Tonight')"
    )
    deadline: Optional[str] = Field(
        default=None,
        description="Deadline in YYYY-MM-DD format, resolved from the current date"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Estimated duration in minutes"
    )
    
    # --- Context & Meta ---
    emotional_context: Optional[str] = Field(
        default=None,
        description="Explicit emotional or motivational signals from the user, captured verbatim"
    )

class TaskList(BaseModel):
    """Wrapper used specifically for the LLM structured output parser."""
    tasks: List[Task]

class AgentState(BaseModel):
    """Shared state for Agent 1 across all LangGraph nodes."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    mind_dump: str = Field(default="", description="The raw text input from the user")
    
    # Extracted data
    tasks: List[Task] = Field(default_factory=list, description="List of tasks extracted so far")
    
    # Loop & Clarification Management
    clarification_round: int = Field(default=0, description="Counter for the clarification loop")
    pending_questions: List[ClarificationQuestion] = Field(
        default_factory=list, 
        description="Questions currently waiting for user response"
    )
    clarification_history: List[dict] = Field(
        default_factory=list, 
        description="History of QA to provide context for the next extraction. Format: [{'role': 'user/assistant', 'content': '...'}]"
    )
    
    # Routing flag
    next_action: Literal["ask_clarification", "produce_output"] = Field(
        default="produce_output",
        description="Flag to determine the next node in the graph"
    )
    structured_output: Optional[dict[str, Any]] = Field(
        default=None,
        description="Final structured payload produced by finalizer"
    )

    @field_validator("clarification_round")
    @classmethod
    def round_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("clarification_round cannot be negative")
        return v
    
llm = ChatQwen(
    model="qwen-flash",
    temperature=0.3
)

structured_llm = llm.with_structured_output(TaskList)

INTERPRETER_SYSTEM_PROMPT = f"""Kamu adalah Agent 1 dari sistem Schedule Helper — seorang data extractor yang presisi dan empatik.
Tugas kamu: ekstrak SEMUA task/kegiatan yang disebutkan user dari teks bebas dan strukturkan ke dalam JSON sesuai skema.

Aturan penting ekstraksi:
- Tanggal hari ini adalah: {TODAY}. Gunakan ini untuk me-resolve kata seperti 'besok', 'lusa', atau 'minggu depan'.
- JANGAN asumsikan 'deadline' jika tidak disebutkan → biarkan null.
- JANGAN asumsikan 'duration_minutes' jika tidak disebutkan → biarkan null.
- 'emotional_context' HANYA diisi kalau ada sinyal emosional/motivasional EKSPLISIT dari user.
  Valid: "males banget", "excited", "takut ga kelar", "capek".
  TIDAK valid: "penting", "harus selesai" (kosongkan/null jika tidak ada emosi spesifik).
- Jika ada riwayat percakapan (clarification_history), gunakan info tersebut untuk mengisi data yang sebelumnya kosong pada task yang bersangkutan.
"""

def mind_dump_interpreter(state: AgentState):
    """
    Node that interpret human need
    """
    # 1. Ambil data dari eksternal/tools
    calendar_data = calendar_service.fetch_calendar()
    
    existing_tasks_context = ""
    if state.tasks:
        existing_tasks_context = "\nTasks already identified: " + str([t.dict() for t in state.tasks])

    dynamic_system_prompt = INTERPRETER_SYSTEM_PROMPT + \
        f"\n\n[Current Calendar]:\n{calendar_data}" + \
        f"\n\n[Existing Tasks in State]:{existing_tasks_context}" + \
        "\nIMPORTANT: If the user provides info for an existing task, UPDATE that task instead of creating a new one."
    
    # 2. Sisipkan konteks kalender ke dalam System Prompt agar AI bisa melihat jadwal bentrok/kosong
    messages: list[BaseMessage] = [
            SystemMessage(content=dynamic_system_prompt)
        ]
    
    
    # 4. Masukkan riwayat klarifikasi (Wajib!)
    # Jika agent ini dipanggil lagi setelah user menjawab pertanyaan klarifikasi, 
    # AI harus tahu konteks jawabannya untuk meng-update hasil ekstraksi sebelumnya.
    for chat in state.clarification_history:
        role = HumanMessage if chat["role"] == "user" else AIMessage
        messages.append(role(content=chat["content"]))

    messages.append(HumanMessage(content=state.mind_dump))

    # print(messages)
    # 5. Eksekusi LLM dengan daftar pesan lengkap
    # Karena pakai structured_output, kembaliannya langsung berupa objek Pydantic TaskList
    result = structured_llm.invoke(messages)
    
    # Ensure result is a TaskList object (handle dict case)
    if isinstance(result, dict):
        result = TaskList(**result)

    # 6. Return update state
    # Cukup kembalikan result.tasks (Pydantic objects), tidak perlu diubah ke dict karena 
    # field `tasks` di AgentState menerima `List[Task]`
    # print(f"Tasks: {result.tasks}")
    return {
        "tasks": result.tasks 
        # Saya hapus "calendar_context" karena tidak ada di schema AgentState.
        # Kalau kamu butuh kalender di-passing ke agent 2, tambahkan dulu field 'calendar_data' di Pydantic AgentState.
    }


def check_context_completeness(state: AgentState) -> Literal["ask_clarification", "produce_output"]:
    # Jika sudah mencapai batas maksimal klarifikasi, paksa lanjut ke output
    if state.clarification_round >= MAX_CLARIFICATION_ROUNDS:
        return "produce_output"

    # Cek apakah ada task yang masih kekurangan informasi penting
    # Di sini kita anggap 'duration_minutes' dan 'scheduled_time' sebagai mandatory
    incomplete_tasks = [
        t for t in state.tasks 
        if t.duration_minutes is None or (t.scheduled_time is None and t.deadline is None)
    ]

    if incomplete_tasks:
        return "ask_clarification"
    
    return "produce_output"

CLARIFICATION_PROMPT = """You are a supportive productivity buddy. 
Your job is to write a warm, empathetic message to the user asking for missing details.

Tasks with missing info:
{missing_info}

User's Emotional Context: {emotions}

Guidelines:
1. Match the tone: If they are stressed, be gentle. If they are excited, be energetic.
2. Be concise: Don't ask too many things at once.
3. Reference their specific tasks by name.
"""

def generate_clarification_questions(state: AgentState):
    # Filter task yang butuh detail
    incomplete_tasks = [t for t in state.tasks if t.duration_minutes is None]
    
    # Kumpulkan emosi dari semua task untuk tone matching
    emotions = [t.emotional_context for t in state.tasks if t.emotional_context]
    
    # Panggil LLM (Gunakan prompt yang lebih bebas/creative)
    formatted_missing = "\n".join([f"- {t.name} (missing duration/time)" for t in incomplete_tasks])
    
    response = llm.invoke(CLARIFICATION_PROMPT.format(
        missing_info=formatted_missing,
        emotions=", ".join(emotions) if emotions else "Neutral"
    ))

    # LangChain message content can be either plain string or a list of content blocks.
    raw_content = response.content
    if isinstance(raw_content, str):
        question_text = raw_content
    else:
        content_parts: List[str] = []
        for item in raw_content:
            if isinstance(item, str):
                content_parts.append(item)
            elif isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str):
                    content_parts.append(text_value)
        question_text = "\n".join(part for part in content_parts if part).strip()

    if not question_text:
        question_text = "Boleh bantu isi estimasi durasi untuk task ini?"

    # Buat objek ClarificationQuestion (untuk tracking internal)
    questions = [
        ClarificationQuestion(
            task_id=t.id, 
            missing_field="duration_minutes", 
            question_text=question_text
        ) for t in incomplete_tasks
    ]
    
    return {
        "pending_questions": questions,
        "clarification_round": state.clarification_round + 1
    }

def ask_user(state: AgentState):
    # Node ini biasanya kosong atau hanya log, karena transisi ke user 
    # ditangani oleh orchestrator/frontend.
    print(f"--- WAITING FOR USER (Round {state.clarification_round}) ---")
    return {}


def produce_structured_output(state: AgentState):
    final_data = {
        "user_id": "raka_fadillah",
        "processed_at": TODAY,
        "tasks": [t.model_dump() for t in state.tasks], # Gunakan model_dump() di Pydantic V2
        "summary": f"Successfully processed {len(state.tasks)} tasks."
    }
    
    # Update field structured_output di state
    return {"structured_output": final_data}


def build_agent1_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("interpreter", mind_dump_interpreter)
    workflow.add_node("generator", generate_clarification_questions)
    workflow.add_node("finalizer", produce_structured_output)

    workflow.set_entry_point("interpreter")

    # Flow: Interpreter -> Router -> Generator atau Finalizer
    workflow.add_conditional_edges(
        "interpreter",
        check_context_completeness,
        {
            "ask_clarification": "generator",
            "produce_output": "finalizer"
        }
    )

    # Setelah generator, kita END untuk menunggu input user (Human-in-the-loop)
    workflow.add_edge("generator", END)
    workflow.add_edge("finalizer", END)

    return workflow

serde = JsonPlusSerializer(
    allowed_msgpack_modules=[
        (__name__, "Task"),
        (__name__, "ClarificationQuestion"),
        (__name__, "AgentState"),
    ]
)

checkpointer = MemorySaver(serde=serde)
agent1_app = build_agent1_graph().compile(checkpointer=checkpointer)

def start_agent1(raw_input: str, thread_id: str = "default") -> dict:
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
    
    # Input awal user
    initial_input = {"mind_dump": raw_input, "clarification_round": 0}
    
    # Jalankan graph
    result = agent1_app.invoke(initial_input, config)
    
    # Ambil state terbaru setelah invoke (lebih andal daripada result delta)
    snapshot_values = agent1_app.get_state(config).values
    
    # Jika node selanjutnya adalah END tapi pending_questions tidak kosong,
    # berarti kita baru saja melewati 'generator'.
    pending_questions = snapshot_values.get("pending_questions", [])
    if pending_questions:
        # Ambil pertanyaan terakhir dari list
        last_question = pending_questions[-1].question_text
        return {
            "done": False,
            "question": last_question,
            "output": None,
            "state": snapshot_values
        }

    return {
        "done": True,
        "question": None,
        "output": snapshot_values.get("structured_output"),
        "state": snapshot_values
    }

def resume_agent1(user_answer: str, thread_id: str = "default") -> dict:
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
    
    # 1. Ambil state lama untuk mencatat history
    old_state = agent1_app.get_state(config).values
    
    # 2. Update history agar AI Agent 1 tahu apa yang dibahas sebelumnya
    updated_history = old_state.get("clarification_history", [])
    updated_history.append({"role": "user", "content": user_answer})
    
    # 3. Jalankan kembali dengan input baru dari user
    # Kita overwrite 'mind_dump' dengan jawaban baru agar interpreter fokus ke info tambahan
    result = agent1_app.invoke(
        {
            "mind_dump": user_answer, 
            "clarification_history": updated_history,
            "pending_questions": [] # Kosongkan karena sedang dijawab
        }, 
        config
    )

    snapshot_values = agent1_app.get_state(config).values
    pending_questions = snapshot_values.get("pending_questions", [])

    if pending_questions:
        return {
            "done": False,
            "question": pending_questions[-1].question_text,
            "output": None,
            "state": snapshot_values
        }

    return {
        "done": True,
        "question": None,
        "output": snapshot_values.get("structured_output"),
        "state": snapshot_values
    }

def run_test_scenario():
    # 1. Inisialisasi thread_id unik untuk simulasi user Raka
    session_id = str(uuid.uuid4())
    print(f"=== Starting Test Session: {session_id} ===\n")

    # --- TAHAP 1: Input Awal (Mind Dump) ---
    # Kita berikan input yang ambigu: Ada tugas tapi tidak tahu durasinya.
    raw_input = "Raka di sini. Gue males banget nih, tapi besok ada tugas kumpul progres TeamQuest jam 10 pagi."
    
    print(f"[User]: {raw_input}")
    response = start_agent1(raw_input, thread_id=session_id)

    if not response["done"]:
        print(f"\n[AI Agent 1]: {response['question']}")
        
        # --- TAHAP 2: User Menjawab (Resume) ---
        # User memberikan informasi tambahan yang diminta.
        user_answer = "Paling sekitar 2 jam lah, soalnya cuma revisi database dikit."
        print(f"\n[User]: {user_answer}")
        
        final_response = resume_agent1(user_answer, thread_id=session_id)
        
        if final_response["done"]:
            print("\n=== FINAL STRUCTURED OUTPUT (Ready for Agent 2) ===")
            import json
            print(json.dumps(final_response["output"], indent=2))
        else:
            print(f"\n[AI Agent 1]: {final_response['question']} (Still clarifying...)")

if __name__ == "__main__":
    # graph = build_agent1_graph().compile()

    # # Print Mermaid diagram (text)
    # print(graph.get_graph().draw_mermaid())
    run_test_scenario()