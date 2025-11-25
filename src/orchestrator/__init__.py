"""
Polygon Generation Orchestrator
LangGraph-based workflow for natural language to polygon conversion

Public API:
    - process_query: Process initial user query
    - resume_with_buffers: Continue after user provides buffer decisions
    - PolygonGeneratorState: State type definition

Example:
    >>> from src.orchestrator import process_query, resume_with_buffers
    >>>
    >>> # Phase 1: Initial processing
    >>> result = process_query("I want Minsk and Gomel")
    >>>
    >>> if result["needs_user_input"]:
    ...     # Phase 2: Resume with user decisions
    ...     buffer_decisions = {"location": 2.0}
    ...     final = resume_with_buffers(result, buffer_decisions)
    >>> else:
    ...     # Already complete
    ...     final = result
    >>>
    >>> # Use final polygon
    >>> polygon = final["final_polygon"]
"""

# Public API
from src.orchestrator.interface import process_query, resume_with_buffers
from src.orchestrator.state import PolygonGeneratorState

__all__ = [
    "process_query",
    "resume_with_buffers",
    "PolygonGeneratorState",
]

# Version
__version__ = "1.0.0"
