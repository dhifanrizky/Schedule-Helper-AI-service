import json
import traceback
from collections.abc import AsyncIterator
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from app.api.schemas import HITLResumeRequest, ResumeResponse
from app.dependencies import get_graph
from langgraph.types import Command

router = APIRouter(prefix="/resume", tags=["hitl"])


async def _print_step_state(graph, config: dict, thread_id: str, step_update: dict) -> None:
    state = await graph.aget_state(config)
    node = next(iter(step_update.keys()), "unknown") if isinstance(step_update, dict) else "unknown"
    print(
        f"[graph-step][resume][thread_id={thread_id}] "
        f"node={node} next={list(state.next)} values={state.values}"
    )


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


def _inject_authorization(approved_data: dict, authorization: str | None) -> dict:
    if not authorization:
        return approved_data
    for key in ("authorization", "auth_token", "access_token"):
        if approved_data.get(key):
            return approved_data
    return {**approved_data, "authorization": authorization}


async def _stream_resume_events(
    graph,
    config: dict,
    thread_id: str,
    approved_data: dict,
) -> AsyncIterator[str]:
    """Stream resume events as SSE."""
    print(f"[resume-stream][start][thread_id={thread_id}]")
    try:
        async for stream_item in graph.astream(
            Command(resume=approved_data),
            config=config,
            stream_mode=["messages", "updates"],
        ):
            print(
                f"[resume-stream][item][thread_id={thread_id}] "
                f"type={type(stream_item).__name__} value={stream_item}"
            )
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
                    print(
                        f"[resume-stream][message][thread_id={thread_id}] "
                        f"node={_extract_node_name(metadata)} text={text}"
                    )
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

    new_state = await graph.aget_state(config)
    is_waiting = bool(new_state.next)
    hitl_payload = None

    if is_waiting and new_state.tasks:
        for task in new_state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                hitl_payload = task.interrupts[0].value
                break

    yield _format_sse(
        "execution_complete",
        {
            "thread_id": thread_id,
            "status": "waiting_hitl" if is_waiting else "done",
            "next_node": list(new_state.next),
            "hitl_payload": hitl_payload,
        },
    )


@router.post("/{thread_id}", response_model=ResumeResponse)
async def resume(
    thread_id: str,
    body: HITLResumeRequest,
    graph=Depends(get_graph),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """
    Dipanggil NestJS setelah user approve/edit data di frontend.

    Flow:
    1. Update state dengan approved_data dari user
    2. Lanjut eksekusi graph dari titik interrupt
    3. Kalau masih ada interrupt lagi → return waiting_hitl
    4. Kalau sudah selesai → return done
    """
    config = {"configurable": {"thread_id": thread_id}}

    # cek apakah thread ada dan memang sedang interrupt
    state = await graph.aget_state(config)
    if not state.values:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} tidak ditemukan")
    if not state.next:
        raise HTTPException(status_code=400, detail="Thread ini tidak sedang menunggu HITL")

    approved_data = _inject_authorization(body.approved_data, authorization)

    try:
        # inject approved_data sebagai Command untuk resume interrupt
        async for step_update in graph.astream(
            Command(resume=approved_data),
            config=config,
            stream_mode="updates",
        ):
            await _print_step_state(graph, config, thread_id, step_update)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_state = await graph.aget_state(config)
    is_waiting = bool(new_state.next)

    hitl_payload = None
    if is_waiting and new_state.tasks:
        for task in new_state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                hitl_payload = task.interrupts[0].value
                break

    return ResumeResponse(
        thread_id=thread_id,
        status="waiting_hitl" if is_waiting else "done",
        next_node=list(new_state.next),
        hitl_payload=hitl_payload,
    )


@router.post("/{thread_id}/stream")
async def resume_stream(
    thread_id: str,
    body: HITLResumeRequest,
    graph=Depends(get_graph),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """
    Stream resume events as Server-Sent Events (SSE).
    Same as POST /{thread_id} but with real-time streaming updates.
    """
    config = {"configurable": {"thread_id": thread_id}}

    # cek apakah thread ada dan memang sedang interrupt
    state = await graph.aget_state(config)
    if not state.values:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} tidak ditemukan")
    if not state.next:
        raise HTTPException(status_code=400, detail="Thread ini tidak sedang menunggu HITL")

    approved_data = _inject_authorization(body.approved_data, authorization)

    return StreamingResponse(
        _stream_resume_events(graph, config, thread_id, approved_data),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )