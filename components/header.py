"""
Application Header Component
"""

import streamlit as st


def render_header():
    """
    Render the main application header

    Displays:
        - Application title with icon
        - Subtitle with description
    """
    st.markdown(
        '<div class="main-header">🗺️ Polygon Generator</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">Natural language to geographic polygons • Powered by LangGraph</div>',
        unsafe_allow_html=True,
    )
