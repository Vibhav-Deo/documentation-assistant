"""
Gap Analysis UI Component

Visualizes gaps and inconsistencies in the project:
- Orphaned tickets
- Undocumented features
- Missing decisions
- Stale work

Provides actionable insights and drill-down views.
"""

import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_URL = "http://api:4000"


def render_gaps_page():
    """Render the Gap Analysis page with multiple views"""
    st.title("🔍 Gap Analysis")
    st.caption("Find missing work, documentation gaps, and stale items")

    # Check authentication
    if "auth_token" not in st.session_state:
        st.warning("⚠️ Please log in to view gap analysis")
        return

    # Add refresh button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🔄 Refresh", key="refresh_gaps"):
            st.rerun()

    # Fetch comprehensive gaps
    with st.spinner("Analyzing gaps..."):
        gaps_data = fetch_comprehensive_gaps()

    if not gaps_data:
        st.error("Failed to load gap analysis. Please try again.")
        return

    # Display summary cards
    render_summary_cards(gaps_data.get("summary", {}))

    st.divider()

    # Tabbed interface for different gap types
    tabs = st.tabs([
        "🎫 Orphaned Tickets",
        "📝 Undocumented Features",
        "🧠 Missing Decisions",
        "⏰ Stale Work"
    ])

    with tabs[0]:
        render_orphaned_tickets(gaps_data.get("orphaned_tickets", {}))

    with tabs[1]:
        render_undocumented_features(gaps_data.get("undocumented_features", {}))

    with tabs[2]:
        render_missing_decisions(gaps_data.get("missing_decisions", {}))

    with tabs[3]:
        render_stale_work(gaps_data.get("stale_work", {}))


def render_summary_cards(summary):
    """Render summary statistics cards"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🎫 Orphaned Tickets",
            value=summary.get("total_orphaned", 0),
            help="Tickets with no commits or PRs"
        )

    with col2:
        st.metric(
            label="📝 Undocumented",
            value=summary.get("total_undocumented", 0),
            help="Commits without ticket references"
        )

    with col3:
        st.metric(
            label="🧠 Missing Decisions",
            value=summary.get("total_missing_decisions", 0),
            help="Tickets needing decision analysis"
        )

    with col4:
        st.metric(
            label="⏰ Stale Work",
            value=summary.get("total_stale", 0),
            help="Work not updated recently"
        )


def render_orphaned_tickets(data):
    """Render orphaned tickets tab"""
    st.subheader("Orphaned Tickets")
    st.caption("Jira tickets with no associated commits or pull requests")

    total = data.get("total_orphaned", 0)
    if total == 0:
        st.success("✅ No orphaned tickets found! All tickets have implementation.")
        return

    # Statistics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**By Status**")
        by_status = data.get("by_status", {})
        for status, count in sorted(by_status.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{status}**: {count}")

    with col2:
        st.markdown("**By Priority**")
        by_priority = data.get("by_priority", {})
        for priority, count in sorted(by_priority.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{priority}**: {count}")

    st.divider()

    # Tickets list
    tickets = data.get("tickets", [])
    if tickets:
        st.markdown(f"**Found {total} orphaned tickets:**")

        for ticket in tickets[:20]:  # Show first 20
            with st.expander(f"🎫 {ticket['ticket_key']}: {ticket['summary']}", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**Status:** {ticket.get('status', 'Unknown')}")
                    st.markdown(f"**Priority:** {ticket.get('priority', 'Unknown')}")

                with col2:
                    st.markdown(f"**Assignee:** {ticket.get('assignee', 'Unassigned')}")
                    if ticket.get('created_date'):
                        created = ticket['created_date']
                        st.markdown(f"**Created:** {created[:10] if isinstance(created, str) else 'N/A'}")

                with col3:
                    if ticket.get('updated_date'):
                        updated = ticket['updated_date']
                        st.markdown(f"**Updated:** {updated[:10] if isinstance(updated, str) else 'N/A'}")

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Analyze Decision", key=f"analyze_{ticket['ticket_key']}"):
                        st.session_state.analyze_ticket = ticket['ticket_key']
                        st.switch_page("pages/decisions.py")

                with col2:
                    if st.button(f"View Relationships", key=f"rel_{ticket['ticket_key']}"):
                        st.session_state.view_ticket = ticket['ticket_key']
                        st.switch_page("pages/relationships.py")

        if total > 20:
            st.info(f"Showing 20 of {total} orphaned tickets")


def render_undocumented_features(data):
    """Render undocumented features tab"""
    st.subheader("Undocumented Features")
    st.caption("Commits without ticket references")

    total = data.get("total_undocumented", 0)
    if total == 0:
        st.success("✅ All commits are properly documented!")
        return

    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Commits", total)
    with col2:
        st.metric("Code Changes", f"{data.get('total_code_changes', 0):,} lines")
    with col3:
        by_author = data.get("by_author", {})
        top_author = max(by_author.items(), key=lambda x: x[1])[0] if by_author else "N/A"
        st.metric("Top Author", top_author)

    st.divider()

    # By repository
    st.markdown("**By Repository:**")
    by_repo = data.get("by_repository", {})
    for repo, count in sorted(by_repo.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"- **{repo}**: {count} commits")

    st.divider()

    # Commits list
    commits = data.get("commits", [])
    if commits:
        st.markdown(f"**Recent undocumented commits:**")

        for commit in commits[:15]:  # Show first 15
            sha_short = commit['sha'][:7] if commit.get('sha') else 'N/A'
            message = commit.get('message', 'No message')
            first_line = message.split('\n')[0][:80]

            with st.expander(f"💻 {sha_short}: {first_line}", expanded=False):
                st.markdown(f"**Author:** {commit.get('author_name', 'Unknown')}")
                st.markdown(f"**Date:** {str(commit.get('commit_date', 'N/A'))[:10]}")
                st.markdown(f"**Repository:** {commit.get('repo_name', 'Unknown')}")

                if commit.get('files_changed'):
                    st.markdown("**Files Changed:**")
                    for file in commit['files_changed'][:5]:
                        st.code(file, language="text")

                st.markdown("**Message:**")
                st.text_area("", value=message, height=100, key=f"msg_{sha_short}", disabled=True)

                st.warning("⚠️ This commit has no ticket reference. Consider adding one for traceability.")

        if total > 15:
            st.info(f"Showing 15 of {total} undocumented commits")


def render_missing_decisions(data):
    """Render missing decisions tab"""
    st.subheader("Missing Decisions")
    st.caption("Tickets that should have decision analysis but don't")

    total = data.get("total_missing_decisions", 0)
    if total == 0:
        st.success("✅ All major tickets have decision analysis!")
        return

    # By issue type
    st.markdown("**By Issue Type:**")
    by_type = data.get("by_issue_type", {})
    for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"- **{issue_type}**: {count}")

    st.divider()

    # Tickets list
    tickets = data.get("tickets", [])
    if tickets:
        st.markdown(f"**Tickets needing decision analysis:**")

        for ticket in tickets:
            with st.expander(f"🎫 {ticket['ticket_key']}: {ticket['summary']}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Type:** {ticket.get('issue_type', 'Unknown')}")
                    st.markdown(f"**Status:** {ticket.get('status', 'Unknown')}")

                with col2:
                    st.markdown(f"**Commits:** {ticket.get('commit_count', 0)}")
                    st.markdown(f"**PRs:** {ticket.get('pr_count', 0)}")

                st.info("💡 This ticket has implementation (commits/PRs) but no decision analysis.")

                if st.button(f"Analyze Now", key=f"analyze_dec_{ticket['ticket_key']}"):
                    with st.spinner(f"Analyzing {ticket['ticket_key']}..."):
                        result = analyze_ticket_decision(ticket['ticket_key'])
                        if result:
                            st.success(f"✅ Decision analyzed for {ticket['ticket_key']}")
                            st.rerun()
                        else:
                            st.error("Failed to analyze decision")


def render_stale_work(data):
    """Render stale work tab"""
    st.subheader("Stale Work")
    st.caption(f"Work items not updated in {data.get('days_threshold', 30)} days")

    total = data.get("total_stale", 0)
    if total == 0:
        st.success("✅ No stale work items found!")
        return

    # Statistics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**By Status:**")
        by_status = data.get("by_status", {})
        for status, count in sorted(by_status.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{status}**: {count}")

    with col2:
        st.markdown("**By Assignee:**")
        by_assignee = data.get("by_assignee", {})
        for assignee, count in sorted(by_assignee.items(), key=lambda x: x[1], reverse=True)[:10]:
            st.markdown(f"- **{assignee}**: {count}")

    st.divider()

    # Tickets list
    tickets = data.get("tickets", [])
    if tickets:
        st.markdown(f"**Stale tickets (oldest first):**")

        for ticket in tickets[:20]:
            days_stale = int(ticket.get('days_since_update', 0))
            severity = "🔴" if days_stale > 60 else "🟡" if days_stale > 30 else "🟢"

            with st.expander(f"{severity} {ticket['ticket_key']}: {ticket['summary']} ({days_stale} days)", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**Status:** {ticket.get('status', 'Unknown')}")
                    st.markdown(f"**Priority:** {ticket.get('priority', 'Unknown')}")

                with col2:
                    st.markdown(f"**Assignee:** {ticket.get('assignee', 'Unassigned')}")
                    if ticket.get('created_date'):
                        st.markdown(f"**Created:** {str(ticket['created_date'])[:10]}")

                with col3:
                    if ticket.get('updated_date'):
                        st.markdown(f"**Last Updated:** {str(ticket['updated_date'])[:10]}")
                    st.markdown(f"**Days Stale:** {days_stale}")

                if days_stale > 60:
                    st.error("⚠️ This ticket hasn't been updated in over 60 days. Consider closing or updating it.")
                elif days_stale > 30:
                    st.warning("⚠️ This ticket hasn't been updated in over 30 days.")

        if total > 20:
            st.info(f"Showing 20 of {total} stale tickets")


# ============================================================================
# API Helper Functions
# ============================================================================

def fetch_comprehensive_gaps():
    """Fetch all gaps from API"""
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        response = requests.get(
            f"{API_URL}/gaps/comprehensive",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Failed to fetch gaps: {str(e)}")
        return None


def analyze_ticket_decision(ticket_key: str):
    """Trigger decision analysis for a ticket"""
    headers = {}
    if "auth_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        response = requests.post(
            f"{API_URL}/decisions/analyze/{ticket_key}",
            headers=headers,
            timeout=120
        )

        return response.status_code == 200
    except Exception as e:
        st.error(f"Failed to analyze: {str(e)}")
        return False


if __name__ == "__main__":
    render_gaps_page()
