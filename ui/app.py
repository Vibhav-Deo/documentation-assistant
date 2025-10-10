import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat_interface
from components.auth import render_login_page, check_authentication
from components.admin import render_admin_panel
from components.relationships import render_relationships_page

# Page configuration
st.set_page_config(
    page_title="Documentation Assistant",
    page_icon="🤖",
    layout="wide"
)

def main():
    """Main application entry point"""
    # Initialize session state from browser storage if available
    if "auth_token" not in st.session_state:
        # Try to restore from query params (for development)
        try:
            query_params = st.query_params
            if "token" in query_params:
                st.session_state.auth_token = query_params["token"]
        except Exception:
            # Ignore query params if not available
            pass
    
    # Check authentication
    if not check_authentication():
        render_login_page()
        return
    
    # Check if admin panel should be shown
    if st.session_state.get("show_admin", False):
        if st.button("← Back to Chat"):
            st.session_state.show_admin = False
            st.rerun()
        render_admin_panel()
        return

    # Check if relationships page should be shown
    if st.session_state.get("show_relationships", False):
        if st.button("← Back to Chat"):
            st.session_state.show_relationships = False
            st.rerun()
        render_relationships_page()
        return

    # Render sidebar and get AI settings
    ai_settings = render_sidebar()

    # Render main chat interface
    render_chat_interface(ai_settings)

if __name__ == "__main__":
    main()