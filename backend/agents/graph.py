from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any, List, Literal

# Import all agents
from . import agent1_preference
from . import agent2_retrieval
from . import agent3_review
from . import agent4_scoring
from . import agent5_ethics
from . import agent6_price_intel
from . import agent7_recommendation
from . import agent8_alternatives
from . import agent9_query_intel
from . import agent10_final

class PipelineState(TypedDict):
    query: str
    extracted_preferences: Dict[str, Any]
    retrieval_strategy: str
    products: List[Dict[str, Any]]
    ethics: Dict[str, Any]
    price_intelligence: Dict[str, Any]
    user_profile: Dict[str, Any]
    alternatives: Dict[str, Any]
    query_intelligence: Dict[str, Any]
    final_report: Dict[str, Any]


def _after_retrieval(state: PipelineState) -> Literal["has_products", "empty_recovery"]:
    """Conditional transition: recover when no rows matched (e.g. DB issue)."""
    prods = state.get("products") or []
    return "has_products" if len(prods) > 0 else "empty_recovery"


def _empty_recovery(state: PipelineState) -> Dict[str, Any]:
    """Broaden search using the same retrieval heuristics as Agent 2."""
    from .agent2_retrieval import recover_for_empty_state

    return recover_for_empty_state(state)


def build_graph():
    graph = StateGraph(PipelineState)
    
    # Node mapping
    graph.add_node("agent_01", agent1_preference.process)
    graph.add_node("agent_02", agent2_retrieval.process)
    graph.add_node("agent_03", agent3_review.process)
    graph.add_node("agent_04", agent4_scoring.process)
    graph.add_node("agent_05", agent5_ethics.process)
    graph.add_node("agent_06", agent6_price_intel.process)
    graph.add_node("agent_07", agent7_recommendation.process)
    graph.add_node("agent_08", agent8_alternatives.process)
    graph.add_node("agent_09", agent9_query_intel.process)
    graph.add_node("agent_10", agent10_final.process)
    graph.add_node("empty_recovery", _empty_recovery)

    graph.add_edge("agent_01", "agent_02")
    graph.add_conditional_edges(
        "agent_02",
        _after_retrieval,
        {"has_products": "agent_03", "empty_recovery": "empty_recovery"},
    )
    graph.add_edge("empty_recovery", "agent_03")
    graph.add_edge("agent_03", "agent_04")
    graph.add_edge("agent_04", "agent_05")
    graph.add_edge("agent_05", "agent_06")
    graph.add_edge("agent_06", "agent_07")
    graph.add_edge("agent_07", "agent_08")
    graph.add_edge("agent_08", "agent_09")
    graph.add_edge("agent_09", "agent_10")
    graph.add_edge("agent_10", END)
    
    graph.set_entry_point("agent_01")
    return graph.compile()
