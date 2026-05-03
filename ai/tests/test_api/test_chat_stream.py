import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.routes import chat as chat_route
from app.dependencies import get_graph


class _FakeChunk:
    def __init__(self, content: str):
        self.content = content


class _FakeInterrupt:
    def __init__(self, value):
        self.value = value


class _FakeTask:
    def __init__(self, interrupt_value):
        self.interrupts = [_FakeInterrupt(interrupt_value)]


class _FakeState:
    def __init__(self):
        self.next = []
        self.tasks = []
        self.values = {"final_message": "done"}


class _FakeGraph:
    def __init__(self):
        self.last_stream_mode = None

    async def astream(self, _input, *, config=None, stream_mode=None):
        self.last_stream_mode = stream_mode
        yield ("updates", {"router": {"current_intent": "manage_task"}})
        yield ("messages", (_FakeChunk("Halo"), {"langgraph_node": "counselor"}))
        yield ("messages", (_FakeChunk(" dunia"), {"langgraph_node": "counselor"}))
        yield ("updates", {"scheduler": {"final_message": "Selesai"}})

    async def aget_state(self, _config):
        return _FakeState()


@pytest.mark.asyncio
async def test_chat_stream_emits_agent_steps_messages_and_completion():
    fake_graph = _FakeGraph()
    app = FastAPI()
    app.include_router(chat_route.router)

    async def _override_get_graph():
        return fake_graph

    app.dependency_overrides[get_graph] = _override_get_graph

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/chat/stream",
            json={"message": "bantu saya", "user_id": "user-123"},
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            body = await response.aread()

    text = body.decode("utf-8")

    print("\n\n=== RAW SSE OUTPUT ===")
    print(text)
    print("======================\n\n")
    
    assert fake_graph.last_stream_mode == ["messages", "updates"]
    assert "event: agent_step" in text
    assert '"node": "router"' in text
    assert "event: message" in text
    assert '"text": "Halo"' in text
    assert '"text": " dunia"' in text
    assert "event: execution_complete" in text
    assert '"status": "done"' in text
