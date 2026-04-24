import json
import os

import pytest
from openai import BadRequestError, RateLimitError

from app.dependencies import (
    INTENT_MAP,
    ROUTER_LLM_MODEL,
    ROUTER_LLM_PROVIDER,
    ROUTER_LLM_TEMPERATURE,
)
from app.graph.builder import build_graph
import app.graph.agents.router as router_module
from app.config import settings
from app.services.llm import get_llm


def _noop_agent(_state):
    return {}


def _invoke_with_real_llm(prompt: str, use_graph: bool = False):
    provider = ROUTER_LLM_PROVIDER
    model = ROUTER_LLM_MODEL

    if provider == "openai" and not settings.openai_api_key:
        pytest.skip("Router LLM is configured to openai, but OPENAI_API_KEY is missing.")
    if provider == "groq" and not settings.groq_api_key:
        pytest.skip("Router LLM is configured to groq, but GROQ_API_KEY is missing.")

    llm = get_llm(provider=provider, model=model, temperature=ROUTER_LLM_TEMPERATURE)

    if use_graph:
        runner = build_graph(
            {
                "router": router_module.make_router(INTENT_MAP, llm=llm),
                "counselor": _noop_agent,
                "prioritizer": _noop_agent,
                "scheduler": _noop_agent,
            },  # type: ignore
            checkpointer=None,
        ).invoke
    else:
        runner = router_module.make_router(INTENT_MAP, llm=llm)

    try:
        result = runner({"user_input": prompt})  # type: ignore
        return result, provider, model
    except RateLimitError:
        pytest.skip(f"{provider}:{model}=rate_limit_or_quota")
    except BadRequestError as err:
        if "does not support response format `json_schema`" in str(err):
            pytest.skip(f"{provider}:{model}=json_schema_not_supported")
        raise


@pytest.mark.skipif(
    not (settings.openai_api_key or settings.groq_api_key),
    reason="No LLM API key configured (OPENAI_API_KEY or GROQ_API_KEY).",
)
def test_router_with_real_llm_opt_in():
    if os.getenv("RUN_REAL_LLM_TESTS") != "1":
        pytest.skip("Set RUN_REAL_LLM_TESTS=1 to run real LLM integration test.")

    result, used_provider, used_model = _invoke_with_real_llm(
        "Aku punya tugas project dan deadline mepet minggu ini, bantu atur prioritas ya."
    )

    print("\nLLM router output:")
    print(f"provider={used_provider}, model={used_model}")
    try:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except TypeError:
        print(result)

    assert isinstance(result, dict)
    assert "current_intent" in result
    assert "raw_tasks" in result
    assert result["current_intent"] in {"stress", "overload", "manage_task", "schedule", None}
    assert isinstance(result["raw_tasks"], list)


@pytest.mark.skipif(
    not (settings.openai_api_key or settings.groq_api_key),
    reason="No LLM API key configured (OPENAI_API_KEY or GROQ_API_KEY).",
)
def test_router_saved_in_global_state_opt_in():
    if os.getenv("RUN_REAL_LLM_TESTS") != "1":
        pytest.skip("Set RUN_REAL_LLM_TESTS=1 to run real LLM integration test.")

    final_state, used_provider, used_model = _invoke_with_real_llm(
        "aduh aku ga tau lagi mau ngapain hari ini, tugas masih banyak lagi anjay",
        use_graph=True,
    )

    print("\nGLOBAL STATE AFTER GRAPH INVOICE:")
    print(f"provider={used_provider}, model={used_model}")
    try:
        print(json.dumps(final_state, indent=2, ensure_ascii=False))
    except TypeError:
        print(final_state)

    assert isinstance(final_state, dict)
    assert final_state.get("current_intent") in {
        "stress",
        "overload",
        "manage_task",
        "schedule",
        None,
    }
    assert isinstance(final_state.get("raw_tasks"), list)
