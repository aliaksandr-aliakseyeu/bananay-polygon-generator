"""
Graph builder and configuration
Construct and compile LangGraph workflow
"""

from langgraph.graph import StateGraph, END

from src.orchestrator.state import PolygonGeneratorState
from src.orchestrator.nodes import (
    validate_intent_node,
    parse_query_node,
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
    Create and compile the LangGraph workflow

    Returns:
        Compiled LangGraph workflow

    Graph structure:
        1. Validate Intent -> (continue or end)
        2. Parse Query
        3. Geocode Locations
        4. Disambiguate Results
        5. Fetch Boundaries
        6. Suggest Buffers
        7. (Decision: needs user input? -> pause or continue)
        8. [After user input] Generate Buffers
        9. Validate Results
        10. Merge Geometries
    """
    workflow = StateGraph(PolygonGeneratorState)

    workflow.add_node("validate_intent", validate_intent_node)
    workflow.add_node("parse_query", parse_query_node)
    workflow.add_node("geocode_locations", geocode_locations_node)
    workflow.add_node("disambiguate", disambiguate_node)
    workflow.add_node("fetch_boundaries", fetch_boundaries_node)
    workflow.add_node("suggest_buffers", suggest_buffers_node)
    workflow.add_node("validate_results", validate_results_node)
    workflow.add_node("merge_geometries", merge_geometries_node)

    workflow.set_entry_point("validate_intent")

    workflow.add_conditional_edges(
        "validate_intent",
        should_continue_after_intent,
        {"parse_query": "parse_query", "end": END},
    )

    workflow.add_edge("parse_query", "geocode_locations")
    workflow.add_edge("geocode_locations", "disambiguate")
    workflow.add_edge("disambiguate", "fetch_boundaries")
    workflow.add_edge("fetch_boundaries", "suggest_buffers")

    workflow.add_conditional_edges(
        "suggest_buffers",
        should_ask_user,
        {
            "pause_for_user": END,
            "validate_results": "validate_results",
        },
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
