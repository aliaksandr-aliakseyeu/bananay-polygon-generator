"""
Merge geometries node
Merge all geometries into final polygon
"""

from src.orchestrator.state import PolygonGeneratorState
from src.geometry import (
    union_polygons_smart,
    calculate_area_km2,
)


def merge_geometries_node(state: PolygonGeneratorState) -> dict:
    """
    Merge all geometries into final polygon(s) using union

    Args:
        state: Current workflow state

    Returns:
        State updates with final polygon (or list of polygons if disconnected)
    """
    print("Node: Merging geometries...")

    locations_with_polygons = state["locations_with_polygons"]

    if not locations_with_polygons:
        return {
            "errors": ["No geometries to merge"],
            "current_step": "merge_failed",
        }

    try:
        geometries = [loc["geometry"] for loc in locations_with_polygons]

        result_polygons = union_polygons_smart(geometries, return_list=True)

        num_regions = len(result_polygons)
        is_disconnected = num_regions > 1

        total_area_km2 = sum(calculate_area_km2(poly) for poly in result_polygons)

        regions_metadata = []
        for i, poly in enumerate(result_polygons, 1):
            region_area = calculate_area_km2(poly)
            regions_metadata.append({
                "region_number": i,
                "area_km2": region_area,
                "centroid": {
                    "lat": poly.centroid.y,
                    "lon": poly.centroid.x,
                }
            })

        final_polygon = {
            "geometry": result_polygons[0] if num_regions == 1 else result_polygons,
            "components": locations_with_polygons,
            "metadata": {
                "area_km2": total_area_km2,
                "total_locations": len(locations_with_polygons),
                "num_separate_regions": num_regions,
                "is_disconnected": is_disconnected,
                "regions": regions_metadata,
            },
        }

        print(f"  ✓ Merged {len(geometries)} geometries")
        print(f"  ✓ Total area: {total_area_km2:.2f} km²")

        if is_disconnected:
            print(f"  ⚠️ Result: {num_regions} SEPARATE (disconnected) regions")
            for i, meta in enumerate(regions_metadata, 1):
                print(f"     Region {i}: {meta['area_km2']:.2f} km²")
        else:
            print("  ✓ Result: 1 connected region")

        warnings = []
        if is_disconnected:
            warnings.append(
                f"Your query resulted in {num_regions} separate (disconnected) regions. "
                + "These locations are far apart and don't share borders."
            )

        return {
            "final_polygon": final_polygon,
            "warnings": warnings,
            "current_step": "complete",
        }

    except Exception as e:
        return {
            "errors": [f"Merge error: {str(e)}"],
            "current_step": "merge_failed",
        }
