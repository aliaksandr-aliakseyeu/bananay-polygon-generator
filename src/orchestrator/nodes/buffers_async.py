"""
Async Buffer operations nodes
Suggest and generate buffers
Processes multiple locations in parallel
"""

from src.orchestrator.state import PolygonGeneratorState
from src.llm_agents_async import create_async_agents
from src.geometry import buffer_point


_agents_cache = None


def _get_async_agents():
    """Lazy initialization of async agents (singleton)"""
    global _agents_cache
    if _agents_cache is None:
        _agents_cache = create_async_agents()
    return _agents_cache


async def suggest_buffers_node(state: PolygonGeneratorState) -> dict:
    """
    Use LLM to suggest buffer radii for points without polygons (ASYNC)
    Processes all locations in parallel

    Args:
        state: Current workflow state

    Returns:
        State updates with AI-suggested buffer radii
    """
    print("Node: Suggesting buffer radii (async)...")

    locations_with_points = state.locations_with_points
    context = state.context
    _, _, _, buffer_agent = _get_async_agents()

    if not locations_with_points:
        return {
            "buffer_decisions": {},
            "needs_user_input": False,
            "current_step": "ready_to_merge",
        }

    location_data = [
        (loc_data["name"], loc_data["result"].place_type, context)
        for loc_data in locations_with_points
    ]

    print(f"  Processing {len(location_data)} locations in parallel...")

    try:
        radii = await buffer_agent.suggest_radius_batch(location_data)

        suggested_buffers = {}
        for (name, _, _), radius in zip(location_data, radii):
            if isinstance(radius, Exception):
                suggested_buffers[name] = 1.0
                print(f"  [!] {name}: Fallback to 1.0 km (error)")
            else:
                suggested_buffers[name] = radius
                print(f"  [i] {name}: Suggested {radius} km")

    except Exception as e:
        print(f"  [!] Batch processing failed: {e}")
        suggested_buffers = {
            loc_data["name"]: 1.0
            for loc_data in locations_with_points
        }

    needs_user_input = len(locations_with_points) > 0

    return {
        "buffer_decisions": suggested_buffers,
        "needs_user_input": needs_user_input,
        "current_step": "buffers_suggested" if needs_user_input else "ready_to_merge",
    }


def generate_buffers_node(state: PolygonGeneratorState) -> dict:
    """
    Generate buffer polygons for points using user-provided radii
    (Pure computation - no async needed)

    Args:
        state: Current workflow state

    Returns:
        State updates with generated buffers
    """
    print("Node: Generating buffers...")

    locations_with_points = state.locations_with_points
    buffer_decisions = state.buffer_decisions

    buffered_geometries = []

    for loc_data in locations_with_points:
        name = loc_data["name"]
        result = loc_data["result"]
        radius = buffer_decisions.get(name, 1.0)

        try:
            buffer_geom = buffer_point((result.lon, result.lat), radius_km=radius)
            buffered_geometries.append({
                "name": f"{name} ({radius}km buffer)",
                "result": result,
                "geometry": buffer_geom,
                "source": "generated",
                "radius_km": radius,
            })
            print(f"  [+] {name}: Buffer generated ({radius} km)")
        except Exception as e:
            print(f"  [ERROR] {name}: Buffer generation failed - {e}")

    return {
        "locations_with_polygons": state.locations_with_polygons + buffered_geometries,
        "current_step": "buffers_generated",
    }
