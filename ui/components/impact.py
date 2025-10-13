"""
Impact Analysis UI Component

Predicts the impact of changes:
- File impact (what breaks if we change this?)
- Ticket impact (scope estimation)
- Commit impact (risk assessment)
- Reviewer suggestions

Helps prevent breaking changes and plan work better.
"""

import streamlit as st
import requests
import json

API_URL = "http://api:4000"


def render_impact_page():
    """Render the Impact Analysis page"""
    st.title("🎯 Impact Analysis")
    st.caption("Predict the impact of changes before they happen")

    # Check authentication
    if "auth_token" not in st.session_state:
        st.warning("⚠️ Please log in to use impact analysis")
        return

    # Analysis type selector
    analysis_type = st.radio(
        "Select Analysis Type:",
        ["📄 File Impact", "🎫 Ticket Impact", "💻 Commit Impact", "👥 Suggest Reviewers"],
        horizontal=True
    )

    st.divider()

    if analysis_type == "📄 File Impact":
        render_file_impact_tab()
    elif analysis_type == "🎫 Ticket Impact":
        render_ticket_impact_tab()
    elif analysis_type == "💻 Commit Impact":
        render_commit_impact_tab()
    else:
        render_reviewer_suggestions_tab()


def render_file_impact_tab():
    """Render file impact analysis"""
    st.subheader("File Impact Analysis")
    st.caption("Analyze what would be affected if you change a specific file")

    # Input
    file_path = st.text_input(
        "File Path:",
        placeholder="e.g., src/auth/oauth.ts",
        help="Enter the path to the file you want to analyze"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_btn = st.button("🔍 Analyze Impact", type="primary")

    if analyze_btn and file_path:
        with st.spinner(f"Analyzing impact of changing {file_path}..."):
            result = analyze_file_impact(file_path)

        if result:
            display_file_impact_results(result)
    elif analyze_btn:
        st.warning("Please enter a file path")


def display_file_impact_results(result):
    """Display file impact analysis results"""
    st.success(f"✅ Analysis complete for: {result.get('file_path')}")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Commits", result.get("total_commits", 0))
    with col2:
        st.metric("Related Tickets", len(result.get("related_tickets", [])))
    with col3:
        st.metric("Top Developers", len(result.get("top_developers", [])))
    with col4:
        st.metric("Co-changed Files", len(result.get("frequently_changed_with", [])))

    st.divider()

    # Tabbed results
    tabs = st.tabs(["🎫 Related Tickets", "👥 Developers", "📁 Co-changed Files", "📜 Recent Commits"])

    with tabs[0]:
        st.markdown("### Related Tickets")
        tickets = result.get("related_tickets", [])
        if tickets:
            for ticket in tickets:
                with st.expander(f"🎫 {ticket['ticket_key']}: {ticket['summary']}", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Status:** {ticket.get('status', 'Unknown')}")
                    with col2:
                        st.markdown(f"**Priority:** {ticket.get('priority', 'Unknown')}")
        else:
            st.info("No related tickets found")

    with tabs[1]:
        st.markdown("### Developers Who Worked On This File")
        st.caption("Suggested reviewers based on commit history")

        developers = result.get("top_developers", [])
        if developers:
            for i, dev in enumerate(developers, 1):
                st.markdown(f"**{i}. {dev['email']}**")
                st.markdown(f"   - Commits: {dev['commit_count']}")
                if i <= 3:
                    st.success(f"   ⭐ Recommended as reviewer #{i}")
                st.markdown("")
        else:
            st.info("No developer history found")

    with tabs[2]:
        st.markdown("### Files Frequently Changed Together")
        st.caption("These files are often modified in the same commits")

        co_changed = result.get("frequently_changed_with", [])
        if co_changed:
            for item in co_changed:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.code(item['file'], language="text")
                with col2:
                    st.markdown(f"**{item['co_change_count']}x**")
        else:
            st.info("No co-changed files found")

    with tabs[3]:
        st.markdown("### Recent Commits")

        recent_commits = result.get("recent_commits", [])
        if recent_commits:
            for commit in recent_commits:
                sha_short = commit['sha'][:7] if commit.get('sha') else 'N/A'
                message = commit.get('message', 'No message').split('\n')[0][:80]

                with st.expander(f"💻 {sha_short}: {message}", expanded=False):
                    st.markdown(f"**Author:** {commit.get('author_name', 'Unknown')}")
                    st.markdown(f"**Date:** {str(commit.get('commit_date', 'N/A'))[:10]}")

                    if commit.get('ticket_references'):
                        st.markdown(f"**Tickets:** {', '.join(commit['ticket_references'])}")
        else:
            st.info("No recent commits found")


def render_ticket_impact_tab():
    """Render ticket impact analysis"""
    st.subheader("Ticket Impact Analysis")
    st.caption("Estimate the scope and impact of implementing a ticket")

    # Input
    ticket_key = st.text_input(
        "Ticket Key:",
        placeholder="e.g., AUTH-101",
        help="Enter the Jira ticket key"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_btn = st.button("🔍 Analyze Impact", type="primary")

    if analyze_btn and ticket_key:
        with st.spinner(f"Analyzing impact of {ticket_key}..."):
            result = analyze_ticket_impact(ticket_key)

        if result:
            display_ticket_impact_results(result)
    elif analyze_btn:
        st.warning("Please enter a ticket key")


def display_ticket_impact_results(result):
    """Display ticket impact analysis results"""
    ticket_key = result.get("ticket_key")
    summary = result.get("summary", "")

    st.success(f"✅ Analysis complete for: {ticket_key}")
    st.markdown(f"**Summary:** {summary}")

    # Implementation status
    if result.get("already_implemented"):
        st.info("ℹ️ This ticket has already been implemented")
    else:
        st.warning("⚠️ This ticket has not been implemented yet")

    st.divider()

    # Impact metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Files Affected", result.get("file_count", 0))
    with col2:
        st.metric("Total Changes", f"{result.get('total_changes', 0):,} lines")
    with col3:
        st.metric("Similar Tickets", len(result.get("similar_tickets", [])))
    with col4:
        st.metric("Dependencies", len(result.get("dependent_tickets", [])))

    # Blast radius
    blast_radius = result.get("blast_radius", "Unknown")
    if "Small" in blast_radius:
        st.success(f"📊 **Blast Radius:** {blast_radius}")
    elif "Medium" in blast_radius:
        st.info(f"📊 **Blast Radius:** {blast_radius}")
    elif "Large" in blast_radius:
        st.warning(f"📊 **Blast Radius:** {blast_radius}")
    else:
        st.error(f"📊 **Blast Radius:** {blast_radius}")

    st.divider()

    # Details in tabs
    tabs = st.tabs(["📁 Affected Files", "🎫 Similar Tickets", "🔗 Dependencies", "💻 Commits"])

    with tabs[0]:
        st.markdown("### Affected Files")
        files = result.get("affected_files", [])
        if files:
            for file in files:
                st.code(file, language="text")
        else:
            st.info("No files affected (ticket not yet implemented)")

    with tabs[1]:
        st.markdown("### Similar Tickets")
        st.caption("Other tickets with similar scope or components")

        similar = result.get("similar_tickets", [])
        if similar:
            for ticket in similar:
                st.markdown(f"- **{ticket['ticket_key']}**: {ticket['summary']} ({ticket['status']})")
        else:
            st.info("No similar tickets found")

    with tabs[2]:
        st.markdown("### Dependent Tickets")
        st.caption("Tickets that depend on or are related to this one")

        deps = result.get("dependent_tickets", [])
        if deps:
            for ticket in deps:
                st.markdown(f"- **{ticket['ticket_key']}**: {ticket['summary']} ({ticket['status']})")
        else:
            st.info("No dependent tickets found")

    with tabs[3]:
        st.markdown("### Implementation Commits")

        commits = result.get("commits", [])
        if commits:
            for commit in commits:
                sha_short = commit['sha'][:7] if commit.get('sha') else 'N/A'
                st.markdown(f"**{sha_short}**")
                st.caption(f"Additions: {commit.get('additions', 0)}, Deletions: {commit.get('deletions', 0)}")
        else:
            st.info("No commits yet (ticket not implemented)")


def render_commit_impact_tab():
    """Render commit impact analysis"""
    st.subheader("Commit Impact Analysis")
    st.caption("Analyze the impact and risk of a specific commit")

    # Input
    sha = st.text_input(
        "Commit SHA:",
        placeholder="e.g., abc123def456 or abc123",
        help="Enter the full or short commit SHA"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_btn = st.button("🔍 Analyze Impact", type="primary")

    if analyze_btn and sha:
        with st.spinner(f"Analyzing commit {sha}..."):
            result = analyze_commit_impact(sha)

        if result:
            display_commit_impact_results(result)
    elif analyze_btn:
        st.warning("Please enter a commit SHA")


def display_commit_impact_results(result):
    """Display commit impact analysis results"""
    sha = result.get("sha", "Unknown")[:7]
    message = result.get("message", "No message").split('\n')[0]

    st.success(f"✅ Analysis complete for commit: {sha}")
    st.markdown(f"**Message:** {message}")
    st.markdown(f"**Author:** {result.get('author', 'Unknown')}")
    st.markdown(f"**Date:** {str(result.get('date', 'Unknown'))[:10]}")

    st.divider()

    # Risk assessment
    risk_score = result.get("risk_score", 0)
    risk_level = result.get("risk_level", "Unknown")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Changed", result.get("file_count", 0))
    with col2:
        st.metric("Lines Changed", f"+{result.get('additions', 0)} -{result.get('deletions', 0)}")
    with col3:
        st.metric("Risk Score", f"{risk_score}/100")

    # Risk level indicator
    if risk_level == "Low":
        st.success(f"🟢 **Risk Level:** {risk_level}")
    elif risk_level == "Medium":
        st.info(f"🟡 **Risk Level:** {risk_level}")
    elif risk_level == "High":
        st.warning(f"🟠 **Risk Level:** {risk_level}")
    else:
        st.error(f"🔴 **Risk Level:** {risk_level}")

    # Progress bar for risk
    st.progress(min(risk_score / 100, 1.0))

    st.divider()

    # File types
    st.markdown("### File Types Changed")
    file_types = result.get("file_types", {})
    if file_types:
        for file_type, count in file_types.items():
            st.markdown(f"- **{file_type.replace('_', ' ').title()}**: {count} files")
    else:
        st.info("No file type information")

    st.divider()

    # Files and tickets
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Files Changed")
        files = result.get("files_changed", [])
        if files:
            for file in files:
                st.code(file, language="text")
        else:
            st.info("No files listed")

    with col2:
        st.markdown("### Related Tickets")
        tickets = result.get("related_tickets", [])
        if tickets:
            for ticket in tickets:
                st.markdown(f"**{ticket['ticket_key']}**: {ticket['summary']}")
                st.caption(f"Status: {ticket['status']} | Priority: {ticket['priority']}")
                st.markdown("")
        else:
            st.info("No related tickets")


def render_reviewer_suggestions_tab():
    """Render reviewer suggestions"""
    st.subheader("Suggest Code Reviewers")
    st.caption("Get reviewer recommendations based on file history")

    # Input
    st.markdown("### Files to Review")
    num_files = st.number_input("Number of files", min_value=1, max_value=10, value=2)

    files = []
    for i in range(num_files):
        file = st.text_input(
            f"File {i+1}:",
            key=f"file_{i}",
            placeholder=f"e.g., src/auth/oauth.ts"
        )
        if file:
            files.append(file)

    col1, col2 = st.columns([1, 5])
    with col1:
        suggest_btn = st.button("👥 Suggest Reviewers", type="primary")

    if suggest_btn and files:
        with st.spinner("Finding best reviewers..."):
            result = suggest_reviewers(files)

        if result:
            display_reviewer_suggestions(result, files)
    elif suggest_btn:
        st.warning("Please enter at least one file path")


def display_reviewer_suggestions(result, files):
    """Display reviewer suggestions"""
    st.success("✅ Reviewer suggestions ready")

    st.markdown("### Files Analyzed:")
    for file in files:
        st.code(file, language="text")

    st.divider()

    st.markdown("### Suggested Reviewers")

    reviewers = result.get("suggested_reviewers", [])
    if reviewers:
        for i, reviewer in enumerate(reviewers, 1):
            is_top = i <= 3

            with st.container():
                if is_top:
                    st.markdown(f"### ⭐ #{i} Recommended: {reviewer.get('author_name', 'Unknown')}")
                else:
                    st.markdown(f"### #{i}. {reviewer.get('author_name', 'Unknown')}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Email:** {reviewer.get('author_email', 'N/A')}")
                    st.markdown(f"**Commits:** {reviewer.get('commit_count', 0)}")

                with col2:
                    last_commit = reviewer.get('last_commit_date', 'Unknown')
                    st.markdown(f"**Last Commit:** {str(last_commit)[:10]}")

                # Files worked on
                files_worked = reviewer.get('files_worked_on', [])
                if files_worked:
                    st.markdown("**Files they worked on:**")
                    for file in files_worked[:5]:
                        st.caption(f"- {file}")

                if is_top:
                    st.success("✅ Highly recommended based on commit history")

                st.divider()
    else:
        st.info("No reviewers found. These files might be new or have limited history.")

    # Recommendation
    recommendation = result.get("recommendation", "")
    if recommendation:
        st.info(f"💡 {recommendation}")


# ============================================================================
# API Helper Functions
# ============================================================================

def analyze_file_impact(file_path: str):
    """Call file impact analysis API"""
    headers = {
        "Content-Type": "application/json"
    }
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        response = requests.post(
            f"{API_URL}/impact/file",
            headers=headers,
            json={"file_path": file_path},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to analyze file: {str(e)}")
        return None


def analyze_ticket_impact(ticket_key: str):
    """Call ticket impact analysis API"""
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        response = requests.get(
            f"{API_URL}/impact/ticket/{ticket_key}",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to analyze ticket: {str(e)}")
        return None


def analyze_commit_impact(sha: str):
    """Call commit impact analysis API"""
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        response = requests.get(
            f"{API_URL}/impact/commit/{sha}",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to analyze commit: {str(e)}")
        return None


def suggest_reviewers(files: list):
    """Call reviewer suggestion API"""
    headers = {
        "Content-Type": "application/json"
    }
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        response = requests.post(
            f"{API_URL}/impact/suggest-reviewers",
            headers=headers,
            json={"files": files},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Failed to suggest reviewers: {str(e)}")
        return None


if __name__ == "__main__":
    render_impact_page()
