"""
Gap Detector Service

Identifies gaps and inconsistencies in your project:
1. Orphaned tickets (no commits/PRs)
2. Undocumented features (code without docs)
3. Missing decisions (tickets without analysis)
4. Stale work (old tickets still open)

Core USP: Proactively surface problems before they become critical.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class GapDetector:
    """
    Detects gaps and inconsistencies across all data sources.

    Key capabilities:
    1. Find orphaned Jira tickets (no implementation found)
    2. Find undocumented features (code but no docs/tickets)
    3. Find missing decision analysis
    4. Find stale work items
    5. Find broken relationships (referenced tickets/commits that don't exist)
    """

    def __init__(self, db_service):
        self.db = db_service

    async def find_orphaned_tickets(self, org_id: str, days: int = 90) -> Dict:
        """
        Find Jira tickets that have no associated commits or PRs.

        These are tickets that might be:
        - Forgotten/abandoned
        - Implemented but not linked properly
        - Duplicates of other work

        Args:
            org_id: Organization ID
            days: Look at tickets from last N days (default 90)

        Returns:
            Dict with orphaned tickets and statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        async with self.db.pool.acquire() as conn:
            # Find tickets with no commits or PRs
            orphaned = await conn.fetch("""
                SELECT
                    t.id,
                    t.ticket_key,
                    t.summary,
                    t.status,
                    t.priority,
                    t.assignee,
                    t.created_date,
                    t.updated_date,
                    (SELECT COUNT(*) FROM commits c
                     WHERE c.organization_id = t.organization_id
                     AND t.ticket_key = ANY(c.ticket_references)) as commit_count,
                    (SELECT COUNT(*) FROM pull_requests pr
                     WHERE pr.organization_id = t.organization_id
                     AND t.ticket_key = ANY(pr.ticket_references)) as pr_count
                FROM jira_tickets t
                WHERE t.organization_id = $1
                AND t.created_date >= $2
                AND NOT EXISTS (
                    SELECT 1 FROM commits c
                    WHERE c.organization_id = t.organization_id
                    AND t.ticket_key = ANY(c.ticket_references)
                )
                AND NOT EXISTS (
                    SELECT 1 FROM pull_requests pr
                    WHERE pr.organization_id = t.organization_id
                    AND t.ticket_key = ANY(pr.ticket_references)
                )
                ORDER BY t.priority DESC, t.created_date DESC
            """, org_id, cutoff_date)

            orphaned_tickets = [dict(row) for row in orphaned]

            # Calculate statistics
            by_status = {}
            by_priority = {}
            by_assignee = {}

            for ticket in orphaned_tickets:
                status = ticket['status'] or 'Unknown'
                priority = ticket['priority'] or 'Unknown'
                assignee = ticket['assignee'] or 'Unassigned'

                by_status[status] = by_status.get(status, 0) + 1
                by_priority[priority] = by_priority.get(priority, 0) + 1
                by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

            return {
                "total_orphaned": len(orphaned_tickets),
                "tickets": orphaned_tickets,
                "by_status": by_status,
                "by_priority": by_priority,
                "by_assignee": by_assignee,
                "timeframe_days": days
            }

    async def find_undocumented_features(self, org_id: str) -> Dict:
        """
        Find code changes that have no corresponding documentation or tickets.

        These are potentially undocumented features that should be:
        - Added to documentation
        - Linked to tickets
        - Explained for future reference

        Args:
            org_id: Organization ID

        Returns:
            Dict with undocumented commits and statistics
        """
        async with self.db.pool.acquire() as conn:
            # Find commits with no ticket references
            undocumented_commits = await conn.fetch("""
                SELECT
                    c.id,
                    c.sha,
                    c.message,
                    c.author_name,
                    c.author_email,
                    c.commit_date,
                    c.files_changed,
                    c.additions,
                    c.deletions,
                    r.repo_name,
                    r.repo_url
                FROM commits c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.organization_id = $1
                AND (c.ticket_references IS NULL OR array_length(c.ticket_references, 1) = 0)
                AND c.message NOT ILIKE '%merge%'
                AND c.message NOT ILIKE '%revert%'
                ORDER BY c.commit_date DESC
                LIMIT 100
            """, org_id)

            undocumented = [dict(row) for row in undocumented_commits]

            # Analyze patterns
            by_author = {}
            by_repo = {}
            total_changes = 0

            for commit in undocumented:
                author = commit['author_name'] or 'Unknown'
                repo = commit['repo_name'] or 'Unknown'

                by_author[author] = by_author.get(author, 0) + 1
                by_repo[repo] = by_repo.get(repo, 0) + 1
                total_changes += (commit['additions'] or 0) + (commit['deletions'] or 0)

            return {
                "total_undocumented": len(undocumented),
                "commits": undocumented,
                "by_author": by_author,
                "by_repository": by_repo,
                "total_code_changes": total_changes
            }

    async def find_missing_decisions(self, org_id: str) -> Dict:
        """
        Find tickets that should have decision analysis but don't.

        Criteria for needing decision analysis:
        - Type is "Story" or "Epic"
        - Has commits/PRs (was implemented)
        - No decision record exists

        Args:
            org_id: Organization ID

        Returns:
            Dict with tickets needing decision analysis
        """
        async with self.db.pool.acquire() as conn:
            # Find tickets that should have decisions but don't
            missing_decisions = await conn.fetch("""
                SELECT
                    t.id,
                    t.ticket_key,
                    t.summary,
                    t.issue_type,
                    t.status,
                    t.assignee,
                    t.created_date,
                    (SELECT COUNT(*) FROM commits c
                     WHERE c.organization_id = t.organization_id
                     AND t.ticket_key = ANY(c.ticket_references)) as commit_count,
                    (SELECT COUNT(*) FROM pull_requests pr
                     WHERE pr.organization_id = t.organization_id
                     AND t.ticket_key = ANY(pr.ticket_references)) as pr_count
                FROM jira_tickets t
                WHERE t.organization_id = $1
                AND (t.issue_type ILIKE '%story%' OR t.issue_type ILIKE '%epic%' OR t.issue_type ILIKE '%feature%')
                AND EXISTS (
                    SELECT 1 FROM commits c
                    WHERE c.organization_id = t.organization_id
                    AND t.ticket_key = ANY(c.ticket_references)
                )
                AND NOT EXISTS (
                    SELECT 1 FROM decisions d
                    WHERE d.organization_id = t.organization_id
                    AND d.ticket_key = t.ticket_key
                )
                ORDER BY t.created_date DESC
                LIMIT 50
            """, org_id)

            missing = [dict(row) for row in missing_decisions]

            # Statistics
            by_type = {}
            for ticket in missing:
                issue_type = ticket['issue_type'] or 'Unknown'
                by_type[issue_type] = by_type.get(issue_type, 0) + 1

            return {
                "total_missing_decisions": len(missing),
                "tickets": missing,
                "by_issue_type": by_type
            }

    async def find_stale_work(self, org_id: str, days: int = 30) -> Dict:
        """
        Find work items that haven't been updated recently.

        These might be:
        - Blocked work needing attention
        - Forgotten tasks
        - Work that should be closed

        Args:
            org_id: Organization ID
            days: Consider stale if no updates in N days (default 30)

        Returns:
            Dict with stale tickets and statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        async with self.db.pool.acquire() as conn:
            stale_tickets = await conn.fetch("""
                SELECT
                    t.id,
                    t.ticket_key,
                    t.summary,
                    t.status,
                    t.priority,
                    t.assignee,
                    t.created_date,
                    t.updated_date,
                    EXTRACT(DAY FROM NOW() - t.updated_date) as days_since_update
                FROM jira_tickets t
                WHERE t.organization_id = $1
                AND t.status NOT IN ('Done', 'Closed', 'Resolved', 'Cancelled')
                AND t.updated_date < $2
                ORDER BY t.updated_date ASC
                LIMIT 100
            """, org_id, cutoff_date)

            stale = [dict(row) for row in stale_tickets]

            # Statistics
            by_status = {}
            by_assignee = {}

            for ticket in stale:
                status = ticket['status'] or 'Unknown'
                assignee = ticket['assignee'] or 'Unassigned'

                by_status[status] = by_status.get(status, 0) + 1
                by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

            return {
                "total_stale": len(stale),
                "tickets": stale,
                "by_status": by_status,
                "by_assignee": by_assignee,
                "days_threshold": days
            }

    async def get_comprehensive_gaps(self, org_id: str) -> Dict:
        """
        Get all gaps at once for dashboard view.

        Args:
            org_id: Organization ID

        Returns:
            Dict with all gap types
        """
        orphaned = await self.find_orphaned_tickets(org_id)
        undocumented = await self.find_undocumented_features(org_id)
        missing_decisions = await self.find_missing_decisions(org_id)
        stale = await self.find_stale_work(org_id)

        return {
            "orphaned_tickets": orphaned,
            "undocumented_features": undocumented,
            "missing_decisions": missing_decisions,
            "stale_work": stale,
            "summary": {
                "total_orphaned": orphaned["total_orphaned"],
                "total_undocumented": undocumented["total_undocumented"],
                "total_missing_decisions": missing_decisions["total_missing_decisions"],
                "total_stale": stale["total_stale"]
            }
        }
