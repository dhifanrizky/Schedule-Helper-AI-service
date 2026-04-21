from fastapi import APIRouter, Depends, HTTPException
from app.api.schemas import StateResponse
from app.dependencies import get_graph
from app.graph.agents.helpers import get_task_list

router = APIRouter(prefix="/state", tags=["state"])


@router.get("/{thread_id}", response_model=StateResponse)
async def get_thread_state(thread_id: str, graph=Depends(get_graph)):
    """
    Dipakai NestJS untuk poll status thread — apakah sedang tunggu HITL atau tidak.
    Berguna juga untuk restore state UI kalau user refresh halaman.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)

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
        intent=state.values.get("intent"),
        task_list=get_task_list(state),
        hitl_payload=hitl_payload,
    )