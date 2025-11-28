"""
Async Validation node
Validate results using LLM

LangGraph 1.0: Native async support - no sync wrapper needed
"""

from src.orchestrator.state import PolygonGeneratorState
from src.llm_agents_async import create_async_agents


_agents_cache = None


def _get_async_agents():
    """Lazy initialization of async agents (singleton)"""
    global _agents_cache
    if _agents_cache is None:
        _agents_cache = create_async_agents()
    return _agents_cache


async def validate_results_node(state: PolygonGeneratorState) -> dict:
    """
    Use LLM to validate that geocoding results make sense (ASYNC)

    Args:
        state: Current workflow state

    Returns:
        State updates with validation warnings/suggestions
    """
    print("Node: Validating results (async)...")

    _, _, validator, _ = _get_async_agents()

    try:
        if not state.selected_locations:
            print("  [!] No selected_locations in state, skipping validation")
            return {
                "warnings": [],
                "current_step": "results_validated",
            }

        geocoded_locations = [
            {"query": name, "result": result}
            for name, result in state.selected_locations.items()
        ]

        validation = await validator.validate(
            state.user_query,
            {
                "locations": state.locations,
                "context": state.context,
            },
            geocoded_locations,
        )

        warnings = validation.get("warnings", [])
        suggestions = validation.get("suggestions", [])

        return {
            "warnings": warnings + suggestions,
            "current_step": "results_validated",
        }

    except Exception as e:
        print(f"  [!] Validation error: {e}")
        return {
            "warnings": ["Validation step encountered an error"],
            "current_step": "results_validated",
        }
