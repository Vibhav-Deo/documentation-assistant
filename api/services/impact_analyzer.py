"""
Impact Analyzer Service

Predicts the impact of changes before they happen:
1. What breaks if we change this file?
2. Which tickets are affected by this code change?
3. What features depend on this component?
4. Who needs to be notified?

Core USP: Prevent breaking changes by understanding ripple effects.
"""

from typing import Dict, List, Optional, Set
from collections import defaultdict


class ImpactAnalyzer:
    """
    Analyzes the impact of changes across the codebase.

    Key capabilities:
    1. Predict affected tickets when code changes
    2. Find dependent files and components
    3. Identify affected features
    4. Suggest reviewers based on file history
    5. Calculate blast radius of changes
    """

    def __init__(self, db_service):
        self.db = db_service

    async def analyze_file_impact(self, file_path: str, org_id: str) -> Dict:
        """
        Analyze the impact of changing a specific file.

        Returns:
        - Related tickets
        - Commits that touched this file
        - Developers who worked on it
        - Other files often changed together
        - Features that depend on it

        Args:
            file_path: Path to the file
            org_id: Organization ID

        Returns:
            Dict with impact analysis
        """
        async with self.db.pool.acquire() as conn:
            # Find commits that modified this file
            commits = await conn.fetch("""
                SELECT
                    c.id,
                    c.sha,
                    c.message,
                    c.author_name,
                    c.author_email,
                    c.commit_date,
                    c.ticket_references,
                    c.files_changed
                FROM commits c
                WHERE c.organization_id = $1
                AND $2 = ANY(c.files_changed)
                ORDER BY c.commit_date DESC
                LIMIT 50
            """, org_id, file_path)

            commit_list = [dict(row) for row in commits]

            # Extract related information
            related_tickets = set()
            developers = defaultdict(int)
            co_changed_files = defaultdict(int)

            for commit in commit_list:
                # Collect tickets
                if commit['ticket_references']:
                    related_tickets.update(commit['ticket_references'])

                # Count developer contributions
                if commit['author_email']:
                    developers[commit['author_email']] += 1

                # Find files often changed together
                if commit['files_changed']:
                    for file in commit['files_changed']:
                        if file != file_path:
                            co_changed_files[file] += 1

            # Get ticket details
            ticket_details = []
            if related_tickets:
                tickets = await conn.fetch("""
                    SELECT ticket_key, summary, status, priority
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND ticket_key = ANY($2::text[])
                """, org_id, list(related_tickets))
                ticket_details = [dict(row) for row in tickets]

            # Sort by frequency
            top_developers = sorted(developers.items(), key=lambda x: x[1], reverse=True)[:5]
            top_co_changed = sorted(co_changed_files.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "file_path": file_path,
                "total_commits": len(commit_list),
                "related_tickets": ticket_details,
                "top_developers": [
                    {"email": dev, "commit_count": count}
                    for dev, count in top_developers
                ],
                "frequently_changed_with": [
                    {"file": file, "co_change_count": count}
                    for file, count in top_co_changed
                ],
                "recent_commits": commit_list[:10],
                "suggested_reviewers": [dev for dev, _ in top_developers[:3]]
            }

    async def analyze_ticket_impact(self, ticket_key: str, org_id: str) -> Dict:
        """
        Analyze what would be affected if we implement/change this ticket.
        OPTIMIZED: Batch queries and use CTEs for better performance.
        """
        async with self.db.pool.acquire() as conn:
            # OPTIMIZED: Single query with all ticket data and related info
            result = await conn.fetchrow("""
                WITH ticket_commits AS (
                    SELECT 
                        c.id, c.sha, c.message, c.files_changed, 
                        c.additions, c.deletions
                    FROM commits c
                    WHERE c.organization_id = $1
                    AND $2 = ANY(c.ticket_references)
                )
                SELECT 
                    t.*,
                    COALESCE(array_agg(DISTINCT f.file) FILTER (WHERE f.file IS NOT NULL), '{}') as affected_files,
                    COALESCE(SUM(tc.additions), 0) as total_additions,
                    COALESCE(SUM(tc.deletions), 0) as total_deletions,
                    COUNT(tc.id) as commit_count
                FROM jira_tickets t
                LEFT JOIN ticket_commits tc ON true
                LEFT JOIN LATERAL unnest(tc.files_changed) as f(file) ON true
                WHERE t.organization_id = $1 AND t.ticket_key = $2
                GROUP BY t.id, t.ticket_key, t.summary, t.description, t.status, 
                         t.assignee, t.reporter, t.issue_type, t.priority, 
                         t.labels, t.components, t.created_date, t.updated_date, 
                         t.resolved_date, t.metadata, t.organization_id, t.created_at
            """, org_id, ticket_key)

            if not result:
                raise ValueError(f"Ticket {ticket_key} not found")

            ticket_dict = dict(result)
            affected_files = set(ticket_dict['affected_files'])
            total_additions = int(ticket_dict['total_additions'])
            total_deletions = int(ticket_dict['total_deletions'])

            # Get commits separately for return data
            commits = await conn.fetch("""
                SELECT id, sha, message, files_changed, additions, deletions
                FROM commits
                WHERE organization_id = $1 AND $2 = ANY(ticket_references)
            """, org_id, ticket_key)
            commit_list = [dict(row) for row in commits]

            # OPTIMIZED: Find similar tickets with better query
            similar_tickets = await conn.fetch("""
                SELECT ticket_key, summary, status
                FROM jira_tickets
                WHERE organization_id = $1
                AND ticket_key != $2
                AND (
                    (components && $3 AND cardinality(components) > 0)
                    OR (similarity(summary, $4) > 0.3)
                )
                ORDER BY similarity(summary, $4) DESC
                LIMIT 10
            """, org_id, ticket_key, ticket_dict['components'] or [], ticket_dict['summary'])

            similar_list = [dict(row) for row in similar_tickets]

            # Find dependent tickets (mentioned in description/comments)
            # For now, simple text search for ticket keys
            dependent_keys = self._extract_ticket_keys_from_text(
                ticket_dict.get('description', '')
            )

            dependent_tickets = []
            if dependent_keys:
                dependents = await conn.fetch("""
                    SELECT ticket_key, summary, status
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND ticket_key = ANY($2::text[])
                """, org_id, list(dependent_keys))
                dependent_tickets = [dict(row) for row in dependents]

            return {
                "ticket_key": ticket_key,
                "summary": ticket_dict['summary'],
                "status": ticket_dict['status'],
                "already_implemented": len(commit_list) > 0,
                "affected_files": list(affected_files),
                "file_count": len(affected_files),
                "total_changes": total_additions + total_deletions,
                "additions": total_additions,
                "deletions": total_deletions,
                "similar_tickets": similar_list,
                "dependent_tickets": dependent_tickets,
                "commits": commit_list,
                "blast_radius": self._calculate_blast_radius(
                    len(affected_files),
                    total_additions + total_deletions,
                    len(similar_list)
                )
            }

    async def analyze_commit_impact(self, sha: str, org_id: str) -> Dict:
        """
        Analyze the impact of a specific commit.

        Returns:
        - Files changed
        - Related tickets
        - Affected features
        - Risk assessment

        Args:
            sha: Commit SHA
            org_id: Organization ID

        Returns:
            Dict with impact analysis
        """
        async with self.db.pool.acquire() as conn:
            # Get commit details
            commit = await conn.fetchrow("""
                SELECT c.*, r.repo_name, r.repo_url
                FROM commits c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.organization_id = $1
                AND c.sha LIKE $2
            """, org_id, f"{sha}%")

            if not commit:
                raise ValueError(f"Commit {sha} not found")

            commit_dict = dict(commit)

            # Get ticket details if referenced
            ticket_details = []
            if commit_dict['ticket_references']:
                tickets = await conn.fetch("""
                    SELECT ticket_key, summary, status, priority
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND ticket_key = ANY($2::text[])
                """, org_id, commit_dict['ticket_references'])
                ticket_details = [dict(row) for row in tickets]

            # Analyze files changed
            files_changed = commit_dict['files_changed'] or []
            file_types = self._categorize_files(files_changed)

            # Calculate risk
            risk_score = self._calculate_risk_score(
                len(files_changed),
                commit_dict['additions'] or 0,
                commit_dict['deletions'] or 0,
                file_types
            )

            return {
                "sha": commit_dict['sha'],
                "message": commit_dict['message'],
                "author": commit_dict['author_name'],
                "date": commit_dict['commit_date'],
                "files_changed": files_changed,
                "file_count": len(files_changed),
                "file_types": file_types,
                "additions": commit_dict['additions'],
                "deletions": commit_dict['deletions'],
                "related_tickets": ticket_details,
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score)
            }

    async def suggest_reviewers(self, files: List[str], org_id: str) -> Dict:
        """
        Suggest code reviewers based on file history.
        OPTIMIZED: Better query structure for file matching.
        """
        async with self.db.pool.acquire() as conn:
            # OPTIMIZED: Use array overlap for better performance
            reviewers = await conn.fetch("""
                SELECT
                    c.author_name,
                    c.author_email,
                    COUNT(*) as commit_count,
                    MAX(c.commit_date) as last_commit_date,
                    array_agg(DISTINCT f.file) FILTER (WHERE f.file = ANY($2::text[])) as files_worked_on
                FROM commits c
                CROSS JOIN LATERAL unnest(c.files_changed) as f(file)
                WHERE c.organization_id = $1
                AND c.files_changed && $2::text[]
                GROUP BY c.author_name, c.author_email
                HAVING COUNT(*) > 0
                ORDER BY commit_count DESC, last_commit_date DESC
                LIMIT 10
            """, org_id, files)

            reviewer_list = [dict(row) for row in reviewers]

            return {
                "suggested_reviewers": reviewer_list,
                "files_analyzed": files,
                "recommendation": "Top 2-3 reviewers based on commit history" if reviewer_list else "No historical data available"
            }

    def _extract_ticket_keys_from_text(self, text: str) -> Set[str]:
        """Extract ticket keys like DEMO-123 from text."""
        import re
        if not text:
            return set()
        pattern = r'\b([A-Z]{2,10}-\d+)\b'
        return set(re.findall(pattern, text))

    def _categorize_files(self, files: List[str]) -> Dict[str, int]:
        """Categorize files by type."""
        categories = defaultdict(int)
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.java', '.go', '.rb')):
                categories['source_code'] += 1
            elif file.endswith(('.test.js', '.spec.ts', '_test.py', 'test_')):
                categories['tests'] += 1
            elif file.endswith(('.md', '.txt', '.rst')):
                categories['documentation'] += 1
            elif file.endswith(('.json', '.yaml', '.yml', '.xml')):
                categories['config'] += 1
            else:
                categories['other'] += 1
        return dict(categories)

    def _calculate_risk_score(self, file_count: int, additions: int, deletions: int, file_types: Dict) -> float:
        """Calculate risk score (0-100) for changes."""
        # Base risk from volume of changes
        volume_risk = min(file_count * 5 + (additions + deletions) / 100, 50)

        # Additional risk for certain file types
        type_risk = file_types.get('config', 0) * 5 + file_types.get('source_code', 0) * 2

        # Bonus for having tests
        test_bonus = -10 if file_types.get('tests', 0) > 0 else 0

        total_risk = max(0, min(100, volume_risk + type_risk + test_bonus))
        return round(total_risk, 1)

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level."""
        if risk_score < 20:
            return "Low"
        elif risk_score < 50:
            return "Medium"
        elif risk_score < 75:
            return "High"
        else:
            return "Critical"

    def _calculate_blast_radius(self, file_count: int, total_changes: int, similar_count: int) -> str:
        """Estimate blast radius of changes."""
        if file_count <= 2 and total_changes < 50:
            return "Small - Localized changes"
        elif file_count <= 5 and total_changes < 200:
            return "Medium - Module-level changes"
        elif file_count <= 10 and total_changes < 500:
            return "Large - Cross-module changes"
        else:
            return "Very Large - System-wide changes"
