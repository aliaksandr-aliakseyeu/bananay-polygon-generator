"""
Routing logic for conditional edges
Make routing decisions

LangGraph 1.0: Functions return node names or END directly (no path_map)
"""

from langgraph.graph import END
from src.orchestrator.state import PolygonGeneratorState


def should_continue_after_intent(state: PolygonGeneratorState) -> str:
    """
    Route after parse and validate

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.is_polygon_request:
        return "geocode_locations"
    else:
        return END


def should_ask_user(state: PolygonGeneratorState) -> str:
    """
    Route after fetching boundaries
    Check if we need user input for buffer radii

    Args:
        state: Current workflow state

    Returns:
        END if user input needed, else "validate_results"
    """
    if state.needs_user_input:
        return END
    else:
        return "validate_results"
