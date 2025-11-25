"""
Graph builder and configuration
Construct and compile LangGraph workflow
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
    Create and compile the LangGraph workflow

    Returns:
        Compiled LangGraph workflow

    Graph structure:
        1. Parse & Validate (merged - ONE API call)
        2. Geocode Locations
        3. Disambiguate Results
        4. Fetch Boundaries
        5. Suggest Buffers
        6. (Decision: needs user input? -> pause or continue)
        7. [After user input] Generate Buffers
        8. Validate Results
        9. Merge Geometries
    """
    workflow = StateGraph(PolygonGeneratorState)

    # Merged node: parse_and_validate (replaces validate_intent + parse_query)
    workflow.add_node("parse_and_validate", parse_and_validate_node)
    workflow.add_node("geocode_locations", geocode_locations_node)
    workflow.add_node("disambiguate", disambiguate_node)
    workflow.add_node("fetch_boundaries", fetch_boundaries_node)
    workflow.add_node("suggest_buffers", suggest_buffers_node)
    workflow.add_node("validate_results", validate_results_node)
    workflow.add_node("merge_geometries", merge_geometries_node)

    workflow.set_entry_point("parse_and_validate")

    # Conditional: After parsing and validation
    workflow.add_conditional_edges(
        "parse_and_validate",
        should_continue_after_intent,
        {"geocode_locations": "geocode_locations", "end": END},
    )
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
