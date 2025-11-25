"""
Async Intent validation node
Validate if query is about polygons
"""

import asyncio
from src.orchestrator.state import PolygonGeneratorState
from src.llm_agents_async import create_async_agents


_agents_cache = None


def _get_async_agents():
    """Lazy initialization of async agents (singleton)"""
    global _agents_cache
    if _agents_cache is None:
        _agents_cache = create_async_agents()
    return _agents_cache


async def validate_intent_async(state: PolygonGeneratorState) -> dict:
    """
    Validate if user query is about geographic polygons

    Args:
        state: Current workflow state

    Returns:
        State updates with intent validation result
    """
    print("Node: Validating intent (async)...")

    query = state["user_query"]
    parser, _, _, _ = _get_async_agents()

    try:
        parsed = await parser.parse(query)

        if parsed.get("locations"):
            return {
                "is_polygon_request": True,
                "clarification_needed": None,
                "current_step": "intent_validated",
            }
        else:
            return {
                "is_polygon_request": False,
                "clarification_needed": "Could not identify any locations. Please describe geographic areas you want.",
                "current_step": "needs_clarification",
            }

    except Exception as e:
        return {
            "is_polygon_request": False,
            "clarification_needed": f"Error understanding query: {str(e)}",
            "current_step": "needs_clarification",
            "errors": [str(e)],
        }


def validate_intent_node(state: PolygonGeneratorState) -> dict:
    """Sync wrapper for async intent validation"""
    return asyncio.run(validate_intent_async(state))
