from langgraph.graph import StateGraph, END
from app.graph.routing import route_by_intent, route_after_counselor, route_after_prioritizer
from app.graph.state import AppState
from app.graph.agents.protocol import Agent


def build_graph(agents: dict[str, Agent], checkpointer):
    graph = StateGraph(AppState)

    for name, agent in agents.items():
        graph.add_node(name, agent)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_by_intent)
    graph.add_conditional_edges("counselor", route_after_counselor)
    graph.add_conditional_edges("prioritizer", route_after_prioritizer)
    graph.add_edge("scheduler", END)

    return graph.compile(checkpointer=checkpointer)