"""
Buffer Configuration Editor Component
"""

import streamlit as st
import asyncio
from typing import Dict, Tuple, Optional

from src.orchestrator import resume_with_buffers


def render_buffer_editor(state: Dict, debug: bool = False) -> Tuple[bool, Optional[Dict[str, float]]]:
    """
    Render buffer radius editor for locations without boundaries

    Args:
        state: Current workflow state
        debug: Show debug information on errors

    Returns:
        tuple: (confirmed, buffer_decisions)
            - confirmed: True if user confirmed and generation succeeded
            - buffer_decisions: Dict of location names to radii (if confirmed)
    """
    if not (state.get("needs_user_input") and state.get("locations_with_points")):
        return False, None

    st.header("🎯 Buffer Configuration Required")

    st.warning(
        f"[!] {len(state['locations_with_points'])} location(s) don't have defined boundaries"
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
                final_result = asyncio.run(resume_with_buffers(state, buffer_decisions))
                st.session_state.graph_state = final_result
                st.rerun()
                return True, buffer_decisions
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if debug:
                    import traceback
                    st.code(traceback.format_exc())
                return False, None

    return False, None
