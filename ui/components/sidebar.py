import streamlit as st
import requests
from config import API_URL

def render_sidebar():
    """Render the sidebar configuration panel"""
    with st.sidebar:
        st.header("📥 Data Sources")

        # Tabs for different data sources
        tab1, tab2, tab3 = st.tabs(["📄 Docs", "🎫 Jira", "💻 Code"])

        with tab1:
            # Confluence only for internal documentation
            sync_config = render_confluence_config()
            can_sync = all([
                sync_config["confluence_base_url"],
                sync_config["confluence_username"],
                sync_config["confluence_api_token"],
                sync_config["space_key_or_url"]
            ])

            # Sync button
            if st.button("🔄 Sync Confluence Documentation", use_container_width=True, disabled=not can_sync):
                handle_sync(sync_config)

            st.caption("💡 Sync internal Confluence docs to answer questions about your team's documentation")

        with tab2:
            render_jira_sync()

        with tab3:
            render_repository_sync()

        st.divider()
        
        # AI Settings
        ai_settings = render_ai_settings()
        st.divider()
        
        # Controls
        render_controls()

        # Knowledge Graph Explorer
        if st.button("🔗 Knowledge Graph", use_container_width=True, key="relationships_btn"):
            st.session_state.show_relationships = True
            st.rerun()

        # Decision Analysis (Phase 8a: IntentAnalyzer)
        if st.button("🧠 Decision Analysis", use_container_width=True, key="decisions_btn"):
            st.session_state.show_decisions = True
            st.rerun()

        # Admin panel link
        if "user_info" in st.session_state and st.session_state.user_info["user"]["role"] == "admin":
            if st.button("🛠️ Admin Panel", use_container_width=True, key="admin_panel_btn"):
                st.session_state.show_admin = True
                st.rerun()

        # User info
        from components.auth import render_user_info
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
            elif r.status_code >= 400:
                # Extract error detail from API response
                try:
                    error_detail = r.json().get('detail', 'Unknown error')
                    st.error(f"❌ Sync failed: {error_detail}")
                except:
                    st.error(f"❌ Sync failed: HTTP {r.status_code}")
                return

            result = r.json()
            count = result.get('pages', result.get('chunks', 0))
            st.success(f"✅ Synced {count} documents for enhanced answers")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Sync failed: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

def render_jira_sync():
    """Render Jira synchronization panel"""
    st.subheader("🎫 Jira Integration")

    jira_server = st.text_input(
        "Jira Server",
        placeholder="https://your-domain.atlassian.net",
        key="jira_server"
    )
    jira_email = st.text_input(
        "Email",
        placeholder="your.email@company.com",
        key="jira_email"
    )
    jira_token = st.text_input(
        "API Token",
        type="password",
        placeholder="Your Jira API token",
        key="jira_token"
    )
    jira_project = st.text_input(
        "Project Key",
        placeholder="PROJ",
        key="jira_project"
    )

    can_sync_jira = all([jira_server, jira_email, jira_token, jira_project])

    if st.button("🔄 Sync Jira Project", use_container_width=True, disabled=not can_sync_jira):
        with st.spinner("Syncing Jira tickets..."):
            try:
                headers = {}
                if "auth_token" in st.session_state:
                    headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

                response = requests.post(
                    f"{API_URL}/sync/jira",
                    json={
                        "server": jira_server,
                        "email": jira_email,
                        "api_token": jira_token,
                        "project_key": jira_project
                    },
                    headers=headers,
                    timeout=120
                )

                if response.status_code == 401:
                    st.error("❌ Authentication failed - check Jira credentials")
                    return
                elif response.status_code == 429:
                    st.error("❌ Monthly quota exceeded")
                    return
                elif response.status_code >= 400:
                    # Extract error detail from API response
                    try:
                        error_detail = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Jira sync failed: {error_detail}")
                    except:
                        st.error(f"❌ Jira sync failed: HTTP {response.status_code}")
                    return

                result = response.json()

                # Show dual storage metrics if available
                if result.get('dual_storage'):
                    st.success(f"✅ Synced {result['tickets_synced']} tickets from {result['project_key']}")
                    st.info(f"🔍 Indexed {result.get('tickets_indexed', 0)} tickets for semantic search")
                else:
                    st.success(f"✅ Synced {result['tickets_synced']} tickets from {result['project_key']}")

                st.session_state.show_jira_tickets = True

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Network error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

    # Button to view/hide synced tickets
    st.divider()
    if st.button("📋 View Synced Tickets", use_container_width=True):
        st.session_state.show_jira_tickets = not st.session_state.get("show_jira_tickets", False)

    # Show synced tickets
    if st.session_state.get("show_jira_tickets", False):
        try:
            headers = {}
            if "auth_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

            response = requests.get(
                f"{API_URL}/jira/tickets?limit=10",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                st.write(f"**Total Tickets**: {data['count']}")

                for ticket in data['tickets'][:5]:
                    with st.expander(f"{ticket['ticket_key']}: {ticket['summary']}"):
                        st.write(f"**Status**: {ticket['status']}")
                        st.write(f"**Type**: {ticket['issue_type']}")
                        if ticket.get('assignee'):
                            st.write(f"**Assignee**: {ticket['assignee']}")
        except Exception as e:
            st.error(f"Failed to load tickets: {str(e)}")

    st.caption("💡 Sync Jira tickets to answer questions about your project management")

def render_repository_sync():
    """Render Repository synchronization panel"""
    st.subheader("💻 Repository Integration")

    provider = st.selectbox(
        "Provider",
        ["github", "gitlab", "bitbucket"],
        key="repo_provider"
    )

    repo_url = st.text_input(
        "Repository URL",
        placeholder="https://github.com/owner/repo",
        key="repo_url"
    )

    access_token = st.text_input(
        "Access Token",
        type="password",
        placeholder="Your personal access token",
        key="repo_token",
        help="Generate token at: GitHub Settings → Developer settings → Personal access tokens"
    )

    branch = st.text_input(
        "Branch",
        value="main",
        key="repo_branch"
    )

    can_sync_repo = all([provider, repo_url, access_token])

    if st.button("🔄 Sync Repository", use_container_width=True, disabled=not can_sync_repo):
        with st.spinner("Syncing repository files..."):
            try:
                headers = {}
                if "auth_token" in st.session_state:
                    headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

                response = requests.post(
                    f"{API_URL}/sync/repository",
                    json={
                        "provider": provider,
                        "repo_url": repo_url,
                        "access_token": access_token,
                        "branch": branch
                    },
                    headers=headers,
                    timeout=180  # 3 minutes for repo sync
                )

                if response.status_code == 401:
                    st.error("❌ Authentication failed - check repository credentials")
                    return
                elif response.status_code == 429:
                    st.error("❌ Monthly quota exceeded")
                    return
                elif response.status_code >= 400:
                    try:
                        error_detail = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Repository sync failed: {error_detail}")
                    except:
                        st.error(f"❌ Repository sync failed: HTTP {response.status_code}")
                    return

                result = response.json()

                st.success(f"✅ Synced {result['repo_name']} ({result['provider']})")
                st.write(f"- 📄 {result['files_synced']} code files")
                st.write(f"- 💾 {result.get('commits_synced', 0)} commits")
                st.write(f"- 🔀 {result.get('prs_synced', 0)} pull requests")

                # Show dual storage metrics if available
                if result.get('dual_storage'):
                    st.info(f"🔍 **Dual Storage Active:**")
                    st.write(f"  - {result.get('files_indexed', 0)} files indexed for semantic search")
                    st.write(f"  - {result.get('commits_indexed', 0)} commits indexed for semantic search")

                st.session_state.show_repo_files = True

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Network error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")

    # Button to view/hide synced repositories
    st.divider()
    if st.button("📁 View Synced Repositories", use_container_width=True):
        st.session_state.show_repositories = not st.session_state.get("show_repositories", False)

    # Show synced repositories
    if st.session_state.get("show_repositories", False):
        try:
            headers = {}
            if "auth_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

            response = requests.get(
                f"{API_URL}/repositories",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                st.write(f"**Total Repositories**: {data['count']}")

                for repo in data['repositories'][:5]:
                    with st.expander(f"{repo['repo_name']} ({repo['provider']})"):
                        st.write(f"**URL**: {repo['repo_url']}")
                        st.write(f"**Branch**: {repo['branch']}")
                        st.write(f"**Files**: {repo['file_count']}")
                        if repo.get('last_synced'):
                            st.write(f"**Last Synced**: {repo['last_synced']}")
        except Exception as e:
            st.error(f"Failed to load repositories: {str(e)}")

    st.caption("💡 Sync code repositories to answer questions about your codebase")