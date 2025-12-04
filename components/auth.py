"""
Authentication Section Component
"""

import streamlit as st
from src.auth import authenticate_request, get_user_stats


def render_auth_section():
    """
    Render authentication section in sidebar

    Features:
        - API key input
        - Authentication status
        - Usage statistics
        - Progress bar
        - User metrics
    """
    st.header("🔐 Authentication")

    api_key_input = st.text_input(
        "API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-polygon-...",
        help="Enter your API key to use the service"
    )

    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.authenticated_user = None

    if api_key_input:
        is_auth, user_data, error_msg = authenticate_request(api_key_input)

        if is_auth:
            st.session_state.authenticated_user = user_data
            st.success(f"✅ Authenticated as: **{user_data['username']}**")

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Requests Used",
                    f"{user_data['requests_used']}/{user_data['daily_limit']}",
                    delta=f"-{user_data['requests_remaining']} left"
                )
            with col2:
                progress = user_data['requests_used'] / user_data['daily_limit']
                st.metric(
                    "Usage",
                    f"{progress * 100:.0f}%"
                )

            st.progress(progress)

            try:
                stats = get_user_stats(user_data['user_id'])
                with st.expander("📊 Usage Statistics"):
                    st.write(f"**Total requests (all time):** {stats['total_requests']}")
                    st.write(f"**Requests today:** {stats['requests_today']}")
                    st.write(f"**Last 24 hours:** {stats['requests_last_24h']}")
                    if stats['last_request_time']:
                        last_req = stats['last_request_time'].strftime('%Y-%m-%d %H:%M:%S')
                        st.write(f"**Last request:** {last_req}")
            except Exception:
                pass

        else:
            st.session_state.authenticated_user = None
            st.error(f"❌ {error_msg}")
    else:
        st.session_state.authenticated_user = None
        st.warning("⚠️ Please enter your API key to use the service")

    st.divider()
