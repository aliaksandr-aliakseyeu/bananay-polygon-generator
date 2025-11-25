"""
Public interface for polygon generation workflow
Provide clean API for external use
"""

from src.orchestrator.state import PolygonGeneratorState, create_initial_state
from src.orchestrator.graph import get_graph
from src.orchestrator.nodes.buffers_async import generate_buffers_node
from src.orchestrator.nodes.validation_async import validate_results_node
from src.orchestrator.nodes.merge import merge_geometries_node


def process_query(user_query: str) -> PolygonGeneratorState:
    """
    Process a natural language query (Phase 1)

    This runs the LangGraph workflow until it either:
    - Completes successfully (returns final_polygon)
    - Pauses for user input (returns needs_user_input=True)
    - Encounters an error (returns errors)

    Args:
        user_query: User's natural language query

    Returns:
        State dict with workflow results
    """
    graph = get_graph()
    initial_state = create_initial_state(user_query)
    result = graph.invoke(initial_state)
    return result


def resume_with_buffers(
    previous_state: PolygonGeneratorState, buffer_decisions: dict
) -> PolygonGeneratorState:
    """
    Resume processing after user provides buffer decisions (Phase 2)

    This continues the workflow from where it paused, using the
    user-provided buffer radii to generate buffers and complete
    the polygon generation.

    Args:
        previous_state: State returned from process_query()
        buffer_decisions: Dict mapping location names to buffer radii (km)
                         Example: {"location1": 1.5, "location2": 2.0}

    Returns:
        State dict with final polygon
    """
    resumed_state = dict(previous_state)
    resumed_state["buffer_decisions"] = buffer_decisions
    resumed_state["needs_user_input"] = False

    updates = generate_buffers_node(resumed_state)
    resumed_state.update(updates)

    updates = validate_results_node(resumed_state)
    resumed_state.update(updates)

    updates = merge_geometries_node(resumed_state)
    resumed_state.update(updates)

    return resumed_state
