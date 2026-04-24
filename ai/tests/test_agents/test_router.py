import pytest
from langchain_core.messages import HumanMessage

import app.graph.agents.router as router_module


def test_make_router_sets_current_intent(monkeypatch):
    intent_map = {
        "stress": ["stres"],
        "manage_task": ["tugas"],
        "schedule": ["jadwalkan"],
    }

    def fake_classify(text, received_intent_map):
        assert text == "tolong bantu atur tugas saya"
        assert received_intent_map is intent_map
        return "manage_task"

    monkeypatch.setattr(router_module, "_classify", fake_classify)

    run = router_module.make_router(intent_map, llm=None)
    result = run({"user_input": "tolong bantu atur tugas saya"})

    assert result == {"current_intent": "manage_task"}


def test_make_router_reads_from_messages_when_user_input_missing(monkeypatch):
    intent_map = {"stress": ["stres"]}

    def fake_classify(text, _):
        assert text == "aku lagi stres"
        return "stress"

    monkeypatch.setattr(router_module, "_classify", fake_classify)

    run = router_module.make_router(intent_map, llm=None)
    state = {"messages": [HumanMessage(content="aku lagi stres")]}

    result = run(state) # type: ignore

    assert result["current_intent"] == "stress"


def test_classify_currently_not_implemented():
    with pytest.raises(NotImplementedError):
        router_module._classify("anything", {"stress": ["stres"]})