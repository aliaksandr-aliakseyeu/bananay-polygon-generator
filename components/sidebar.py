"""
Sidebar Component with Info and Settings
"""

import streamlit as st
from .auth import render_auth_section
from src.config import config


def render_sidebar() -> bool:
    """
    Render sidebar with authentication, about, and settings

    Returns:
        bool: Debug mode status
    """
    with st.sidebar:
        render_auth_section()

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
            микрорайон Уручье-6 Минска + Колодищи в минском районе +
            деревня Сухорукие в минском районе
            ```

            ### How it works:

            1. 🤖 **LangChain** parses your query
            2. 🌍 **Nominatim** geocodes locations
            3. 🤖 **GPT-4** disambiguates results
            4. 📐 **Shapely** creates polygons
            5. 🗺️ **Folium** visualizes on map

            ### Tech Stack:

            - LangGraph for orchestration
            - OpenAI GPT-4 for NLP
            - OpenStreetMap Nominatim for geocoding
            - Shapely for geometric operations
            - Streamlit + Folium for UI
            """
        )

        st.divider()

        st.header("⚙️ Settings")
        debug = st.checkbox("🐛 Debug Mode", value=config.DEBUG, help="Show detailed processing steps")

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
