"""
Map Rendering Component using Folium
"""

from streamlit_folium import st_folium
import folium
from typing import List, Dict, Optional

from src.geometry import to_geojson


def create_map(geometries: List[Dict], center: Optional[tuple] = None):
    """
    Create Folium map with geometries

    Args:
        geometries: List of geometry dictionaries with 'geometry', 'name', 'source' keys
        center: Tuple of (lat, lon) for map center. If None, calculated from geometries

    Returns:
        folium.Map object
    """
    if center is None:
        if geometries:
            all_coords = []
            for geom_data in geometries:
                geom = geom_data["geometry"]
                if hasattr(geom, "centroid"):
                    all_coords.append((geom.centroid.y, geom.centroid.x))

            if all_coords:
                avg_lat = sum(c[0] for c in all_coords) / len(all_coords)
                avg_lon = sum(c[1] for c in all_coords) / len(all_coords)
                center = (avg_lat, avg_lon)
            else:
                center = (53.9, 27.56)  # Default: Minsk
        else:
            center = (53.9, 27.56)  # Default: Minsk

    m = folium.Map(location=center, zoom_start=11, tiles="OpenStreetMap")

    for geom_data in geometries:
        geom = geom_data["geometry"]
        name = geom_data.get("name", "Location")
        source = geom_data.get("source", "unknown")

        if source == "OSM":
            color = "green"
        elif source == "generated":
            color = "orange"
        else:
            color = "red"

        geojson_data = to_geojson(geom, properties={"name": name, "source": source})

        folium.GeoJson(
            geojson_data,
            name=name,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": 0.3,
            },
            tooltip=name,
        ).add_to(m)

    return m


def render_map(geometries: List[Dict], center: Optional[tuple] = None, height: int = 600):
    """
    Render Folium map in Streamlit

    Args:
        geometries: List of geometry dictionaries
        center: Optional map center coordinates
        height: Map height in pixels
    """
    m = create_map(geometries, center)
    st_folium(m, height=height, width=None)
