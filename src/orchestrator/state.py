"""
State definition for polygon generation workflow
"""

from typing import TypedDict, Annotated
import operator


class PolygonGeneratorState(TypedDict):
    """
    State for polygon generation workflow
    """

    user_query: str
    is_polygon_request: bool
    clarification_needed: str | None
    locations: list[str]
    context: dict
    language: str
    geocoding_results: dict
    selected_locations: dict
    locations_with_polygons: list[dict]
    locations_with_points: list[dict]
    buffer_decisions: dict
    needs_user_input: bool
    final_geometries: list
    final_polygon: dict | None
    current_step: str
    errors: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]


def create_initial_state(user_query: str) -> PolygonGeneratorState:
    """
    Create initial state for workflow

    Args:
        user_query: User's natural language query

    Returns:
        Initial state dict with default values
    """
    return {
        "user_query": user_query,
        "is_polygon_request": False,
        "clarification_needed": None,
        "locations": [],
        "context": {},
        "language": "unknown",
        "geocoding_results": {},
        "selected_locations": {},
        "locations_with_polygons": [],
        "locations_with_points": [],
        "buffer_decisions": {},
        "needs_user_input": False,
        "final_geometries": [],
        "final_polygon": None,
        "current_step": "start",
        "errors": [],
        "warnings": [],
    }
