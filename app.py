"""
Polygon Generator - Natural Language to Geographic Polygons
Powered by LangGraph, OpenAI, and OpenStreetMap
"""

import streamlit as st
from streamlit_folium import st_folium
import folium
import json
from typing import Optional, List, Dict

from src.config import config
from src.orchestrator import process_query, resume_with_buffers
from src.geometry import to_geojson, get_bounding_box

st.set_page_config(
    page_title="Polygon Generator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables"""
    if "graph_state" not in st.session_state:
        st.session_state.graph_state = None
    if "processing" not in st.session_state:
        st.session_state.processing = False


def render_header():
    """Render application header"""
    st.markdown(
        '<div class="main-header">🗺️ Polygon Generator</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Natural language to geographic polygons • Powered by LangGraph</div>',
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render sidebar with info and settings"""
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown(
            """
            Describe the area you want in **natural language**,
            and get a polygon!

            ### Examples:

            **English:**
            ```
            I want a polygon that includes
            Uruchye-6 and Kolodishchi in Minsk district
            and Sukhorukie in Minsk district
            ```

            **Russian:**
            ```
            Я хочу полигон который включает
            Уручье-6 Минска + Колодищи в Минском районе +
            Сухорукие в Минском районе
            ```

            ### ✨ Features:
            - 🔤 **Auto-corrects spelling** (e.g., "Совецкий" → "Советский")
            - 🌍 **Smart context detection** (understands city/country)
            - 🔀 **Handles disconnected regions** (returns multiple polygons)
            - 📥 **Export to GeoJSON**

            ### Powered by:
            - 🤖 **LangGraph** - State-driven workflow
            - 🧠 **OpenAI GPT-5** - Natural language understanding
            - 🗺️ **OpenStreetMap** - Geographic data
            - 🔷 **Shapely** - Geometry operations
            """
        )

        st.divider()

        st.header("⚙️ Settings")

        debug = st.checkbox("Debug mode", value=config.DEBUG)

        st.divider()

        st.header("🔧 Status")
        is_valid, messages = config.validate()

        if is_valid:
            st.success("✓ Configuration OK")
        else:
            st.error("✗ Configuration issues")

        for msg in messages:
            if msg.startswith("Warning:"):
                st.warning(msg)
            else:
                st.error(msg)

        if not config.OPENAI_API_KEY:
            st.error("⚠️ OpenAI API key not set!")
            st.info("Add OPENAI_API_KEY to .env file")

        return debug


def display_workflow_progress(state: dict):
    """Display current workflow step"""
    current_step = state.get("current_step", "start")

    steps = {
        "start": ("⏳", "Starting..."),
        "intent_validated": ("✅", "Intent validated"),
        "query_parsed": ("📝", "Query parsed"),
        "locations_geocoded": ("🌍", "Locations geocoded"),
        "results_disambiguated": ("🤖", "Results disambiguated"),
        "boundaries_fetched": ("📐", "Boundaries fetched"),
        "buffers_suggested": ("💡", "Buffer radii suggested"),
        "buffers_generated": ("🎯", "Buffers generated"),
        "results_validated": ("✅", "Results validated"),
        "complete": ("🎉", "Complete!"),
    }

    if current_step in steps:
        emoji, text = steps[current_step]
        st.info(f"{emoji} **Current step:** {text}")


def create_map(geometries: List[Dict], center: Optional[tuple] = None):
    """Create Folium map with geometries"""
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
                center = (53.9, 27.56)
        else:
            center = (53.9, 27.56)

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


def main():
    """Main application logic"""
    initialize_session_state()
    render_header()
    debug = render_sidebar()

    st.divider()

    st.header("💬 Describe the Area You Want")

    user_query = st.text_area(
        "Enter your request in natural language:",
        height=120,
        placeholder="""
            Examples:
            I want a polygon that includes Uruchye-6 and Kolodishchi in Minsk district and Sukhorukie in Minsk district
            Я хочу полигон который включает микрорайон Уручье-6 Минска + Колодищи в минском районе +
            деревня Сухорукие в минском районе
        """,
        help="Describe the locations you want in English or Russian",
    )

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        process_button = st.button(
            "🚀 Generate Polygon",
            type="primary",
            disabled=not user_query.strip() or st.session_state.processing,
            use_container_width=True,
        )

    with col2:
        if st.session_state.graph_state:
            if st.button("🔄 Start New", use_container_width=True):
                st.session_state.graph_state = None
                st.session_state.processing = False
                st.rerun()

    with col3:
        show_example = st.checkbox("Show example")

    if show_example:
        st.info(
            """
            **Example query:**

            "I want to combine Pervomaisky district, Uruchye-6 in Minsk district, Kolodishchi in Minsk district
            and Sukhorukie in Minsk district into one polygon"

            The LangGraph workflow will:
            1. ✅ Validate intent (is it about polygons?)
            2. 📝 Parse query (extract locations)
            3. 🌍 Geocode each location
            4. 🤖 Disambiguate results (pick best matches)
            5. 📐 Fetch boundaries from OSM
            6. 💡 Suggest buffer radii (if needed)
            7. ⏸️ Pause for user input (buffer confirmation)
            8. ✅ Validate results
            9. 🔗 Merge geometries
            10. 🎉 Return final polygon!
        """
        )

    if process_button and user_query.strip():
        st.divider()
        st.session_state.processing = True

        with st.spinner("🤖 LangGraph is processing your query..."):
            try:
                result = process_query(user_query)
                st.session_state.graph_state = result

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if debug:
                    import traceback
                    st.code(traceback.format_exc())
                st.session_state.processing = False

        st.session_state.processing = False
        st.rerun()

    if st.session_state.graph_state:
        state = st.session_state.graph_state

        st.divider()

        if debug:
            display_workflow_progress(state)

        if state.get("errors"):
            st.error("❌ Errors occurred:")
            for error in state["errors"]:
                st.error(f"  • {error}")

        if state.get("clarification_needed"):
            st.warning(f"⚠️ {state['clarification_needed']}")
            st.info("Please rephrase your query and try again.")
            return

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

        if state.get("geocoding_results"):
            with st.expander("🔍 All Geocoding Results (from Nominatim)", expanded=False):
                for location, results in state["geocoding_results"].items():
                    st.write(f"**{location}** — found {len(results)} variants:")

                    if not results:
                        st.warning("  ⚠️ No results found")
                        continue

                    for i, result in enumerate(results, 1):
                        selected = state.get("selected_locations", {}).get(location)
                        is_selected = selected and selected.place_id == result.place_id

                        if is_selected:
                            st.success(f"  ✅ **[SELECTED by AI]** #{i}: {result.display_name}")
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

        if state.get("selected_locations"):
            with st.expander("🌍 Selected Locations (after AI disambiguation)", expanded=False):
                for name, result in state["selected_locations"].items():
                    try:
                        display_name = result.display_name
                    except (AttributeError, UnicodeDecodeError):
                        display_name = "[Special characters]"
                    st.success(f"✓ {name} → {display_name}")

        if state.get("needs_user_input") and state.get("locations_with_points"):
            st.header("🎯 Buffer Configuration Required")

            st.warning(
                f"⚠️ {len(state['locations_with_points'])} location(s) don't have defined boundaries"
            )
            st.write("**Please specify buffer radius for each:**")

            buffer_decisions = {}

            for loc_data in state["locations_with_points"]:
                name = loc_data["name"]
                result = loc_data["result"]

                suggested_radius = state.get("buffer_decisions", {}).get(name, 1.0)

                col1, col2 = st.columns([2, 3])

                with col1:
                    st.write(f"**{name}**")
                    st.caption(f"Type: {result.place_type}")

                with col2:
                    radius = st.slider(
                        "Buffer radius (km)",
                        min_value=0.5,
                        max_value=20.0,
                        value=suggested_radius,
                        step=0.5,
                        key=f"buffer_{name}",
                        help=f"AI suggests: {suggested_radius} km",
                    )
                    buffer_decisions[name] = radius

            st.divider()

            if st.button(
                "✅ Confirm and Generate Polygon",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("🔗 Generating final polygon..."):
                    try:
                        final_result = resume_with_buffers(state, buffer_decisions)
                        st.session_state.graph_state = final_result
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        if debug:
                            import traceback
                            st.code(traceback.format_exc())

        if state.get("final_polygon") and state.get("current_step") == "complete":
            st.divider()
            st.header("🗺️ Final Result")

            poly_data = state["final_polygon"]
            metadata = poly_data["metadata"]

            num_regions = metadata.get("num_separate_regions", 1)
            is_disconnected = metadata.get("is_disconnected", False)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Area", f"{metadata['area_km2']:.2f} km²")
            with col2:
                st.metric("Locations", metadata["total_locations"])
            with col3:
                if is_disconnected:
                    st.metric("Separate Regions", num_regions, delta="⚠️ Disconnected", delta_color="off")
                else:
                    st.metric("Regions", num_regions, delta="✓ Connected", delta_color="normal")

            if is_disconnected:
                st.info(
                    f"ℹ️ Your result contains **{num_regions} separate regions** "
                    f"that don't share borders (e.g., cities far apart). "
                    f"See details below."
                )

                with st.expander("📍 Region Details", expanded=True):
                    for region_meta in metadata.get("regions", []):
                        col_a, col_b = st.columns([1, 3])
                        with col_a:
                            st.write(f"**Region {region_meta['region_number']}:**")
                        with col_b:
                            st.write(f"Area: {region_meta['area_km2']:.2f} km²")
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
                        "name": f"🔴 Final Region {i}",
                        "source": "final",
                    }
                    for i, geom in enumerate(geometry, 1)
                ]
            else:
                final_geoms = [
                    {
                        "geometry": geometry,
                        "name": "🔴 Final Combined Polygon",
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
                import urllib.parse

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


if __name__ == "__main__":
    main()
