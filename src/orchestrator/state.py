"""
State definition for polygon generation workflow
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class PolygonGeneratorState(BaseModel):
    """
    State for polygon generation workflow (Pydantic BaseModel)
    """

    user_query: str
    is_polygon_request: bool = False
    clarification_needed: Optional[str] = None
    locations: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    language: str = "unknown"
    geocoding_results: dict[str, Any] = Field(default_factory=dict)
    selected_locations: dict[str, Any] = Field(default_factory=dict)
    locations_with_polygons: list[dict] = Field(default_factory=list)
    locations_with_points: list[dict] = Field(default_factory=list)
    buffer_decisions: dict[str, float] = Field(default_factory=dict)
    needs_user_input: bool = False
    final_geometries: list = Field(default_factory=list)
    final_polygon: Optional[dict] = None
    current_step: str = "start"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


def create_initial_state(user_query: str) -> PolygonGeneratorState:
    """
    Create initial state for workflow

    Args:
        user_query: User's natural language query

    Returns:
        Initial state object with default values
    """
    return PolygonGeneratorState(user_query=user_query)
