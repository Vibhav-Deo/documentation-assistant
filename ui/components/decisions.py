import streamlit as st
import requests
from config import API_URL
from typing import Dict, List, Optional
import pandas as pd


def render_decisions_page():
    """Render the Decision Analysis page"""
    st.title("🧠 Decision Analysis")
    st.caption("Extract and analyze decision rationale from tickets, commits, PRs, and documentation")

    # Create tabs for different decision analysis features
    tabs = st.tabs([
        "🔍 Analyze Ticket",
        "🔎 Search Decisions",
        "📚 Browse All"
    ])

    with tabs[0]:
        render_analyze_ticket_ui()

    with tabs[1]:
        render_search_decisions_ui()

    with tabs[2]:
        render_browse_decisions_ui()


def render_analyze_ticket_ui():
    """UI for analyzing a specific ticket's decision"""
    st.subheader("🔍 Analyze Ticket Decision")
    st.write("Enter a Jira ticket key to extract decision rationale from multi-source context")

    col1, col2 = st.columns([3, 1])

    with col1:
        ticket_key = st.text_input(
            "Jira Ticket Key",
            placeholder="e.g., PROJ-123",
            key="analyze_ticket_key",
            help="Enter the Jira ticket key to analyze"
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        analyze_button = st.button("🚀 Analyze", use_container_width=True)

    if analyze_button:
        if not ticket_key:
            st.warning("⚠️ Please enter a ticket key")
            return

        with st.spinner(f"Analyzing decision rationale for {ticket_key}..."):
            result = analyze_ticket_decision(ticket_key)

            if result:
                st.success(f"✅ Analysis complete for {ticket_key}")

                # Store in session state for viewing
                st.session_state.current_decision = result['decision']

                # Display the decision
                display_full_decision(result['decision'])
            else:
                st.error("❌ Failed to analyze decision. Check if the ticket exists and try again.")


def render_search_decisions_ui():
    """UI for searching decisions with natural language"""
    st.subheader("🔎 Search Decisions")
    st.write("Use natural language to search across all analyzed decisions")

    col1, col2 = st.columns([4, 1])

    with col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="e.g., authentication refactoring, database migration, API design",
            key="search_decisions_query",
            help="Enter natural language query to search decisions"
        )

    with col2:
        limit = st.number_input("Results", min_value=5, max_value=50, value=10, key="search_limit")

    if st.button("🔍 Search", use_container_width=True):
        if not search_query:
            st.warning("⚠️ Please enter a search query")
            return

        with st.spinner("Searching decisions..."):
            results = search_decisions(search_query, limit)

            if results:
                st.write(f"**Found {len(results)} matching decision(s)**")

                for i, decision in enumerate(results, 1):
                    with st.expander(f"🎯 {i}. {decision['decision_summary'][:80]}..."):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"**Ticket:** [{decision['ticket_key']}]")
                            st.markdown(f"**Problem:** {decision.get('problem_statement', 'N/A')[:200]}...")
                            st.markdown(f"**Approach:** {decision.get('chosen_approach', 'N/A')[:200]}...")

                        with col2:
                            confidence = decision.get('confidence_score', 0) * 100
                            st.metric("Confidence", f"{confidence:.0f}%")
                            st.caption(f"Created: {decision['created_at'][:10]}")

                        # View full decision button
                        if st.button(f"📖 View Full Analysis", key=f"view_{decision['id']}"):
                            st.session_state.selected_decision_id = decision['id']
                            st.rerun()
            else:
                st.info("No decisions found matching your query")

    # Show selected decision if available
    if st.session_state.get("selected_decision_id"):
        decision = get_decision_by_id(st.session_state.selected_decision_id)
        if decision:
            st.divider()
            display_full_decision(decision)

            if st.button("🔙 Back to Search Results"):
                st.session_state.selected_decision_id = None
                st.rerun()


def render_browse_decisions_ui():
    """UI for browsing all decisions"""
    st.subheader("📚 Browse All Decisions")
    st.write("View all analyzed decisions for your organization")

    col1, col2 = st.columns([3, 1])

    with col1:
        filter_ticket = st.text_input(
            "Filter by Ticket (optional)",
            placeholder="e.g., PROJ",
            key="filter_ticket"
        )

    with col2:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=50, key="browse_limit")

    if st.button("📥 Load Decisions", use_container_width=True):
        with st.spinner("Loading decisions..."):
            decisions = list_all_decisions(limit)

            # Apply client-side filter if provided
            if filter_ticket:
                decisions = [d for d in decisions if filter_ticket.lower() in d['ticket_key'].lower()]

            if decisions:
                st.write(f"**Showing {len(decisions)} decision(s)**")

                # Create DataFrame for tabular view
                df = pd.DataFrame([{
                    'Ticket': d['ticket_key'],
                    'Summary': d['decision_summary'][:60] + '...' if len(d['decision_summary']) > 60 else d['decision_summary'],
                    'Confidence': f"{d.get('confidence_score', 0) * 100:.0f}%",
                    'Date': d['created_at'][:10],
                    'ID': d['id']
                } for d in decisions])

                # Display as interactive table
                st.dataframe(df[['Ticket', 'Summary', 'Confidence', 'Date']], use_container_width=True, hide_index=True)

                # Decision selector
                st.divider()
                selected_ticket = st.selectbox(
                    "Select a decision to view details:",
                    options=df['Ticket'].tolist(),
                    key="selected_ticket_browse"
                )

                if selected_ticket:
                    selected_decision = next((d for d in decisions if d['ticket_key'] == selected_ticket), None)
                    if selected_decision:
                        display_full_decision(selected_decision)
            else:
                st.info("No decisions found. Analyze some tickets first!")


def display_full_decision(decision: Dict):
    """Render a complete decision analysis"""
    st.markdown("---")
    st.markdown(f"### 📝 {decision['decision_summary']}")

    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Ticket", decision['ticket_key'])
    with col2:
        confidence = decision.get('confidence_score', 0) * 100
        st.metric("🎯 Confidence", f"{confidence:.0f}%")
    with col3:
        st.caption(f"🕒 Analyzed: {decision['created_at'][:16]}")

    # Problem Statement
    st.markdown("#### 🎯 Problem Statement")
    st.info(decision.get('problem_statement', 'N/A'))

    # Alternatives Considered
    st.markdown("#### 🔀 Alternatives Considered")
    alternatives = decision.get('alternatives_considered', [])
    if alternatives and isinstance(alternatives, list):
        for i, alt in enumerate(alternatives, 1):
            st.markdown(f"{i}. {alt}")
    else:
        st.caption("None documented")

    # Chosen Approach
    st.markdown("#### ✅ Chosen Approach")
    st.success(decision.get('chosen_approach', 'N/A'))

    # Rationale
    st.markdown("#### 💡 Rationale")
    st.write(decision.get('rationale', 'N/A'))

    # Constraints & Risks
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ⚠️ Constraints")
        constraints = decision.get('constraints', [])
        if constraints and isinstance(constraints, list):
            for c in constraints:
                st.markdown(f"- {c}")
        else:
            st.caption("None identified")

    with col2:
        st.markdown("#### 🚨 Risks")
        risks = decision.get('risks', [])
        if risks and isinstance(risks, list):
            for r in risks:
                st.markdown(f"- {r}")
        else:
            st.caption("None identified")

    # Tradeoffs
    if decision.get('tradeoffs'):
        st.markdown("#### ⚖️ Tradeoffs")
        st.write(decision['tradeoffs'])

    # Implementation Details
    st.markdown("#### 🔧 Implementation")

    implementation_shown = False

    # Commits
    commits = decision.get('implementation_commits', [])
    if commits and isinstance(commits, list):
        st.markdown("**Commits:**")
        for commit in commits:
            if isinstance(commit, dict):
                sha = commit.get('sha', 'N/A')[:7]
                message = commit.get('message', 'N/A')
                st.markdown(f"- `{sha}` {message}")
                implementation_shown = True

    # PRs
    prs = decision.get('related_prs', [])
    if prs and isinstance(prs, list):
        st.markdown("**Pull Requests:**")
        for pr in prs:
            if isinstance(pr, dict):
                pr_number = pr.get('pr_number', 'N/A')
                title = pr.get('title', 'N/A')
                url = pr.get('url', '#')
                st.markdown(f"- [#{pr_number}]({url}) - {title}")
                implementation_shown = True

    # Related Docs
    docs = decision.get('related_docs', [])
    if docs and isinstance(docs, list):
        st.markdown("**Related Documentation:**")
        for doc in docs:
            if isinstance(doc, dict):
                title = doc.get('title', 'N/A')
                url = doc.get('url', '#')
                st.markdown(f"- [{title}]({url})")
                implementation_shown = True

    if not implementation_shown:
        st.caption("No implementation details available")

    # Stakeholders
    stakeholders = decision.get('stakeholders', [])
    if stakeholders and isinstance(stakeholders, list) and len(stakeholders) > 0:
        st.markdown("#### 👥 Stakeholders")
        st.write(", ".join(stakeholders))

    # Raw Analysis (collapsible)
    if decision.get('raw_analysis'):
        with st.expander("🔍 View Raw AI Analysis"):
            st.text(decision['raw_analysis'])


# API Integration Functions

def analyze_ticket_decision(ticket_key: str) -> Optional[Dict]:
    """Trigger decision analysis for a specific ticket"""
    try:
        headers = {}
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

        response = requests.post(
            f"{API_URL}/decisions/analyze/{ticket_key}",
            headers=headers,
            timeout=120  # 2 minutes for analysis
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("❌ Authentication required")
        elif response.status_code == 404:
            st.error(f"❌ Ticket {ticket_key} not found")
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"❌ Analysis failed: {error_detail}")

        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Analysis timed out. This ticket may have too much context.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def get_decision_by_id(decision_id: str) -> Optional[Dict]:
    """Retrieve a specific decision by ID"""
    try:
        headers = {}
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

        response = requests.get(
            f"{API_URL}/decisions/{decision_id}",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        return None
    except Exception as e:
        st.error(f"❌ Error fetching decision: {str(e)}")
        return None


def get_decisions_for_ticket(ticket_key: str) -> List[Dict]:
    """Get all decision analyses for a specific ticket"""
    try:
        headers = {}
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

        response = requests.get(
            f"{API_URL}/decisions/ticket/{ticket_key}",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        return []
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return []


def search_decisions(query: str, limit: int = 10) -> List[Dict]:
    """Search decisions using natural language"""
    try:
        headers = {}
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

        response = requests.get(
            f"{API_URL}/decisions/search",
            params={"query": query, "limit": limit},
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        return []
    except Exception as e:
        st.error(f"❌ Error searching: {str(e)}")
        return []


def list_all_decisions(limit: int = 100) -> List[Dict]:
    """List all decisions for the organization"""
    try:
        headers = {}
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

        response = requests.get(
            f"{API_URL}/decisions",
            params={"limit": limit},
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        return []
    except Exception as e:
        st.error(f"❌ Error loading decisions: {str(e)}")
        return []
