"""
Boundary fetching node
Fetch polygon boundaries from OSM
"""

from src.orchestrator.state import PolygonGeneratorState


def fetch_boundaries_node(state: PolygonGeneratorState) -> dict:
    """
    Try to get polygon boundaries from OSM
    Separate locations into: with_polygons and with_points

    Args:
        state: Current workflow state (Pydantic BaseModel)

    Returns:
        State updates with boundary data
    """
    print("Node: Fetching boundaries...")

    selected_locations = state.selected_locations

    locations_with_polygons = []
    locations_with_points = []

    for location_name, result in selected_locations.items():
        if result.has_polygon:
            polygon = result.get_polygon()
            if polygon:
                locations_with_polygons.append({
                    "name": location_name,
                    "result": result,
                    "geometry": polygon,
                    "source": "OSM",
                })
                print(f"  {location_name}: Has polygon")
            else:
                locations_with_points.append({
                    "name": location_name,
                    "result": result,
                })
                print(f"  {location_name}: Polygon parse failed, treating as point")
        else:
            locations_with_points.append({
                "name": location_name,
                "result": result,
            })
            print(f"  {location_name}: Point only (needs buffer)")

    return {
        "locations_with_polygons": locations_with_polygons,
        "locations_with_points": locations_with_points,
        "current_step": "boundaries_fetched",
    }
