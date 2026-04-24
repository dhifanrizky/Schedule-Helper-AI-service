from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from app.graph.agents.helpers import last_message
from app.graph.state import AppState
from app.graph.types import RawTask

# ---------------------------------------------------------------------------
# Isi INTENT_MAP dan logic _classify() sesuai kebutuhanmu.
# Tambah intent baru = tambah key baru di INTENT_MAP, tidak perlu ubah lain.
# ---------------------------------------------------------------------------

type IntentMap = dict[str, list[str]]


class RouterOutputSchema(BaseModel):
    current_intent: str | None = Field(
        default=None,
        description="Overall user intent.",
    )
    raw_tasks: list[RawTask] = Field(
        default_factory=list,
        description="Raw tasks extracted from the user's message. Merge related phrases into a single task.",
    )

SYSTEM_PROMPT = """

You are the Router Agent for a schedule management system.
Your job is to identify the user's intent and extract the raw tasks they mention.

HARD RULES FOR EXTRACTION:
1. "current_intent" MUST be exactly one of: ["stress", "overload", "manage_task", "schedule", null].
2. "category" MUST be exactly one of: ["serius", "santai", "biasa", "lainnya", null].
3. "task_id" MUST be sequential starting from "task_001".
4. "raw_input" MUST be the exact words used by the user.
5. "raw_time" MUST be filled with the time phrase if mentioned, otherwise null.
6. MATCH THE LANGUAGE: You MUST write the "title", "description", and "raw_time" using the exact same language and tone as the user's input (e.g., if the user uses informal Indonesian slang, write the output in informal Indonesian).
7. NO DUPLICATES: If the user describes a single task, feeling, or situation using multiple phrases in one sentence, extract it as ONLY ONE task. DO NOT split a single thought into multiple array items.

DESCRIPTION RULE (CRITICAL):
For the "description" field, do not just summarize the task. You must explicitly describe:
- What the user feels about the task (e.g., panicked, relaxed).
- What details are missing or unknown (e.g., unknown deadline, unknown topic).

Example:
User: "aku mau belajar buat ujian besok, terus aku juga ada tugas project yang harus dikelarin tapi masih lama sih"

Extraction logic for description:
- Task 1 (Ujian): User says it's tomorrow, but doesn't specify which subject. Description should highlight the missing subject and immediate urgency in Indonesian (e.g., "Mau ujian besok tapi belum jelas mata kuliah apa yang harus dipelajari").
- Task 2 (Project): User says it's still far away. Description should highlight that the deadline and project details are still vague in Indonesian (e.g., "Ada tugas project tapi tidak tahu spesifiknya apa dan deadlinenya kapan selain masih lama").

"""


def make_router(intent_map: IntentMap, llm: BaseChatModel):
    """
    Factory untuk RouterAgent.
    Tugas: klasifikasi intent dari pesan user -> update state["current_intent"].
    """

    structured_output = llm.with_structured_output(RouterOutputSchema)

    def run(state: AppState) -> dict:
        text = last_message(state)
        output = _classify(text, intent_map, structured_output)
        return output 

    return run


def _classify(
    text: str,
    intent_map: IntentMap,
    structured_output: Runnable,
) -> dict:
    """
    Klasifikasi intent + ekstrak raw tasks via structured LLM output.
    Intent divalidasi terhadap intent_map. Jika tidak valid/ambigu, pakai None.
    """
    result = structured_output.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
    )

    if hasattr(result, "model_dump"):
        result = result.model_dump()

    if not isinstance(result, dict):
        return {"current_intent": None, "raw_tasks": []}

    raw_intent = result.get("current_intent")
    valid_intents = set(intent_map.keys())
    intent = raw_intent if raw_intent in valid_intents else None

    raw_tasks = result.get("raw_tasks")
    if not isinstance(raw_tasks, list):
        raw_tasks = []

    normalized_tasks: list[dict] = []
    for task in raw_tasks:
        if hasattr(task, "model_dump"):
            normalized_tasks.append(task.model_dump())
        elif isinstance(task, dict):
            normalized_tasks.append(task)


    return {
        "current_intent": intent,
        "raw_tasks": normalized_tasks,
    }
