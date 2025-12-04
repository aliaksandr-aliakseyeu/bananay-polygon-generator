"""
Workflow Progress Display Component
"""

import streamlit as st


def display_workflow_progress(state: dict):
    """
    Display current workflow step with icon and text

    Args:
        state: LangGraph workflow state dictionary
    """
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
