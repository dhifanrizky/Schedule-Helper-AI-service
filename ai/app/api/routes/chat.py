import uuid
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from app.api.schemas import ChatRequest, ChatResponse
from app.dependencies import get_graph

router = APIRouter(prefix="/chat", tags=["chat"])


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
        await graph.ainvoke(
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    state = graph.get_state(config)
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
