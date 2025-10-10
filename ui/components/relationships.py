"""
Relationship Visualization Component

This component provides UI for exploring relationships between:
- Tickets <-> Commits <-> Pull Requests
- Developers <-> Tickets
- Code Files <-> Tickets
- Feature Timelines
"""

import streamlit as st
import requests
from typing import Dict, List, Optional
from datetime import datetime
from config import API_URL


def render_relationships_page():
    """Render the relationships exploration page"""
    st.title("🔗 Knowledge Graph Explorer")
    st.caption("Explore relationships between tickets, commits, code, and developers")

    # Get auth token
    token = st.session_state.get("auth_token")
    if not token:
        st.error("Not authenticated")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎫 Ticket Relationships",
        "👨‍💻 Developer Contributions",
        "📁 File History",
        "📊 Repository Stats",
        "🔍 Search All"
    ])

    with tab1:
        render_ticket_relationships(headers)

    with tab2:
        render_developer_contributions(headers)

    with tab3:
        render_file_history(headers)

    with tab4:
        render_repository_stats(headers)

    with tab5:
        render_relationship_search(headers)


def render_ticket_relationships(headers: Dict):
    """Render ticket relationship view"""
    st.subheader("🎫 Ticket Relationships")
    st.caption("See all commits, PRs, code files, and developers related to a ticket")

    ticket_key = st.text_input(
        "Enter Ticket Key",
        placeholder="e.g., JIRA-123, SCRUM-45",
        key="ticket_rel_input"
    )

    if st.button("🔍 Explore Ticket", key="explore_ticket_btn"):
        if not ticket_key:
            st.warning("Please enter a ticket key")
            return

        with st.spinner(f"Loading relationships for {ticket_key}..."):
            try:
                r = requests.get(
                    f"{API_URL}/relationships/ticket/{ticket_key}",
                    headers=headers,
                    timeout=30
                )

                if r.status_code == 200:
                    data = r.json()
                    render_ticket_relationship_data(data)
                else:
                    st.error(f"Failed to load relationships: {r.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_ticket_relationship_data(data: Dict):
    """Render the relationship data for a ticket"""
    ticket_key = data.get("ticket_key", "Unknown")

    st.success(f"✅ Found relationships for {ticket_key}")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💾 Commits", len(data.get("commits", [])))
    with col2:
        st.metric("🔀 Pull Requests", len(data.get("pull_requests", [])))
    with col3:
        st.metric("📁 Code Files", len(data.get("code_files", [])))
    with col4:
        st.metric("👨‍💻 Developers", len(data.get("developers", [])))

    st.divider()

    # Timeline view
    if data.get("timeline"):
        with st.expander("📅 Timeline View", expanded=True):
            render_timeline(data["timeline"])

    # Developers
    if data.get("developers"):
        with st.expander(f"👨‍💻 Developers ({len(data['developers'])})", expanded=True):
            for dev in data["developers"]:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{dev.get('name', 'Unknown')}**")
                    st.caption(dev.get('email', ''))
                with col2:
                    st.write(f"📝 {dev.get('commit_count', 0)} commits")
                with col3:
                    st.write(f"➕{dev.get('lines_added', 0)} ➖{dev.get('lines_deleted', 0)}")

    # Commits
    if data.get("commits"):
        with st.expander(f"💾 Commits ({len(data['commits'])})", expanded=False):
            for commit in data["commits"][:20]:  # Show first 20
                render_commit_card(commit)

    # Pull Requests
    if data.get("pull_requests"):
        with st.expander(f"🔀 Pull Requests ({len(data['pull_requests'])})", expanded=False):
            for pr in data["pull_requests"]:
                render_pr_card(pr)

    # Code Files
    if data.get("code_files"):
        with st.expander(f"📁 Code Files ({len(data['code_files'])})", expanded=False):
            for file in data["code_files"][:50]:  # Show first 50
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.code(file.get('file_path', ''), language=None)
                with col2:
                    st.caption(f"Modified {file.get('modification_count', 0)} times")


def render_developer_contributions(headers: Dict):
    """Render developer contributions view"""
    st.subheader("👨‍💻 Developer Contributions")
    st.caption("See all contributions by a developer")

    developer_email = st.text_input(
        "Enter Developer Email",
        placeholder="developer@example.com",
        key="dev_contrib_input"
    )

    limit = st.slider("Max results", 10, 200, 100, key="dev_contrib_limit")

    if st.button("🔍 View Contributions", key="view_contrib_btn"):
        if not developer_email:
            st.warning("Please enter a developer email")
            return

        with st.spinner(f"Loading contributions for {developer_email}..."):
            try:
                r = requests.get(
                    f"{API_URL}/relationships/developer/{developer_email}",
                    params={"limit": limit},
                    headers=headers,
                    timeout=30
                )

                if r.status_code == 200:
                    data = r.json()
                    render_developer_contribution_data(data)
                else:
                    st.error(f"Failed to load contributions: {r.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_developer_contribution_data(data: Dict):
    """Render developer contribution data"""
    email = data.get("developer_email", "Unknown")
    stats = data.get("stats", {})

    st.success(f"✅ Contributions by {email}")

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💾 Commits", stats.get("total_commits", 0))
    with col2:
        st.metric("🔀 Pull Requests", stats.get("total_prs", 0))
    with col3:
        st.metric("🎫 Tickets", stats.get("total_tickets", 0))
    with col4:
        st.metric("📁 Files", stats.get("files_modified", 0))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("➕ Lines Added", f"{stats.get('lines_added', 0):,}")
    with col2:
        st.metric("➖ Lines Deleted", f"{stats.get('lines_deleted', 0):,}")

    st.divider()

    # Tickets worked on
    if data.get("tickets"):
        with st.expander(f"🎫 Tickets Worked On ({len(data['tickets'])})", expanded=True):
            # Display as pills
            ticket_html = " ".join([
                f'<span style="background-color: #e8f4f8; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block;">{ticket}</span>'
                for ticket in data["tickets"]
            ])
            st.markdown(ticket_html, unsafe_allow_html=True)

    # Recent commits
    if data.get("commits"):
        with st.expander(f"💾 Recent Commits ({len(data['commits'])})", expanded=False):
            for commit in data["commits"][:20]:
                render_commit_card(commit)

    # Recent PRs
    if data.get("pull_requests"):
        with st.expander(f"🔀 Recent Pull Requests ({len(data['pull_requests'])})", expanded=False):
            for pr in data["pull_requests"]:
                render_pr_card(pr)


def render_file_history(headers: Dict):
    """Render file history view"""
    st.subheader("📁 File History")
    st.caption("See complete history of a code file")

    file_path = st.text_input(
        "Enter File Path",
        placeholder="src/main.py",
        key="file_history_input"
    )

    if st.button("🔍 View History", key="view_file_history_btn"):
        if not file_path:
            st.warning("Please enter a file path")
            return

        with st.spinner(f"Loading history for {file_path}..."):
            try:
                r = requests.get(
                    f"{API_URL}/relationships/file",
                    params={"file_path": file_path},
                    headers=headers,
                    timeout=30
                )

                if r.status_code == 200:
                    data = r.json()
                    render_file_history_data(data)
                else:
                    st.error(f"Failed to load file history: {r.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_file_history_data(data: Dict):
    """Render file history data"""
    file_path = data.get("file_path", "Unknown")
    total_commits = data.get("total_commits", 0)

    st.success(f"✅ History for {file_path}")
    st.metric("💾 Total Commits", total_commits)

    # First and last commit
    if data.get("first_commit") and data.get("last_commit"):
        col1, col2 = st.columns(2)
        with col1:
            st.caption("**First Commit**")
            first = data["first_commit"]
            st.write(f"{first.get('author_name', 'Unknown')} - {format_date(first.get('commit_date'))}")
        with col2:
            st.caption("**Last Commit**")
            last = data["last_commit"]
            st.write(f"{last.get('author_name', 'Unknown')} - {format_date(last.get('commit_date'))}")

    st.divider()

    # Developers
    if data.get("developers"):
        with st.expander(f"👨‍💻 Developers ({len(data['developers'])})", expanded=True):
            for dev in data["developers"]:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{dev.get('name', 'Unknown')}**")
                with col2:
                    st.write(f"📝 {dev.get('commit_count', 0)} commits")
                with col3:
                    st.write(f"➕{dev.get('lines_added', 0)} ➖{dev.get('lines_deleted', 0)}")

    # Related tickets
    if data.get("tickets"):
        with st.expander(f"🎫 Related Tickets ({len(data['tickets'])})", expanded=True):
            ticket_html = " ".join([
                f'<span style="background-color: #e8f4f8; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block;">{ticket}</span>'
                for ticket in data["tickets"]
            ])
            st.markdown(ticket_html, unsafe_allow_html=True)

    # Commit history
    if data.get("commits"):
        with st.expander(f"💾 Commit History ({len(data['commits'])})", expanded=False):
            for commit in data["commits"][:50]:
                render_commit_card(commit)


def render_repository_stats(headers: Dict):
    """Render repository statistics view"""
    st.subheader("📊 Repository Statistics")
    st.caption("See comprehensive stats for a repository")

    # Get list of repositories
    try:
        r = requests.get(f"{API_URL}/repositories", headers=headers, timeout=10)
        if r.status_code == 200:
            repos = r.json().get("repositories", [])
            if repos:
                repo_options = {f"{repo['repo_name']} ({repo['provider']})": repo['id'] for repo in repos}
                selected = st.selectbox("Select Repository", list(repo_options.keys()), key="repo_stats_select")

                if st.button("📊 View Stats", key="view_repo_stats_btn"):
                    repo_id = repo_options[selected]
                    with st.spinner("Loading repository statistics..."):
                        try:
                            r = requests.get(
                                f"{API_URL}/relationships/repository/{repo_id}/stats",
                                headers=headers,
                                timeout=30
                            )

                            if r.status_code == 200:
                                data = r.json()
                                render_repository_stats_data(data)
                            else:
                                st.error(f"Failed to load stats: {r.status_code}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            else:
                st.info("No repositories synced yet. Sync a repository first!")
        else:
            st.error("Failed to load repositories")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def render_repository_stats_data(data: Dict):
    """Render repository stats data"""
    repo = data.get("repository", {})
    commit_stats = data.get("commit_stats", {})
    pr_stats = data.get("pr_stats", {})

    st.success(f"✅ Statistics for {repo.get('repo_name', 'Unknown')}")
    st.caption(repo.get('repo_url', ''))

    # Commit stats
    st.subheader("💾 Commit Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Commits", commit_stats.get("total_commits", 0))
    with col2:
        st.metric("Contributors", commit_stats.get("unique_authors", 0))
    with col3:
        st.metric("Lines Added", f"{commit_stats.get('total_additions', 0):,}")
    with col4:
        st.metric("Lines Deleted", f"{commit_stats.get('total_deletions', 0):,}")

    if commit_stats.get("first_commit_date") and commit_stats.get("last_commit_date"):
        col1, col2 = st.columns(2)
        with col1:
            st.caption("**First Commit**")
            st.write(format_date(commit_stats.get("first_commit_date")))
        with col2:
            st.caption("**Last Commit**")
            st.write(format_date(commit_stats.get("last_commit_date")))

    st.divider()

    # PR stats
    st.subheader("🔀 Pull Request Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total PRs", pr_stats.get("total_prs", 0))
    with col2:
        st.metric("Merged", pr_stats.get("merged_prs", 0))
    with col3:
        st.metric("Open", pr_stats.get("open_prs", 0))
    with col4:
        st.metric("Closed", pr_stats.get("closed_prs", 0))

    st.divider()

    # Top contributors
    if data.get("top_contributors"):
        st.subheader("👨‍💻 Top Contributors")
        for contrib in data["top_contributors"][:10]:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.write(f"**{contrib.get('author_name', 'Unknown')}**")
                st.caption(contrib.get('author_email', ''))
            with col2:
                st.write(f"📝 {contrib.get('commit_count', 0)}")
            with col3:
                st.write(f"➕ {contrib.get('lines_added', 0):,}")
            with col4:
                st.write(f"➖ {contrib.get('lines_deleted', 0):,}")

    # Related tickets
    if data.get("related_tickets"):
        st.divider()
        st.subheader(f"🎫 Related Tickets ({len(data['related_tickets'])})")
        ticket_html = " ".join([
            f'<span style="background-color: #e8f4f8; padding: 4px 8px; border-radius: 4px; margin: 2px; display: inline-block;">{ticket}</span>'
            for ticket in data["related_tickets"][:50]
        ])
        st.markdown(ticket_html, unsafe_allow_html=True)


def render_relationship_search(headers: Dict):
    """Render cross-entity search"""
    st.subheader("🔍 Search All Entities")
    st.caption("Search across commits, PRs, tickets, files, and documents")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="Enter search term...",
            key="rel_search_query"
        )
    with col2:
        entity_types = st.multiselect(
            "Entity Types",
            ["commits", "prs", "tickets", "files"],
            default=["commits", "prs", "tickets", "files"],
            key="rel_search_types"
        )

    if st.button("🔍 Search", key="rel_search_btn"):
        if not query:
            st.warning("Please enter a search query")
            return

        with st.spinner("Searching..."):
            try:
                r = requests.get(
                    f"{API_URL}/relationships/search",
                    params={
                        "query": query,
                        "entity_types": ",".join(entity_types)
                    },
                    headers=headers,
                    timeout=30
                )

                if r.status_code == 200:
                    data = r.json()
                    render_search_results(data)
                else:
                    st.error(f"Search failed: {r.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_search_results(data: Dict):
    """Render search results"""
    st.success(f"✅ Search results for: {data.get('query', '')}")

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💾 Commits", len(data.get("commits", [])))
    with col2:
        st.metric("🔀 Pull Requests", len(data.get("pull_requests", [])))
    with col3:
        st.metric("🎫 Tickets", len(data.get("tickets", [])))
    with col4:
        st.metric("📁 Files", len(data.get("files", [])))

    # Commits
    if data.get("commits"):
        with st.expander(f"💾 Commits ({len(data['commits'])})", expanded=True):
            for commit in data["commits"]:
                render_commit_card(commit)

    # Pull Requests
    if data.get("pull_requests"):
        with st.expander(f"🔀 Pull Requests ({len(data['pull_requests'])})", expanded=True):
            for pr in data["pull_requests"]:
                render_pr_card(pr)

    # Tickets
    if data.get("tickets"):
        with st.expander(f"🎫 Tickets ({len(data['tickets'])})", expanded=True):
            for ticket in data["tickets"]:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{ticket.get('ticket_key', '')}**")
                    st.caption(ticket.get('summary', ''))
                with col2:
                    st.write(ticket.get('status', ''))
                with col3:
                    st.write(format_date(ticket.get('created')))

    # Files
    if data.get("files"):
        with st.expander(f"📁 Files ({len(data['files'])})", expanded=True):
            for file in data["files"]:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.code(file.get('file_path', ''), language=None)
                with col2:
                    st.caption(file.get('language', ''))
                with col3:
                    st.caption(f"{file.get('commit_count', 0)} commits")


# Helper rendering functions

def render_commit_card(commit: Dict):
    """Render a commit card"""
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.code(f"💾 {commit.get('sha', 'Unknown')[:7]}", language=None)
            st.write(commit.get('message', '').split('\n')[0][:100])
            st.caption(f"👤 {commit.get('author_name', 'Unknown')} • {format_date(commit.get('commit_date'))}")

            # Show ticket references
            if commit.get('ticket_references'):
                ticket_html = " ".join([
                    f'<span style="background-color: #fff4e6; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 4px;">{ticket}</span>'
                    for ticket in commit['ticket_references']
                ])
                st.markdown(ticket_html, unsafe_allow_html=True)
        with col2:
            if commit.get('additions') is not None and commit.get('deletions') is not None:
                st.caption(f"➕ {commit['additions']}")
                st.caption(f"➖ {commit['deletions']}")
        st.divider()


def render_pr_card(pr: Dict):
    """Render a PR card"""
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            state_emoji = "✅" if pr.get('state') == 'merged' else ("🟢" if pr.get('state') == 'open' else "⭕")
            st.write(f"{state_emoji} **PR #{pr.get('pr_number', '')}**: {pr.get('title', '')}")
            if pr.get('description'):
                st.caption(pr['description'][:150] + "..." if len(pr.get('description', '')) > 150 else pr.get('description', ''))
            st.caption(f"👤 {pr.get('author_name', 'Unknown')} • {format_date(pr.get('created_at_pr'))}")

            # Show ticket references
            if pr.get('ticket_references'):
                ticket_html = " ".join([
                    f'<span style="background-color: #fff4e6; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 4px;">{ticket}</span>'
                    for ticket in pr['ticket_references']
                ])
                st.markdown(ticket_html, unsafe_allow_html=True)
        with col2:
            st.caption(pr.get('state', 'unknown').upper())
        st.divider()


def render_timeline(timeline: List[Dict]):
    """Render a timeline of events"""
    if not timeline:
        st.info("No timeline events")
        return

    for event in timeline:
        event_type = event.get('type', 'unknown')
        timestamp = format_date(event.get('timestamp'))

        # Icon based on type
        icon_map = {
            'commit': '💾',
            'pull_request': '🔀',
            'pr_merged': '✅',
            'ticket_created': '🎫',
            'document': '📄'
        }
        icon = icon_map.get(event_type, '📌')

        col1, col2 = st.columns([1, 5])
        with col1:
            st.caption(timestamp)
        with col2:
            st.write(f"{icon} **{event.get('title', '')}**")
            if event.get('author'):
                st.caption(f"👤 {event['author']}")
            if event.get('description'):
                with st.expander("Details"):
                    st.write(event['description'])


def format_date(date_str) -> str:
    """Format a date string for display"""
    if not date_str:
        return "Unknown"

    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = date_str
        return dt.strftime("%b %d, %Y %H:%M")
    except:
        return str(date_str)
