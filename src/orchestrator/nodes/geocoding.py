"""
Geocoding node
Geocode locations using Nominatim
"""

from src.orchestrator.state import PolygonGeneratorState
from src.geocoding import geocode_location


def geocode_locations_node(state: PolygonGeneratorState) -> dict:
    """
    Geocode all extracted locations

    Args:
        state: Current workflow state

    Returns:
        State updates with geocoding results
    """
    print("Node: Geocoding locations...")

    locations = state["locations"]
    context = state["context"]

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
            results = geocode_location(search_query, limit=15)

            if results:
                geocoding_results[location] = results
            else:
                geocoding_results[location] = []

        except Exception as e:
            print(f"  Error geocoding {location}: {e}")
            geocoding_results[location] = []

    return {
        "geocoding_results": geocoding_results,
        "current_step": "locations_geocoded",
    }
