from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas import StateResponse
from app.dependencies import get_graph
from app.graph.agents.helpers import (
    get_api_payload,
    get_api_status,
    get_counselor_done,
    get_counselor_response,
    get_current_intent,
    get_error_message,
    get_final_message,
    get_proposed_schedule,
    get_raw_tasks,
    get_task_breakdown,
)

router = APIRouter(prefix="/state", tags=["state"])


@router.get("/{thread_id}", response_model=StateResponse)
async def get_thread_state(thread_id: str, graph=Depends(get_graph)):
    """
    Dipakai NestJS untuk poll status thread — apakah sedang tunggu HITL atau tidak.
    Berguna juga untuk restore state UI kalau user refresh halaman.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)

    if not state.values:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} tidak ditemukan")

    hitl_payload = None
    if state.next and state.tasks:
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                hitl_payload = task.interrupts[0].value
                break

    return StateResponse(
        thread_id=thread_id,
        pending_hitl=bool(state.next),
        next_node=list(state.next),
        current_intent=get_current_intent(state),
        raw_tasks=get_raw_tasks(state),
        counselor_response=get_counselor_response(state),
        counselor_done=get_counselor_done(state),
        task_breakdown=get_task_breakdown(state),
        proposed_schedule=get_proposed_schedule(state),
        api_status=get_api_status(state),
        api_payload=get_api_payload(state),
        final_message=get_final_message(state),
        error_message=get_error_message(state),
        hitl_payload=hitl_payload,
    )
