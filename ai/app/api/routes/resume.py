from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas import HITLResumeRequest, ResumeResponse
from app.dependencies import get_graph

router = APIRouter(prefix="/resume", tags=["hitl"])


async def _print_step_state(graph, config: dict, thread_id: str, step_update: dict) -> None:
    state = await graph.aget_state(config)
    node = next(iter(step_update.keys()), "unknown") if isinstance(step_update, dict) else "unknown"
    print(
        f"[graph-step][resume][thread_id={thread_id}] "
        f"node={node} next={list(state.next)} values={state.values}"
    )


@router.post("/{thread_id}", response_model=ResumeResponse)
async def resume(thread_id: str, body: HITLResumeRequest, graph=Depends(get_graph)):
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

    try:
        # inject approved_data sebagai Command untuk resume interrupt
        from langgraph.types import Command
        async for step_update in graph.astream(
            Command(resume=body.approved_data),
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