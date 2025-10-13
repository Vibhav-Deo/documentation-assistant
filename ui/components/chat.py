import streamlit as st
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
from config import API_URL
import re

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    # Initialize source filters (Phase 7 UI Enhancement)
    if "filter_confluence" not in st.session_state:
        st.session_state.filter_confluence = True
    if "filter_jira" not in st.session_state:
        st.session_state.filter_jira = True
    if "filter_git" not in st.session_state:
        st.session_state.filter_git = True
    if "filter_code" not in st.session_state:
        st.session_state.filter_code = True

def render_chat_header():
    """Render chat interface header"""
    st.title("🤖 AI Assistant")
    st.caption("Ask general questions or sync documentation for specific answers")

    # Source filtering (Phase 7 UI Enhancement)
    with st.expander("🎯 Filter Sources", expanded=False):
        st.caption("Select which sources to include in answers")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.session_state.filter_confluence = st.checkbox("📄 Confluence", value=st.session_state.filter_confluence)

        with col2:
            st.session_state.filter_jira = st.checkbox("🎫 Jira", value=st.session_state.filter_jira)

        with col3:
            st.session_state.filter_git = st.checkbox("💻 Git", value=st.session_state.filter_git)

        with col4:
            st.session_state.filter_code = st.checkbox("📝 Code", value=st.session_state.filter_code)

def display_chat_messages():
    """Display existing chat messages with source badges (Phase 7 Enhancement)"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Display answer with source badges
            if message["role"] == "assistant":
                # Render answer content
                st.markdown(message["content"])

                # Show source badges if available
                if "source_metadata" in message:
                    render_source_badges(message["source_metadata"])

                # Show detailed sources
                if "sources" in message and message["sources"]:
                    with st.expander("📚 View All Sources"):
                        for source in message["sources"]:
                            st.write(f"• {source}")
            else:
                st.markdown(message["content"])

def render_source_badges(source_metadata):
    """Render source type badges with counts (Phase 7 Enhancement)"""
    if not source_metadata:
        return

    st.markdown("**Sources:**")
    cols = st.columns(4)

    # Confluence badge
    if source_metadata.get("confluence_count", 0) > 0:
        with cols[0]:
            st.markdown(f"📄 **Confluence** `{source_metadata['confluence_count']}`")

    # Jira badge
    if source_metadata.get("jira_count", 0) > 0:
        with cols[1]:
            st.markdown(f"🎫 **Jira** `{source_metadata['jira_count']}`")

    # Git badge
    if source_metadata.get("git_count", 0) > 0:
        with cols[2]:
            st.markdown(f"💻 **Git** `{source_metadata['git_count']}`")

    # Code badge
    if source_metadata.get("code_count", 0) > 0:
        with cols[3]:
            st.markdown(f"📝 **Code** `{source_metadata['code_count']}`")

def extract_source_metadata(response):
    """Extract source counts from API response for badges (Phase 7 Enhancement)"""
    metadata = {
        "confluence_count": 0,
        "jira_count": 0,
        "git_count": 0,
        "code_count": 0
    }

    # Count sources from the answer content (looking for [DOC-X], [TICKET-X], etc.)
    answer = response.get("answer", "")

    # Count Confluence references
    metadata["confluence_count"] = len(re.findall(r'\[DOC-\d+\]', answer))

    # Count Jira references
    metadata["jira_count"] = len(re.findall(r'\[TICKET-\d+\]', answer))

    # Count Git commit references
    metadata["git_count"] = len(re.findall(r'\[COMMIT-\d+\]', answer))

    # Count Code file references
    metadata["code_count"] = len(re.findall(r'\[CODE-\d+\]', answer))

    return metadata

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
                    # Pass source filters to API (Phase 7 Enhancement)
                    response = get_ai_response(prompt, ai_settings)

                    answer = response.get("answer", "No answer returned")
                    sources = response.get("sources", [])

                    # Extract source metadata for badges (Phase 7 Enhancement)
                    source_metadata = extract_source_metadata(response)

                    st.markdown(answer)

                    # Render source badges
                    render_source_badges(source_metadata)

                    # Store session ID
                    if "session_id" in response:
                        st.session_state.session_id = response["session_id"]

                    # Add assistant message with metadata
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "source_metadata": source_metadata
                    })

                    # Show detailed sources
                    if sources:
                        with st.expander("📚 View All Sources"):
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
    """Get AI response from API with authentication and source filters"""
    # Build payload with source filters (Phase 7 Enhancement)
    payload = {
        "question": prompt,
        "session_id": st.session_state.session_id,
        **ai_settings
    }

    # Add source filters to payload
    source_filters = {
        "include_confluence": st.session_state.get("filter_confluence", True),
        "include_jira": st.session_state.get("filter_jira", True),
        "include_git": st.session_state.get("filter_git", True),
        "include_code": st.session_state.get("filter_code", True)
    }
    payload.update(source_filters)

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
