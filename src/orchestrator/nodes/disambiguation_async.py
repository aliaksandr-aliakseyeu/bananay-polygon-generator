"""
ASYNC Disambiguation node
Processes multiple locations in parallel

LangGraph 1.0: Native async support - no sync wrapper needed
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


async def disambiguate_node(state: PolygonGeneratorState) -> dict:
    """
    Use LLM to pick best geocoding result for each location (ASYNC)
    Processes all locations in parallel

    Args:
        state: Current workflow state

    Returns:
        State updates with selected locations
    """
    print("Node: Disambiguating results (async)...")

    geocoding_results = state.geocoding_results
    context = state.context
    _, disambiguator, _, _ = _get_async_agents()

    selected_locations = {}

    single_result_locations = {}
    multi_result_locations = []

    for location, results in geocoding_results.items():
        if not results:
            print(f"  No results for {location}")
            continue

        if len(results) == 1:
            single_result_locations[location] = results[0]
        else:
            multi_result_locations.append((location, results))

    if multi_result_locations:
        print(f"  Disambiguating {len(multi_result_locations)} locations in parallel...")

        tasks = [
            disambiguator.select_best(location, results, context)
            for location, results in multi_result_locations
        ]

        results_indices = await asyncio.gather(*tasks, return_exceptions=True)

        for (location, results), best_idx in zip(multi_result_locations, results_indices):
            if isinstance(best_idx, Exception):
                selected_locations[location] = max(
                    results, key=lambda r: r.importance
                )
                print(f"  [!] {location}: Fallback to highest importance (error: {best_idx})")
            else:
                selected_locations[location] = results[best_idx]
                print(f"  [+] {location}: Selected result {best_idx + 1} of {len(results)}")

    selected_locations.update(single_result_locations)

    if not selected_locations:
        return {
            "errors": ["No locations could be geocoded"],
            "current_step": "disambiguation_failed",
        }

    return {
        "selected_locations": selected_locations,
        "current_step": "results_disambiguated",
    }
