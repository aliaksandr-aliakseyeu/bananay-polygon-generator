"""
Async Query parsing node
Parse natural language to extract locations
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


async def parse_query_async(state: PolygonGeneratorState) -> dict:
    """
    Parse natural language query

    Extracts and normalizes:
    - Location names (with spelling correction)
    - Context (city, country)
    - Language detection

    Args:
        state: Current workflow state

    Returns:
        State updates with parsed data
    """
    print("Node: Parsing query (async)...")

    query = state["user_query"]
    parser, _, _, _ = _get_async_agents()

    try:
        parsed = await parser.parse(query)

        return {
            "locations": parsed.get("locations", []),
            "context": parsed.get("context", {}),
            "language": parsed.get("language", "unknown"),
            "current_step": "query_parsed",
        }

    except Exception as e:
        return {
            "errors": [f"Parse error: {str(e)}"],
            "current_step": "parse_failed",
        }


def parse_query_node(state: PolygonGeneratorState) -> dict:
    """Sync wrapper for async query parsing"""
    return asyncio.run(parse_query_async(state))
