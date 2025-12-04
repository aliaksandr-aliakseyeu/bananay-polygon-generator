"""
Results Display Components
Displays workflow results, intermediate steps, and final polygon
"""

import streamlit as st
from streamlit_folium import st_folium
import json
import urllib.parse
from typing import Dict

from .map_renderer import create_map
from src.geometry import to_geojson, get_bounding_box


def display_errors_and_clarifications(state: Dict):
    """Display errors and clarification needs"""
    if state.get("errors"):
        st.error("❌ Errors occurred:")
        for error in state["errors"]:
            st.error(f"  • {error}")

    if state.get("clarification_needed"):
        st.warning(f"⚠️ {state['clarification_needed']}")
        st.info("Please rephrase your query and try again.")
        return True
    return False


def display_parsed_query(state: Dict):
    """Display parsed query locations and context"""
    if state.get("locations"):
        with st.expander("📝 Parsed Query", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Locations:**")
                for loc in state["locations"]:
                    st.write(f"  • {loc}")
            with col2:
                st.write("**Context:**")
                for key, value in state.get("context", {}).items():
                    if value:
                        st.write(f"  • {key}: {value}")


def display_geocoding_results(state: Dict):
    """Display all geocoding results from Nominatim"""
    if state.get("geocoding_results"):
        with st.expander("🔍 All Geocoding Results (from Nominatim)", expanded=False):
            for location, results in state["geocoding_results"].items():
                st.write(f"**{location}** — found {len(results)} variants:")

                if not results:
                    st.warning("  [!] No results found")
                    continue

                for i, result in enumerate(results, 1):
                    selected = state.get("selected_locations", {}).get(location)
                    is_selected = selected and selected.place_id == result.place_id

                    if is_selected:
                        st.success(f"  [+] **[SELECTED by AI]** #{i}: {result.display_name}")
                    else:
                        st.info(f"  #{i}: {result.display_name}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Type: {result.place_type}")
                    with col2:
                        st.caption(f"Importance: {result.importance:.2f}")
                    with col3:
                        st.caption(f"Coords: {result.lat:.4f}, {result.lon:.4f}")

                st.divider()


def display_selected_locations(state: Dict):
    """Display locations selected by AI disambiguation"""
    if state.get("selected_locations"):
        with st.expander("🌍 Selected Locations (after AI disambiguation)", expanded=False):
            for name, result in state["selected_locations"].items():
                try:
                    display_name = result.display_name
                except (AttributeError, UnicodeDecodeError):
                    display_name = "[Special characters]"
                st.success(f"[+] {name} → {display_name}")


def display_final_polygon(state: Dict, user_query: str = "", debug: bool = False):
    """Display final polygon with map, export options, and metadata"""
    if not (state.get("final_polygon") and state.get("current_step") == "complete"):
        return

    st.divider()
    st.header("🗺️ Final Result")

    poly_data = state["final_polygon"]
    metadata = poly_data["metadata"]

    num_regions = metadata.get("num_separate_regions", 1)
    is_disconnected = metadata.get("is_disconnected", False)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Area", f"{metadata['area_km2']:.2f} km^2")
    with col2:
        st.metric("Locations", metadata["total_locations"])
    with col3:
        if is_disconnected:
            st.metric("Separate Regions", num_regions, delta="[!] Disconnected", delta_color="off")
        else:
            st.metric("Regions", num_regions, delta="[+] Connected", delta_color="normal")

    if is_disconnected:
        st.info(
            f"[i] Your result contains **{num_regions} separate regions** "
            f"that don't share borders (e.g., cities far apart). "
            f"See details below."
        )

        with st.expander("📍 Region Details", expanded=True):
            for region_meta in metadata.get("regions", []):
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.write(f"**Region {region_meta['region_number']}:**")
                with col_b:
                    st.write(f"Area: {region_meta['area_km2']:.2f} km^2")
                    centroid = region_meta.get('centroid', {})
                    if centroid:
                        st.caption(f"Center: {centroid['lat']:.4f}, {centroid['lon']:.4f}")

    if state.get("warnings"):
        with st.expander("⚠️ Warnings & Suggestions", expanded=False):
            for warning in state["warnings"]:
                st.warning(warning)

    st.subheader("Interactive Map")

    geometry = poly_data["geometry"]
    if isinstance(geometry, list):
        final_geoms = [
            {
                "geometry": geom,
                "name": f"Final Region {i}",
                "source": "final",
            }
            for i, geom in enumerate(geometry, 1)
        ]
    else:
        final_geoms = [
            {
                "geometry": geometry,
                "name": "Final Combined Polygon",
                "source": "final",
            }
        ]

    map_geoms = poly_data["components"] + final_geoms

    m = create_map(map_geoms)
    st_folium(m, width=1200, height=600)

    st.divider()
    st.subheader("💾 Export")

    col1, col2, col3 = st.columns(3)

    with col1:
        geometry_for_export = poly_data["geometry"]
        if isinstance(geometry_for_export, list):
            from shapely.geometry import MultiPolygon
            geometry_for_export = MultiPolygon(geometry_for_export)

        geojson_output = to_geojson(
            geometry_for_export,
            properties={
                "name": "Generated Polygon",
                "area_km2": metadata["area_km2"],
                "total_locations": metadata["total_locations"],
                "num_separate_regions": metadata.get("num_separate_regions", 1),
                "is_disconnected": metadata.get("is_disconnected", False),
                "generated_by": "polygon-generator-langgraph",
                "query": user_query if user_query else "N/A",
            },
        )

        st.download_button(
            label="📥 Download GeoJSON",
            data=json.dumps(geojson_output, indent=2, ensure_ascii=False),
            file_name="polygon.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )

    with col2:
        geojson_str = json.dumps(geojson_output)
        encoded = urllib.parse.quote(geojson_str)
        geojson_io_url = (
            f"http://geojson.io/#data=data:application/json,{encoded}"
        )

        st.link_button(
            "🌐 View in geojson.io",
            geojson_io_url,
            use_container_width=True,
        )

    with col3:
        geometry_for_bbox = poly_data["geometry"]
        if isinstance(geometry_for_bbox, list):
            from shapely.geometry import MultiPolygon
            geometry_for_bbox = MultiPolygon(geometry_for_bbox)

        bbox = get_bounding_box(geometry_for_bbox)
        bbox_str = f"[{bbox[0]:.4f}, {bbox[1]:.4f}, {bbox[2]:.4f}, {bbox[3]:.4f}]"
        st.text_input(
            "Bounding Box",
            value=bbox_str,
            help="min_lon, min_lat, max_lon, max_lat",
        )

    with st.expander("📊 Detailed Information"):
        st.write("**Components:**")
        for comp in poly_data["components"]:
            source = comp.get("source", "unknown")
            st.write(f"• {comp['name']} (source: {source})")

        st.write("**Metadata:**")
        st.json(metadata)

        if debug:
            st.write("**Full State:**")
            display_state = {
                k: v
                for k, v in state.items()
                if k not in ["selected_locations", "final_polygon"]
            }
            st.json(display_state)
