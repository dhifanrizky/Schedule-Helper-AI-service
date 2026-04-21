from langgraph.graph import StateGraph, END
from app.graph.routing import route_by_intent
from app.graph.state import AppState
from app.graph.agents.protocol import Agent


def build_graph(agents: dict[str, Agent], checkpointer):
    graph = StateGraph(AppState)

    for name, agent in agents.items():
        graph.add_node(name, agent)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_by_intent)
    graph.add_edge("counselor", "prioritizer")
    graph.add_edge("prioritizer", "scheduler")
    graph.add_edge("scheduler", END)

    return graph.compile(checkpointer=checkpointer, interrupt_before=["counselor", "prioritizer"])