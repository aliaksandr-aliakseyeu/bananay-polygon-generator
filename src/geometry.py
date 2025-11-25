"""
Geometry operations using Shapely
"""

from typing import List, Union, Optional
from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping
from shapely.ops import unary_union
import geojson


def buffer_point(
    coordinates: tuple[float, float], radius_km: float, resolution: int = 16
) -> Polygon:
    """
    Create a circular buffer around a point

    Args:
        coordinates: (lon, lat) tuple
        radius_km: Radius in kilometers
        resolution: Number of points to approximate circle (higher = smoother)

    Returns:
        Shapely Polygon representing the buffer
    """
    lon, lat = coordinates
    radius_deg = radius_km / 111.0
    point = Point(lon, lat)
    circle = point.buffer(radius_deg, resolution=resolution)

    return circle


# def union_polygons(polygons: List[Union[Polygon, MultiPolygon]]) -> Union[Polygon, MultiPolygon]:
#     """
#     Merge multiple polygons into one

#     Args:
#         polygons: List of Shapely Polygon or MultiPolygon objects

#     Returns:
#         Single Polygon or MultiPolygon containing all input geometries
#     """
#     if not polygons:
#         raise ValueError("Cannot union empty list of polygons")

#     if len(polygons) == 1:
#         return polygons[0]

#     return unary_union(polygons)


def union_polygons_smart(
    polygons: List[Union[Polygon, MultiPolygon]],
    return_list: bool = True
) -> Union[List[Polygon], Polygon, MultiPolygon]:
    """
    Smart polygon union that handles disconnected regions intelligently

    Args:
        polygons: List of Shapely Polygon or MultiPolygon objects
        return_list: If True, returns list of separate polygons when disconnected.
                    If False, returns single Polygon or MultiPolygon (like union_polygons)

    Returns:
        - If return_list=True and result is MultiPolygon: List of separate Polygon objects
        - If return_list=True and result is Polygon: List with single Polygon
        - If return_list=False: Single Polygon or MultiPolygon
    """
    if not polygons:
        raise ValueError("Cannot union empty list of polygons")

    if len(polygons) == 1:
        poly = polygons[0]
        if return_list:
            if isinstance(poly, MultiPolygon):
                return list(poly.geoms)
            return [poly]
        return poly

    result = unary_union(polygons)

    if return_list:
        if isinstance(result, MultiPolygon):
            return list(result.geoms)
        else:
            return [result]
    else:
        return result


# def get_separate_polygons(geometry: Union[Polygon, MultiPolygon]) -> List[Polygon]:
#     """
#     Extract separate polygons from a geometry

#     Args:
#         geometry: Shapely Polygon or MultiPolygon

#     Returns:
#         List of separate Polygon objects
#     """
#     if isinstance(geometry, MultiPolygon):
#         return list(geometry.geoms)
#     return [geometry]


# def count_separate_regions(geometry: Union[Polygon, MultiPolygon]) -> int:
#     """
#     Count number of separate (disconnected) regions in a geometry

#     Args:
#         geometry: Shapely Polygon or MultiPolygon

#     Returns:
#         Number of separate regions (1 for Polygon, n for MultiPolygon)
#     """
#     if isinstance(geometry, MultiPolygon):
#         return len(geometry.geoms)
#     return 1


def simplify_geometry(
    geometry: Union[Polygon, MultiPolygon], tolerance: float = 0.001
) -> Union[Polygon, MultiPolygon]:
    """
    Simplify geometry by removing unnecessary vertices

    Args:
        geometry: Shapely Polygon or MultiPolygon
        tolerance: Simplification tolerance (in degrees).
                   0.001 ≈ 111 meters at equator

    Returns:
        Simplified geometry
    """
    return geometry.simplify(tolerance, preserve_topology=True)


def to_geojson(geometry: Union[Polygon, MultiPolygon], properties: Optional[dict] = None) -> dict:
    """
    Convert Shapely geometry to GeoJSON Feature

    Args:
        geometry: Shapely Polygon or MultiPolygon
        properties: Optional properties dict

    Returns:
        GeoJSON Feature dict
    """
    feature = geojson.Feature(
        geometry=mapping(geometry), properties=properties or {}
    )
    return feature


def from_geojson(geojson_data: Union[dict, str]) -> Union[Polygon, MultiPolygon]:
    """
    Convert GeoJSON to Shapely geometry

    Args:
        geojson_data: GeoJSON dict or string

    Returns:
        Shapely Polygon or MultiPolygon
    """
    if isinstance(geojson_data, str):
        import json
        geojson_data = json.loads(geojson_data)

    if geojson_data.get("type") == "Feature":
        geojson_data = geojson_data["geometry"]

    return shape(geojson_data)


def get_bounding_box(geometry: Union[Polygon, MultiPolygon]) -> tuple[float, float, float, float]:
    """
    Get bounding box of geometry

    Args:
        geometry: Shapely geometry

    Returns:
        Tuple of (min_lon, min_lat, max_lon, max_lat)
    """
    bounds = geometry.bounds
    return bounds


def calculate_area_km2(geometry: Union[Polygon, MultiPolygon]) -> float:
    """
    Calculate approximate area in square kilometers

    Args:
        geometry: Shapely geometry

    Returns:
        Area in square kilometers
    """
    centroid = geometry.centroid
    lat = centroid.y
    area_deg2 = geometry.area

    import math

    lat_correction = math.cos(math.radians(lat))
    km_per_deg_lon = 111.32 * lat_correction
    km_per_deg_lat = 110.574

    area_km2 = area_deg2 * km_per_deg_lon * km_per_deg_lat

    return area_km2


def create_convex_hull(geometries: List[Union[Point, Polygon, MultiPolygon]]) -> Polygon:
    """
    Create convex hull around multiple geometries

    Args:
        geometries: List of Shapely geometries

    Returns:
        Convex hull Polygon
    """
    if not geometries:
        raise ValueError("Cannot create convex hull from empty list")

    combined = unary_union(geometries)
    return combined.convex_hull


def is_valid_geometry(geometry: Union[Polygon, MultiPolygon]) -> tuple[bool, str]:
    """
    Check if geometry is valid

    Args:
        geometry: Shapely geometry

    Returns:
        Tuple of (is_valid, error_message)
    """
    if geometry.is_valid:
        return True, ""
    else:
        from shapely.validation import explain_validity

        return False, explain_validity(geometry)


def fix_geometry(geometry: Union[Polygon, MultiPolygon]) -> Union[Polygon, MultiPolygon]:
    """
    Attempt to fix invalid geometry

    Args:
        geometry: Potentially invalid Shapely geometry

    Returns:
        Fixed geometry
    """
    if geometry.is_valid:
        return geometry

    return geometry.buffer(0)


# if __name__ == "__main__":
#     # Test the geometry module
#     print("Testing Geometry Module")
#     print("=" * 60)

#     # Test 1: Create buffer around a point (Minsk center)
#     print("\n1. Creating 5km buffer around Minsk (27.56, 53.90)...")
#     minsk_point = (27.56, 53.90)
#     buffer = buffer_point(minsk_point, radius_km=5)
#     print(f"   Buffer created: {buffer.geom_type}")
#     print(f"   Number of points: {len(buffer.exterior.coords)}")
#     print(f"   Approximate area: {calculate_area_km2(buffer):.2f} km²")

#     # Test 2: Create multiple buffers and union them
#     print("\n2. Creating buffers around 3 points and merging...")
#     point1 = (27.56, 53.90)  # Minsk center
#     point2 = (27.65, 53.95)  # Northeast
#     point3 = (27.50, 53.85)  # Southwest

#     buffer1 = buffer_point(point1, radius_km=2)
#     buffer2 = buffer_point(point2, radius_km=2)
#     buffer3 = buffer_point(point3, radius_km=2)

#     merged = union_polygons([buffer1, buffer2, buffer3])
#     print(f"   Merged geometry type: {merged.geom_type}")
#     print(f"   Combined area: {calculate_area_km2(merged):.2f} km²")

#     # Test 3: Simplify geometry
#     print("\n3. Simplifying merged geometry...")
#     original_points = len(merged.exterior.coords) if hasattr(merged, 'exterior') else 0
#     simplified = simplify_geometry(merged, tolerance=0.01)
#     simplified_points = len(simplified.exterior.coords) if hasattr(simplified, 'exterior') else 0

#     if original_points > 0:
#         print(f"   Original points: {original_points}")
#         print(f"   Simplified points: {simplified_points}")
#         reduction_pct = (1 - simplified_points/original_points)*100
#         print(f"   Reduction: {reduction_pct:.1f}%")

#     # Test 4: Convert to GeoJSON
#     print("\n4. Converting to GeoJSON...")
#     geojson_feature = to_geojson(
#         simplified, properties={"name": "Test Area", "type": "buffer_union"}
#     )
#     print(f"   GeoJSON type: {geojson_feature['type']}")
#     print(f"   Geometry type: {geojson_feature['geometry']['type']}")
#     print(f"   Properties: {geojson_feature['properties']}")

#     # Test 5: Bounding box
#     print("\n5. Calculating bounding box...")
#     bbox = get_bounding_box(merged)
#     print(f"   Bounding box: {bbox}")
#     print("   (min_lon, min_lat, max_lon, max_lat)")

#     # Test 6: Validation
#     print("\n6. Validating geometry...")
#     is_valid, error = is_valid_geometry(merged)
#     print(f"   Valid: {is_valid}")
#     if error:
#         print(f"   Error: {error}")

#     print("\n" + "=" * 60)
#     print("Geometry module test complete!")
