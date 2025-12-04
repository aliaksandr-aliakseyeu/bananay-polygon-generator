"""
Query Input Component
"""

import streamlit as st


def render_query_input() -> tuple[str, bool]:
    """
    Render query input form with process button
    
    Returns:
        tuple: (user_query, process_button_clicked)
    """
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
        is_disabled = (
            not user_query.strip() or
            st.session_state.processing or
            not st.session_state.authenticated_user
        )

        process_button = st.button(
            "🚀 Generate Polygon",
            type="primary",
            disabled=is_disabled,
            use_container_width=True,
        )

        if not st.session_state.authenticated_user and user_query.strip():
            st.caption("⚠️ Please authenticate with your API key in the sidebar")

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

    return user_query, process_button


