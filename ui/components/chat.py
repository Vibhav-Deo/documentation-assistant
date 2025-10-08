import streamlit as st
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
from config import API_URL

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

def render_chat_header():
    """Render chat interface header"""
    st.title("🤖 AI Assistant")
    st.caption("Ask general questions or sync documentation for specific answers")

def display_chat_messages():
    """Display existing chat messages"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📚 Sources"):
                    for source in message["sources"]:
                        st.write(f"• {source}")

def check_document_status():
    """Check if documents are synced and show info"""
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            doc_count = health_data.get("analytics", {}).get("total_queries", 0)
            has_docs = doc_count > 0 or health_data.get("collections_count", 0) > 0
        else:
            has_docs = False
    except:
        has_docs = False

    if not has_docs:
        st.info("💡 No documents synced yet. You can ask general questions or sync documentation for specific answers.")

def handle_user_input(ai_settings):
    """Handle user input and generate AI response"""
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = get_ai_response(prompt, ai_settings)
                    
                    answer = response.get("answer", "No answer returned")
                    sources = response.get("sources", [])
                    
                    st.markdown(answer)
                    
                    # Store session ID
                    if "session_id" in response:
                        st.session_state.session_id = response["session_id"]
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "sources": sources
                    })
                    
                    # Show sources
                    if sources:
                        with st.expander("📚 Sources"):
                            for source in sources:
                                st.write(f"• {source}")
                                
                except ConnectionError:
                    st.error("❌ Cannot connect to API service")
                except Timeout:
                    st.error("⏱️ Request timed out")
                except requests.HTTPError as e:
                    st.error(f"❌ HTTP error {e.response.status_code}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

def get_ai_response(prompt, ai_settings):
    """Get AI response from API with authentication"""
    payload = {
        "question": prompt,
        "session_id": st.session_state.session_id,
        **ai_settings
    }
    
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
    
    r = requests.post(f"{API_URL}/ask", json=payload, headers=headers, timeout=60)
    
    if r.status_code == 401:
        raise Exception("Authentication required")
    elif r.status_code == 429:
        raise Exception("Monthly quota exceeded")
    
    r.raise_for_status()
    return r.json()

def render_chat_interface(ai_settings):
    """Render the complete chat interface"""
    initialize_session_state()
    render_chat_header()
    display_chat_messages()
    check_document_status()
    handle_user_input(ai_settings)