"""
Public interface for polygon generation workflow
Provide clean API for external use
"""

from src.orchestrator.state import PolygonGeneratorState, create_initial_state
from src.orchestrator.graph import get_graph
from src.orchestrator.nodes.buffers_async import generate_buffers_node
from src.orchestrator.nodes.validation_async import validate_results_node
from src.orchestrator.nodes.merge import merge_geometries_node


async def process_query(user_query: str) -> PolygonGeneratorState:
    """
    Process a natural language query (Phase 1) - ASYNC

    This runs the LangGraph workflow until it either:
    - Completes successfully (returns final_polygon)
    - Pauses for user input (returns needs_user_input=True)
    - Encounters an error (returns errors)

    Args:
        user_query: User's natural language query

    Returns:
        State object with workflow results
    """
    graph = get_graph()
    initial_state = create_initial_state(user_query)
    result = await graph.ainvoke(initial_state)
    return result


async def resume_with_buffers(
    previous_state: PolygonGeneratorState, buffer_decisions: dict[str, float]
) -> PolygonGeneratorState:
    """
    Resume processing after user provides buffer decisions (Phase 2) - ASYNC

    This continues the workflow from where it paused, using the
    user-provided buffer radii to generate buffers and complete
    the polygon generation.

    Args:
        previous_state: State returned from process_query()
        buffer_decisions: Dict mapping location names to buffer radii (km)
                         Example: {"location1": 1.5, "location2": 2.0}

    Returns:
        State object with final polygon
    """
    resumed_state = previous_state.model_copy(deep=True)
    resumed_state.buffer_decisions = buffer_decisions
    resumed_state.needs_user_input = False

    updates = generate_buffers_node(resumed_state)
    for key, value in updates.items():
        setattr(resumed_state, key, value)

    updates = await validate_results_node(resumed_state)
    for key, value in updates.items():
        setattr(resumed_state, key, value)

    updates = merge_geometries_node(resumed_state)
    for key, value in updates.items():
        setattr(resumed_state, key, value)

    return resumed_state
