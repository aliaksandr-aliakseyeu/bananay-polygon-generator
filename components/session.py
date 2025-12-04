"""
Session State Management
"""

import streamlit as st


def initialize_session_state():
    """
    Initialize all session state variables with default values

    Session state variables:
        - graph_state: Current LangGraph workflow state
        - processing: Whether a query is currently being processed
        - authenticated_user: Current authenticated user data
        - api_key: User's API key for authentication
    """
    if "graph_state" not in st.session_state:
        st.session_state.graph_state = None

    if "processing" not in st.session_state:
        st.session_state.processing = False

    if "authenticated_user" not in st.session_state:
        st.session_state.authenticated_user = None

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
