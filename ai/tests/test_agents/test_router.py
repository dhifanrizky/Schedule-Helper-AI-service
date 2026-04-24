from langchain_core.messages import HumanMessage

import app.graph.agents.router as router_module


class DummyStructuredOutput:
    def __init__(self, result):
        self._result = result

    def invoke(self, _messages):
        return self._result


class DummyLLM:
    def __init__(self, result):
        self._result = result

    def with_structured_output(self, _schema):
        return DummyStructuredOutput(self._result)


def test_make_router_sets_current_intent():
    intent_map = {
        "stress": ["stres"],
        "manage_task": ["tugas"],
        "schedule": ["jadwalkan"],
    }
    llm = DummyLLM(
        {
            "current_intent": "manage_task",
            "raw_tasks": [
                {
                    "task_id": "task_001",
                    "title": "Atur tugas",
                    "description": "Perlu mengatur tugas kuliah.",
                    "raw_time": None,
                    "raw_input": "tolong bantu atur tugas saya",
                    "category": "tugas",
                }
            ],
        }
    )

    run = router_module.make_router(intent_map, llm=llm)  # type: ignore
    result = run({"user_input": "tolong bantu atur tugas saya"})  # type: ignore

    assert result["current_intent"] == "manage_task"
    assert len(result["raw_tasks"]) == 1


def test_make_router_reads_from_messages_when_user_input_missing():
    intent_map = {"stress": ["stres"]}
    llm = DummyLLM(
        {
            "current_intent": "stress",
            "raw_tasks": [],
        }
    )

    run = router_module.make_router(intent_map, llm=llm)  # type: ignore
    state = {"messages": [HumanMessage(content="aku lagi stres")]}

    result = run(state)  # type: ignore

    assert result["current_intent"] == "stress"


def test_classify_invalid_intent_falls_back_to_none():
    structured = DummyStructuredOutput(
        {
            "current_intent": "unsupported_intent",
            "raw_tasks": [],
        }
    )

    result = router_module._classify(
        "anything",
        {"stress": ["stres"]},
        structured,  # type: ignore
    )

    assert result["current_intent"] is None
