"""
Graph builder and configuration
Construct and compile LangGraph workflow

LangGraph 1.0: Native async support, no path_map needed
"""

from langgraph.graph import StateGraph, END

from src.orchestrator.state import PolygonGeneratorState
from src.orchestrator.nodes import (
    parse_and_validate_node,
    geocode_locations_node,
    disambiguate_node,
    fetch_boundaries_node,
    suggest_buffers_node,
    validate_results_node,
    merge_geometries_node,
)
from src.orchestrator.routing import should_continue_after_intent, should_ask_user


def create_polygon_graph():
    """
    Create and compile the LangGraph workflow (ASYNC)

    Returns:
        Compiled LangGraph workflow

    Graph structure:
        1. Parse & Validate (merged - ONE API call) [ASYNC]
        2. Geocode Locations [ASYNC]
        3. Disambiguate Results [ASYNC]
        4. Fetch Boundaries [SYNC]
        5. Suggest Buffers [ASYNC]
        6. (Decision: needs user input? -> pause or continue)
        7. [After user input] Generate Buffers [SYNC]
        8. Validate Results [ASYNC]
        9. Merge Geometries [SYNC]
    """
    workflow = StateGraph(PolygonGeneratorState)

    workflow.add_node("parse_and_validate", parse_and_validate_node)
    workflow.add_node("geocode_locations", geocode_locations_node)
    workflow.add_node("disambiguate", disambiguate_node)
    workflow.add_node("fetch_boundaries", fetch_boundaries_node)
    workflow.add_node("suggest_buffers", suggest_buffers_node)
    workflow.add_node("validate_results", validate_results_node)
    workflow.add_node("merge_geometries", merge_geometries_node)

    workflow.set_entry_point("parse_and_validate")

    workflow.add_conditional_edges(
        "parse_and_validate",
        should_continue_after_intent,
    )
    workflow.add_edge("geocode_locations", "disambiguate")
    workflow.add_edge("disambiguate", "fetch_boundaries")
    workflow.add_edge("fetch_boundaries", "suggest_buffers")

    workflow.add_conditional_edges(
        "suggest_buffers",
        should_ask_user,
    )

    workflow.add_edge("validate_results", "merge_geometries")
    workflow.add_edge("merge_geometries", END)

    return workflow.compile()


_graph_instance = None


def get_graph():
    """
    Get or create the compiled graph (singleton pattern)

    Returns:
        Compiled LangGraph workflow
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_polygon_graph()
    return _graph_instance
