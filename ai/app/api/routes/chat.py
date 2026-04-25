import json
import traceback
import uuid
from collections.abc import AsyncIterator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.api.schemas import ChatRequest, ChatResponse
from app.dependencies import get_graph

router = APIRouter(prefix="/chat", tags=["chat"])


async def _print_step_state(graph, config: dict, thread_id: str, step_update: dict) -> None:
    state = await graph.aget_state(config)
    node = next(iter(step_update.keys()), "unknown") if isinstance(step_update, dict) else "unknown"
    print(
        f"[graph-step][chat][thread_id={thread_id}] "
        f"node={node} next={list(state.next)} values={state.values}"
    )


def _chat_input(body: ChatRequest, thread_id: str) -> dict:
    return {
        "messages": [HumanMessage(content=body.message)],
        "user_input": body.message,
        "current_intent": None,
        "raw_tasks": [],
        "counselor_response": [],
        "counselor_done": False,
        "task_breakdown": [],
        "proposed_schedule": [],
        "api_status": None,
        "api_payload": None,
        "final_message": None,
        "error_message": None,
        "metadata": {"user_id": body.user_id},
        "hitl_status": None,
        "hitl_input": None,
    }


def _format_sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _chunk_to_text(chunk) -> str:
    if hasattr(chunk, "content"):
        content = chunk.content
    else:
        content = chunk

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            item if isinstance(item, str) else str(item)
            for item in content
        )
    if content is None:
        return ""
    return str(content)


def _extract_node_name(payload: dict) -> str | None:
    if not isinstance(payload, dict):
        return None

    for key in ("langgraph_node", "node", "name", "source"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    return None


def _normalize_update_payload(update: dict) -> dict:
    if not isinstance(update, dict):
        return {"raw": update}

    if len(update) == 1:
        node_name, node_update = next(iter(update.items()))
        return {"node": node_name, "update": node_update}

    return update


async def _stream_chat_events(graph, config: dict, thread_id: str, body: ChatRequest) -> AsyncIterator[str]:
    try:
        async for stream_item in graph.astream(
            _chat_input(body, thread_id),
            config=config,
            stream_mode=["messages", "updates"],
        ):
            if not isinstance(stream_item, tuple) or len(stream_item) < 2:
                continue

            mode = stream_item[0]
            payload = stream_item[1]

            if mode == "messages":
                if isinstance(payload, tuple) and len(payload) == 2:
                    chunk, metadata = payload
                else:
                    chunk, metadata = payload, {}

                text = _chunk_to_text(chunk)
                if text:
                    yield _format_sse(
                        "message",
                        {
                            "thread_id": thread_id,
                            "text": text,
                            "node": _extract_node_name(metadata),
                        },
                    )
                continue

            if mode == "updates":
                await _print_step_state(graph, config, thread_id, payload)
                yield _format_sse(
                    "agent_step",
                    {
                        "thread_id": thread_id,
                        "update": _normalize_update_payload(payload),
                    },
                )

    except Exception as exc:
        traceback.print_exc()
        yield _format_sse(
            "error",
            {
                "thread_id": thread_id,
                "message": str(exc),
            },
        )
        return

    state = await graph.aget_state(config)
    is_waiting = bool(state.next)
    hitl_payload = None

    if is_waiting and state.tasks:
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                hitl_payload = task.interrupts[0].value
                break

    yield _format_sse(
        "execution_complete",
        {
            "thread_id": thread_id,
            "status": "waiting_hitl" if is_waiting else "done",
            "next_node": list(state.next),
            "hitl_payload": hitl_payload,
        },
    )


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, graph=Depends(get_graph)):
    """
    Entry point percakapan baru atau lanjutan.

    Kalau thread_id tidak dikirim → buat thread baru.
    Kalau thread_id dikirim → lanjut thread yang sudah ada.

    Response:
    - status "waiting_hitl" → frontend harus tampilkan hitl_payload ke user
    - status "done" → percakapan selesai
    """
    thread_id = body.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        async for step_update in graph.astream(
            {
                "messages": [HumanMessage(content=body.message)],
                "user_input": body.message,
                "current_intent": None,
                "raw_tasks": [],
                "counselor_response": [],
                "counselor_done": False,
                "task_breakdown": [],
                "proposed_schedule": [],
                "api_status": None,
                "api_payload": None,
                "final_message": None,
                "error_message": None,
                "metadata": {"user_id": body.user_id},
                "hitl_status": None,
                "hitl_input": None,
            },
            config=config,
            stream_mode="updates",
        ):
            await _print_step_state(graph, config, thread_id, step_update)
    
    except Exception as e:
        traceback.print_exc()  # ⬅️ ini penting
        raise HTTPException(status_code=500, detail=str(e))
    state = await graph.aget_state(config)
    is_waiting = bool(state.next)

    # kalau graph interrupt, ambil payload dari tasks interrupt
    hitl_payload = None
    if is_waiting and state.tasks:
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                hitl_payload = task.interrupts[0].value
                break

    return ChatResponse(
        thread_id=thread_id,
        status="waiting_hitl" if is_waiting else "done",
        next_node=list(state.next),
        hitl_payload=hitl_payload,
    )


@router.post("/stream")
async def chat_stream(body: ChatRequest, graph=Depends(get_graph)):
    thread_id = body.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    return StreamingResponse(
        _stream_chat_events(graph, config, thread_id, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
