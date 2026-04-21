from fastapi import FastAPI
from langgraph.checkpoint.redis import RedisSaver
from langchain_core.messages import HumanMessage
import uuid

app = FastAPI()
checkpointer = RedisSaver.from_conn_string("redis://localhost:6379")
graph = create_app(llm, calendar_client, checkpointer=checkpointer)

INTENT_MAP = {
    "stress":      ["stres", "overwhelmed", "pusing"],
    "overload":    ["banyak banget", "kewalahan", "numpuk"],
    "manage_task": ["tugas", "deadline", "prioritas"],
    "schedule":    ["jadwalkan", "kalender", "reminder"],
}

def create_app(llm, calendar_client):
    agents = {
        "router":      make_router(INTENT_MAP),
        "counselor":   make_counselor(llm),
        "prioritizer": make_prioritizer(llm),
        "scheduler":   make_scheduler(llm, calendar_client),
    }
    return build_graph(agents)

@app.post("/chat")
async def chat(body: ChatRequest):
    thread_id = body.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=body.message)], ...},
        config=config,
    )
    return {"thread_id": thread_id, "status": result.get("hitl_status")}


@app.post("/resume/{thread_id}")
async def resume(thread_id: str, body: HITLResponse):
    """NestJS hit endpoint ini setelah user approve/edit di frontend."""
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"hitl_input": body.approved_data},
        config=config,
    )
    return {"status": "resumed", "result": result}


@app.get("/state/{thread_id}")
async def get_state(thread_id: str):
    """NestJS poll ini untuk tahu apakah graph sedang nunggu HITL."""
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    return {
        "thread_id": thread_id,
        "pending_hitl": bool(state.next),  # next ada isinya = graph sedang interrupt
        "next_node": list(state.next),
        "task_list": state.values.get("task_list"),
    }