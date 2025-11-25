"""
Routing logic for conditional edges
Make routing decisions
"""

from typing import Literal
from src.orchestrator.state import PolygonGeneratorState


def should_continue_after_intent(
    state: PolygonGeneratorState,
) -> Literal["geocode_locations", "end"]:
    """
    Route after parse and validate

    Args:
        state: Current workflow state

    Returns:
        Next node name or "end"
    """
    if state.get("is_polygon_request", False):
        return "geocode_locations"
    else:
        return "end"


def should_ask_user(
    state: PolygonGeneratorState,
) -> Literal["pause_for_user", "validate_results"]:
    """
    Route after fetching boundaries
    Check if we need user input for buffer radii

    Args:
        state: Current workflow state

    Returns:
        "pause_for_user" if user input needed, else "validate_results"
    """
    if state.get("needs_user_input", False):
        return "pause_for_user"
    else:
        return "validate_results"
