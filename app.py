"""
Polygon Generator - Main Application
Natural Language to Geographic Polygons
Powered by LangGraph, OpenAI, and OpenStreetMap

Refactored with modular components architecture
"""

import streamlit as st
import asyncio

from utils import setup_async
setup_async()

from components import (  # noqa: E402
    get_custom_css,
    initialize_session_state,
    render_header,
    render_sidebar,
    render_query_input,
    display_workflow_progress,
    display_errors_and_clarifications,
    display_parsed_query,
    display_geocoding_results,
    display_selected_locations,
    display_final_polygon,
    render_buffer_editor,
)
from src.orchestrator import process_query  # noqa: E402
from src.auth import log_request  # noqa: E402


st.set_page_config(
    page_title="Polygon Generator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.html(get_custom_css())


def main():
    """
    Main application logic

    Flow:
        1. Initialize session state
        2. Render header and sidebar
        3. Render query input form
        4. Process query (if submitted)
        5. Display results (intermediate or final)
        6. Handle buffer configuration (if needed)
    """

    initialize_session_state()
    render_header()
    debug = render_sidebar()

    st.divider()

    user_query, process_button = render_query_input()

    if not st.session_state.authenticated_user:
        if user_query.strip():
            st.info("⚠️ Please authenticate with your API key in the sidebar to use the service")
        return

    if process_button and user_query.strip():
        st.divider()
        st.session_state.processing = True

        user_data = st.session_state.authenticated_user
        request_success = False

        with st.spinner("🤖 LangGraph is processing your query..."):
            try:
                result = asyncio.run(process_query(user_query))
                st.session_state.graph_state = result
                request_success = True

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if debug:
                    import traceback
                    st.code(traceback.format_exc())
                request_success = False
                st.session_state.processing = False

            finally:
                try:
                    log_request(
                        user_id=user_data['user_id'],
                        query_text=user_query,
                        success=request_success,
                    )
                except Exception as log_error:
                    if debug:
                        st.warning(f"Failed to log request: {log_error}")

        st.session_state.processing = False
        st.rerun()

    if st.session_state.graph_state:
        state = st.session_state.graph_state

        st.divider()

        if debug:
            display_workflow_progress(state)

        needs_clarification = display_errors_and_clarifications(state)
        if needs_clarification:
            return

        display_parsed_query(state)
        display_geocoding_results(state)
        display_selected_locations(state)

        render_buffer_editor(state, debug)

        display_final_polygon(state, user_query, debug)


if __name__ == "__main__":
    main()
