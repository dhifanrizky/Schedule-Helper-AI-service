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
    def unwrap_state(state):
        return state.values if hasattr(state, "values") else state

    s = unwrap_state(state)

    return StateResponse(
        thread_id=thread_id,
        pending_hitl=bool(state.next),
        next_node=list(state.next),
        current_intent=s.get("current_intent"),
        raw_tasks=s.get("raw_tasks"),
        counselor_response=s.get("counselor_response"),
        counselor_done=s.get("counselor_done"),
        task_breakdown=s.get("task_breakdown"),
        proposed_schedule=s.get("proposed_schedule"),
        api_status=s.get("api_status"),
        api_payload=s.get("api_payload"),
        final_message=s.get("final_message"),
        error_message=s.get("error_message"),
        hitl_payload=hitl_payload,
    )
