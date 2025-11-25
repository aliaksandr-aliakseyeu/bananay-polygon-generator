"""
Merged: Parse query and validate intent in ONE API call
Replaces: intent_async.py + parser_async.py
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


async def parse_and_validate_async(state: PolygonGeneratorState) -> dict:
    """
    Parse query and validate intent in ONE API call

    Extracts and normalizes:
    - Location names (with spelling correction)
    - Context (city, country)
    - Language detection

    AND validates:
    - Is this a polygon request?
    - Are locations found?

    Args:
        state: Current workflow state

    Returns:
        State updates with parsed data OR clarification needed
    """
    print("Node: Parsing and validating query (async)...")

    query = state["user_query"]
    parser, _, _, _ = _get_async_agents()

    try:
        # ONE API call to parse the query
        parsed = await parser.parse(query)

        # Check if locations were found
        locations = parsed.get("locations", [])

        if locations:
            # Valid polygon request with locations
            return {
                "is_polygon_request": True,
                "clarification_needed": None,
                "locations": locations,
                "context": parsed.get("context", {}),
                "language": parsed.get("language", "unknown"),
                "current_step": "query_parsed",
            }
        else:
            # No locations found - need clarification
            return {
                "is_polygon_request": False,
                "clarification_needed": (
                    "Could not identify any locations. "
                    "Please describe geographic areas you want."
                ),
                "current_step": "needs_clarification",
            }

    except Exception as e:
        # Error during parsing
        return {
            "is_polygon_request": False,
            "clarification_needed": f"Error understanding query: {str(e)}",
            "current_step": "needs_clarification",
            "errors": [str(e)],
        }


def parse_and_validate_node(state: PolygonGeneratorState) -> dict:
    """Sync wrapper for async parse and validate"""
    return asyncio.run(parse_and_validate_async(state))
