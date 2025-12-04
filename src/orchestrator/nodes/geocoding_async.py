"""
Geocode locations using Nominatim with rate limiting
"""

from src.orchestrator.state import PolygonGeneratorState
from src.geocoding import geocode_location_async


async def geocode_locations_node(state: PolygonGeneratorState) -> dict:
    """
    Geocode all extracted locations asynchronously (ASYNC)

    Args:
        state: Current workflow state

    Returns:
        State updates with geocoding results
    """
    print("Node: Geocoding locations (async)...")

    locations = state.locations
    context = state.context

    if not locations:
        return {
            "errors": ["No locations to geocode"],
            "current_step": "geocode_failed",
        }

    geocoding_results = {}

    for location in locations:
        search_query = location
        if context.get("city") and context["city"].lower() not in location.lower():
            search_query += f", {context['city']}"
        if context.get("country"):
            search_query += f", {context['country']}"

        try:
            results = await geocode_location_async(search_query, limit=15)

            if results:
                geocoding_results[location] = results
                print(f"  [+] {location}: {len(results)} results found")
            else:
                geocoding_results[location] = []
                print(f"  [!] {location}: No results found")

        except Exception as e:
            print(f"  [ERROR] Error geocoding {location}: {e}")
            geocoding_results[location] = []

    return {
        "geocoding_results": geocoding_results,
        "current_step": "locations_geocoded",
    }
