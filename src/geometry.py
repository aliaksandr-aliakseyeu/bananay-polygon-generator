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
