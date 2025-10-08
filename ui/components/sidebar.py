import streamlit as st
import requests
from config import API_URL
from components.auth import render_user_info

def render_sidebar():
    """Render the sidebar configuration panel"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Source type selection
        source_type = st.selectbox("📂 Source Type", ["confluence", "public"])
        
        # Configuration based on source type
        if source_type == "confluence":
            sync_config = render_confluence_config()
            can_sync = all([
                sync_config["confluence_base_url"],
                sync_config["confluence_username"], 
                sync_config["confluence_api_token"],
                sync_config["space_key_or_url"]
            ])
        else:
            sync_config = render_public_config()
            can_sync = bool(sync_config["space_key_or_url"].strip())
        
        # Sync button
        if st.button("🔄 Sync Documentation", use_container_width=True, disabled=not can_sync):
            handle_sync(sync_config)
        
        st.caption("📝 Syncing is optional - you can ask general questions without it")
        st.divider()
        
        # AI Settings
        ai_settings = render_ai_settings()
        st.divider()
        
        # Controls
        render_controls()
        
        # Admin panel link
        if "user_info" in st.session_state and st.session_state.user_info["user"]["role"] == "admin":
            if st.button("🛠️ Admin Panel", use_container_width=True, key="admin_panel_btn"):
                st.session_state.show_admin = True
                st.rerun()
        
        # User info
        render_user_info()
        
        return ai_settings

def render_confluence_config():
    """Render Confluence configuration form"""
    st.subheader("🔗 Confluence Settings")
    confluence_url = st.text_input("Base URL", placeholder="https://your-domain.atlassian.net/wiki")
    confluence_user = st.text_input("Username", placeholder="your.email@domain.com")
    confluence_token = st.text_input("API Token", type="password", placeholder="Your API token")
    space_key = st.text_input("Space Key", placeholder="SPACE")
    
    return {
        "source_type": "confluence",
        "space_key_or_url": space_key,
        "confluence_base_url": confluence_url,
        "confluence_username": confluence_user,
        "confluence_api_token": confluence_token
    }

def render_public_config():
    """Render public URL configuration form"""
    st.subheader("🌐 Public URL Settings")
    public_url = st.text_input("URL to Sync", placeholder="https://example.com/docs")
    
    return {
        "source_type": "public",
        "space_key_or_url": public_url
    }

def render_ai_settings():
    """Render AI model and search settings"""
    st.subheader("🤖 AI Settings")
    from config import MODEL_OPTIONS, SEARCH_TYPES
    
    selected_model = st.selectbox("Model", MODEL_OPTIONS)
    max_results = st.slider("Max Results", 1, 10, 5)
    search_type = st.radio("Search Type", SEARCH_TYPES)
    
    return {
        "model": selected_model,
        "max_results": max_results,
        "search_type": search_type
    }

def render_controls():
    """Render analytics and control buttons"""
    # Initialize analytics visibility state
    if "show_analytics" not in st.session_state:
        st.session_state.show_analytics = False
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Analytics"):
            st.session_state.show_analytics = not st.session_state.show_analytics
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()
    
    # Show/hide analytics based on state
    if st.session_state.show_analytics:
        try:
            headers = {}
            if "auth_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
            
            r = requests.get(f"{API_URL}/analytics", headers=headers)
            if r.status_code == 200:
                st.json(r.json())
            elif r.status_code == 401:
                st.error("Authentication required")
        except Exception as e:
            st.error(f"Failed: {e}")

def handle_sync(sync_config):
    """Handle document synchronization with authentication"""
    with st.spinner("Syncing documents..."):
        try:
            headers = {}
            if "auth_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
            
            r = requests.post(f"{API_URL}/sync", json=sync_config, headers=headers, timeout=60)
            
            if r.status_code == 401:
                st.error("❌ Authentication required")
                return
            elif r.status_code == 429:
                st.error("❌ Monthly quota exceeded")
                return
            
            r.raise_for_status()
            result = r.json()
            count = result.get('pages', result.get('chunks', 0))
            st.success(f"✅ Synced {count} documents for enhanced answers")
        except Exception as e:
            st.error(f"❌ Sync failed: {e}")