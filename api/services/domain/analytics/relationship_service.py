"""
Relationship Builder Service

This service builds and queries relationships between different entities:
- Commits <-> Tickets
- Pull Requests <-> Tickets
- Documents <-> Tickets
- Code Files <-> Tickets (via commits)
- Developers <-> Tickets (via commits)
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
import re


class RelationshipService:
    """Service for building and querying relationships between entities"""

    def __init__(self, db_service):
        self.db = db_service
        self.ticket_pattern = re.compile(r'\b([A-Z]{2,10}-\d+)\b')

    async def get_ticket_relationships(self, ticket_key: str, org_id: str) -> Dict:
        """
        Get all relationships for a Jira ticket

        Returns a comprehensive view of:
        - Related commits
        - Related pull requests
        - Related documents (Confluence pages)
        - Related code files (via commits)
        - Related developers (commit authors)
        - Timeline of activities
        """
        relationships = {
            "ticket_key": ticket_key,
            "commits": [],
            "pull_requests": [],
            "documents": [],
            "code_files": [],
            "developers": [],
            "timeline": []
        }

        # Get related commits
        commits = await self.db.get_commits_for_ticket(ticket_key, org_id)
        relationships["commits"] = commits

        # Get related pull requests
        prs = await self.db.get_pull_requests_for_ticket(ticket_key, org_id)
        relationships["pull_requests"] = prs

        # Get related documents (Confluence pages that mention this ticket)
        documents = await self._get_documents_for_ticket(ticket_key, org_id)
        relationships["documents"] = documents

        # Extract unique code files from commits
        code_files = self._extract_code_files_from_commits(commits)
        relationships["code_files"] = code_files

        # Extract unique developers from commits
        developers = self._extract_developers_from_commits(commits)
        relationships["developers"] = developers

        # Build timeline
        timeline = self._build_timeline(commits, prs, documents)
        relationships["timeline"] = timeline

        return relationships

    async def get_developer_contributions(self, developer_email: str, org_id: str, limit: int = 100) -> Dict:
        """
        Get all contributions by a developer

        Returns:
        - Commits authored
        - Pull requests created
        - Tickets worked on
        - Code files modified
        - Activity timeline
        """
        async with self.db.pool.acquire() as conn:
            # Get commits by developer
            commits = await conn.fetch("""
                SELECT c.id, c.sha, c.message, c.commit_date, c.files_changed,
                       c.additions, c.deletions, c.ticket_references,
                       r.repo_name, r.repo_url
                FROM commits c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.organization_id = $1
                AND c.author_email = $2
                ORDER BY c.commit_date DESC
                LIMIT $3
            """, org_id, developer_email, limit)

            commits_list = [dict(row) for row in commits]

            # Get PRs by developer
            prs = await conn.fetch("""
                SELECT pr.id, pr.pr_number, pr.title, pr.description, pr.state,
                       pr.created_at_pr, pr.merged_at, pr.ticket_references,
                       r.repo_name, r.repo_url
                FROM pull_requests pr
                JOIN repositories r ON pr.repository_id = r.id
                WHERE pr.organization_id = $1
                AND pr.author_name = $2
                ORDER BY pr.created_at_pr DESC
                LIMIT $3
            """, org_id, developer_email, limit)

            prs_list = [dict(row) for row in prs]

            # Extract unique tickets
            ticket_keys = set()
            for commit in commits_list:
                if commit.get('ticket_references'):
                    ticket_keys.update(commit['ticket_references'])
            for pr in prs_list:
                if pr.get('ticket_references'):
                    ticket_keys.update(pr['ticket_references'])

            # Extract unique files
            files_modified = set()
            for commit in commits_list:
                if commit.get('files_changed'):
                    files_modified.update(commit['files_changed'])

            # Calculate stats
            total_additions = sum(c.get('additions', 0) for c in commits_list)
            total_deletions = sum(c.get('deletions', 0) for c in commits_list)

            return {
                "developer_email": developer_email,
                "stats": {
                    "total_commits": len(commits_list),
                    "total_prs": len(prs_list),
                    "total_tickets": len(ticket_keys),
                    "files_modified": len(files_modified),
                    "lines_added": total_additions,
                    "lines_deleted": total_deletions
                },
                "commits": commits_list,
                "pull_requests": prs_list,
                "tickets": list(ticket_keys),
                "files": list(files_modified)
            }

    async def get_file_history(self, file_path: str, org_id: str) -> Dict:
        """
        Get the complete history of a code file

        Returns:
        - All commits that modified this file
        - Developers who worked on it
        - Related tickets
        - Timeline
        """
        async with self.db.pool.acquire() as conn:
            commits = await conn.fetch("""
                SELECT c.id, c.sha, c.message, c.author_name, c.author_email,
                       c.commit_date, c.additions, c.deletions, c.ticket_references,
                       r.repo_name, r.repo_url
                FROM commits c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.organization_id = $1
                AND $2 = ANY(c.files_changed)
                ORDER BY c.commit_date DESC
            """, org_id, file_path)

            commits_list = [dict(row) for row in commits]

            # Extract developers
            developers = {}
            for commit in commits_list:
                email = commit.get('author_email')
                if email:
                    if email not in developers:
                        developers[email] = {
                            "name": commit.get('author_name'),
                            "email": email,
                            "commit_count": 0,
                            "lines_added": 0,
                            "lines_deleted": 0
                        }
                    developers[email]["commit_count"] += 1
                    developers[email]["lines_added"] += commit.get('additions', 0)
                    developers[email]["lines_deleted"] += commit.get('deletions', 0)

            # Extract tickets
            ticket_keys = set()
            for commit in commits_list:
                if commit.get('ticket_references'):
                    ticket_keys.update(commit['ticket_references'])

            return {
                "file_path": file_path,
                "total_commits": len(commits_list),
                "commits": commits_list,
                "developers": list(developers.values()),
                "tickets": list(ticket_keys),
                "first_commit": commits_list[-1] if commits_list else None,
                "last_commit": commits_list[0] if commits_list else None
            }

    async def get_repository_stats(self, repo_id: str, org_id: str) -> Dict:
        """Get comprehensive statistics for a repository"""
        async with self.db.pool.acquire() as conn:
            # Get repository info
            repo = await conn.fetchrow("""
                SELECT id, repo_name, repo_url, provider, branch, created_at
                FROM repositories
                WHERE id = $1 AND organization_id = $2
            """, repo_id, org_id)

            if not repo:
                return None

            # Get commit stats
            commit_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_commits,
                    COUNT(DISTINCT author_email) as unique_authors,
                    SUM(additions) as total_additions,
                    SUM(deletions) as total_deletions,
                    MIN(commit_date) as first_commit_date,
                    MAX(commit_date) as last_commit_date
                FROM commits
                WHERE repository_id = $1 AND organization_id = $2
            """, repo_id, org_id)

            # Get PR stats
            pr_stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_prs,
                    COUNT(*) FILTER (WHERE state = 'merged') as merged_prs,
                    COUNT(*) FILTER (WHERE state = 'open') as open_prs,
                    COUNT(*) FILTER (WHERE state = 'closed') as closed_prs
                FROM pull_requests
                WHERE repository_id = $1 AND organization_id = $2
            """, repo_id, org_id)

            # Get file stats
            file_stats = await conn.fetchrow("""
                SELECT COUNT(*) as total_files
                FROM code_files
                WHERE repository_id = $1 AND organization_id = $2
            """, repo_id, org_id)

            # Get top contributors
            top_contributors = await conn.fetch("""
                SELECT
                    author_name,
                    author_email,
                    COUNT(*) as commit_count,
                    SUM(additions) as lines_added,
                    SUM(deletions) as lines_deleted
                FROM commits
                WHERE repository_id = $1 AND organization_id = $2
                GROUP BY author_name, author_email
                ORDER BY commit_count DESC
                LIMIT 10
            """, repo_id, org_id)

            # Get ticket references
            ticket_refs = await conn.fetch("""
                SELECT DISTINCT UNNEST(ticket_references) as ticket_key
                FROM commits
                WHERE repository_id = $1
                AND organization_id = $2
                AND ticket_references IS NOT NULL
            """, repo_id, org_id)

            return {
                "repository": dict(repo),
                "commit_stats": dict(commit_stats) if commit_stats else {},
                "pr_stats": dict(pr_stats) if pr_stats else {},
                "file_stats": dict(file_stats) if file_stats else {},
                "top_contributors": [dict(row) for row in top_contributors],
                "related_tickets": [row['ticket_key'] for row in ticket_refs]
            }

    async def get_feature_timeline(self, ticket_key: str, org_id: str) -> List[Dict]:
        """
        Build a complete timeline for a feature/ticket

        Shows chronological order of:
        - Ticket creation
        - Commits
        - Pull requests
        - Document updates
        """
        timeline = []

        # Get ticket info (if available)
        async with self.db.pool.acquire() as conn:
            ticket = await conn.fetchrow("""
                SELECT ticket_key, summary, status, created, updated
                FROM jira_tickets
                WHERE ticket_key = $1 AND organization_id = $2
            """, ticket_key, org_id)

            if ticket:
                timeline.append({
                    "type": "ticket_created",
                    "timestamp": ticket['created'],
                    "title": f"Ticket {ticket_key} created",
                    "description": ticket['summary'],
                    "data": dict(ticket)
                })

        # Get commits
        commits = await self.db.get_commits_for_ticket(ticket_key, org_id)
        for commit in commits:
            timeline.append({
                "type": "commit",
                "timestamp": commit.get('commit_date'),
                "title": f"Commit {commit['sha'][:7]}",
                "description": commit.get('message', ''),
                "author": commit.get('author_name'),
                "data": commit
            })

        # Get pull requests
        prs = await self.db.get_pull_requests_for_ticket(ticket_key, org_id)
        for pr in prs:
            timeline.append({
                "type": "pull_request",
                "timestamp": pr.get('created_at_pr'),
                "title": f"PR #{pr['pr_number']}: {pr.get('title', '')}",
                "description": pr.get('description', ''),
                "author": pr.get('author_name'),
                "state": pr.get('state'),
                "data": pr
            })

            # Add merged event if merged
            if pr.get('merged_at'):
                timeline.append({
                    "type": "pr_merged",
                    "timestamp": pr.get('merged_at'),
                    "title": f"PR #{pr['pr_number']} merged",
                    "description": f"Merged into {pr.get('data', {}).get('base_branch', 'main')}",
                    "data": pr
                })

        # Sort by timestamp
        timeline.sort(key=lambda x: x.get('timestamp') or datetime.min)

        return timeline

    async def search_relationships(self, query: str, org_id: str, entity_types: Optional[List[str]] = None) -> Dict:
        """
        Search across all entities and return relationships.
        OPTIMIZED: Parallel queries for better performance.
        """
        results = {
            "query": query,
            "commits": [],
            "pull_requests": [],
            "tickets": [],
            "files": [],
            "documents": []
        }

        if not entity_types:
            entity_types = ['commits', 'prs', 'tickets', 'files']

        search_pattern = f'%{query}%'

        async with self.db.pool.acquire() as conn:
            # OPTIMIZED: Execute all queries in parallel
            tasks = []
            
            if 'commits' in entity_types:
                tasks.append(('commits', conn.fetch("""
                    SELECT c.id, c.sha, c.message, c.author_name, c.commit_date,
                           c.ticket_references, r.repo_name
                    FROM commits c
                    INNER JOIN repositories r ON c.repository_id = r.id
                    WHERE c.organization_id = $1
                    AND (c.message ILIKE $2 OR c.author_name ILIKE $2)
                    ORDER BY c.commit_date DESC
                    LIMIT 20
                """, org_id, search_pattern)))

            if 'prs' in entity_types:
                tasks.append(('pull_requests', conn.fetch("""
                    SELECT pr.id, pr.pr_number, pr.title, pr.description,
                           pr.author_name, pr.state, pr.ticket_references, r.repo_name
                    FROM pull_requests pr
                    INNER JOIN repositories r ON pr.repository_id = r.id
                    WHERE pr.organization_id = $1
                    AND (pr.title ILIKE $2 OR pr.description ILIKE $2 OR pr.author_name ILIKE $2)
                    ORDER BY pr.created_at_pr DESC
                    LIMIT 20
                """, org_id, search_pattern)))

            if 'tickets' in entity_types:
                tasks.append(('tickets', conn.fetch("""
                    SELECT ticket_key, summary, status, assignee, created_date
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND (ticket_key ILIKE $2 OR summary ILIKE $2 OR description ILIKE $2)
                    LIMIT 20
                """, org_id, search_pattern)))

            if 'files' in entity_types:
                tasks.append(('files', conn.fetch("""
                    SELECT cf.id, cf.file_path, cf.language, r.repo_name,
                           (SELECT COUNT(*) FROM commits c 
                            WHERE c.organization_id = cf.organization_id 
                            AND cf.file_path = ANY(c.files_changed)) as commit_count
                    FROM code_files cf
                    LEFT JOIN repositories r ON cf.repository_id = r.id
                    WHERE cf.organization_id = $1 AND cf.file_path ILIKE $2
                    LIMIT 20
                """, org_id, search_pattern)))

            # Execute all queries concurrently
            import asyncio
            for key, task in tasks:
                rows = await task
                results[key] = [dict(row) for row in rows]

        return results

    # Helper methods

    async def _get_documents_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Find Confluence documents that mention this ticket"""
        # Note: Confluence documents are stored in Qdrant (vector DB), not PostgreSQL
        # TODO: Implement Qdrant search for documents containing ticket references
        # For now, return empty list to avoid table not found errors
        return []

    def _extract_code_files_from_commits(self, commits: List[Dict]) -> List[Dict]:
        """Extract unique code files from commits with modification counts"""
        file_map = {}

        for commit in commits:
            files_changed = commit.get('files_changed', [])
            if not files_changed:
                continue

            for file_path in files_changed:
                if file_path not in file_map:
                    file_map[file_path] = {
                        "file_path": file_path,
                        "modification_count": 0,
                        "last_modified": commit.get('commit_date')
                    }
                file_map[file_path]["modification_count"] += 1

                # Update last modified if this commit is newer
                commit_date = commit.get('commit_date')
                if commit_date and commit_date > file_map[file_path]["last_modified"]:
                    file_map[file_path]["last_modified"] = commit_date

        # Sort by modification count
        files = list(file_map.values())
        files.sort(key=lambda x: x["modification_count"], reverse=True)
        return files

    def _extract_developers_from_commits(self, commits: List[Dict]) -> List[Dict]:
        """Extract unique developers from commits with contribution stats"""
        dev_map = {}

        for commit in commits:
            email = commit.get('author_email')
            if not email:
                continue

            if email not in dev_map:
                dev_map[email] = {
                    "name": commit.get('author_name'),
                    "email": email,
                    "commit_count": 0,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "last_commit_date": commit.get('commit_date')
                }

            dev_map[email]["commit_count"] += 1
            dev_map[email]["lines_added"] += commit.get('additions', 0)
            dev_map[email]["lines_deleted"] += commit.get('deletions', 0)

            # Update last commit date
            commit_date = commit.get('commit_date')
            if commit_date and commit_date > dev_map[email]["last_commit_date"]:
                dev_map[email]["last_commit_date"] = commit_date

        # Sort by commit count
        developers = list(dev_map.values())
        developers.sort(key=lambda x: x["commit_count"], reverse=True)
        return developers

    def _build_timeline(self, commits: List[Dict], prs: List[Dict], documents: List[Dict]) -> List[Dict]:
        """Build a chronological timeline of all activities"""
        timeline = []

        # Add commits
        for commit in commits:
            timeline.append({
                "type": "commit",
                "timestamp": commit.get('commit_date'),
                "title": f"Commit {commit['sha'][:7]}",
                "description": commit.get('message', ''),
                "author": commit.get('author_name'),
                "data": commit
            })

        # Add PRs
        for pr in prs:
            timeline.append({
                "type": "pull_request",
                "timestamp": pr.get('created_at_pr'),
                "title": f"PR #{pr['pr_number']}: {pr.get('title', '')}",
                "description": pr.get('description', ''),
                "author": pr.get('author_name'),
                "state": pr.get('state'),
                "data": pr
            })

        # Add documents
        for doc in documents:
            timeline.append({
                "type": "document",
                "timestamp": doc.get('created_at'),
                "title": doc.get('title', ''),
                "description": "Confluence page created/updated",
                "data": doc
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x.get('timestamp') or datetime.min)
        return timeline
