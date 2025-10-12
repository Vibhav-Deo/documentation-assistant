"""
Qdrant Indexing Service

Handles indexing of various entities into Qdrant for semantic search.
This enables the AI to search across Jira tickets, commits, code files, and PRs
using natural language queries.

Core USP: Multi-source search to find features/enhancements/bugfixes across
Confluence, Jira, and code repositories.
"""

from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
import uuid
import logging

logger = logging.getLogger(__name__)


class QdrantIndexer:
    """
    Indexes entities into Qdrant for semantic search.

    Supports:
    - Jira tickets (Phase 2)
    - Git commits (Phase 3)
    - Code files (Phase 4)
    - Pull requests (Phase 4)
    """

    def __init__(self, qdrant_client: QdrantClient, embedder: SentenceTransformer):
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.vector_size = 384  # BAAI/bge-small-en-v1.5

    # ========================================================================
    # PHASE 2: JIRA TICKETS INDEXING
    # ========================================================================

    async def index_jira_ticket(self, ticket: Dict, org_id: str) -> bool:
        """
        Index a single Jira ticket in Qdrant for semantic search.

        Args:
            ticket: Dict with ticket data (ticket_key, summary, description, etc.)
            org_id: Organization ID for isolation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create searchable text from ticket
            # Combine key fields for better semantic matching
            text_parts = [
                ticket.get('ticket_key', ''),
                ticket.get('summary', ''),
                ticket.get('description', ''),
                ticket.get('issue_type', ''),
                ' '.join(ticket.get('labels', [])),
                ' '.join(ticket.get('components', []))
            ]

            # Filter out empty strings and join
            text = ' '.join(part for part in text_parts if part)

            # Generate embedding
            vector = self.embedder.encode(text).tolist()

            # Create point with metadata
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "entity_type": "jira_ticket",
                    "organization_id": org_id,
                    "ticket_key": ticket.get('ticket_key', ''),
                    "summary": ticket.get('summary', ''),
                    "description": ticket.get('description', '')[:500],  # Limit size
                    "status": ticket.get('status', ''),
                    "assignee": ticket.get('assignee', ''),
                    "reporter": ticket.get('reporter', ''),
                    "issue_type": ticket.get('issue_type', ''),
                    "priority": ticket.get('priority', ''),
                    "labels": ticket.get('labels', []),
                    "components": ticket.get('components', []),
                    "created_date": str(ticket.get('created_date', '')),
                    "updated_date": str(ticket.get('updated_date', '')),
                    "resolved_date": str(ticket.get('resolved_date', ''))
                }
            )

            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name="jira_tickets",
                points=[point]
            )

            logger.info(f"✅ Indexed Jira ticket: {ticket.get('ticket_key')}")
            return True

        except Exception as e:
            logger.error(f"❌ Error indexing ticket {ticket.get('ticket_key')}: {e}")
            return False

    async def index_jira_tickets_batch(self, tickets: List[Dict], org_id: str) -> int:
        """
        Index multiple Jira tickets in batch for better performance.

        Args:
            tickets: List of ticket dicts
            org_id: Organization ID

        Returns:
            Number of successfully indexed tickets
        """
        points = []
        successful = 0

        for ticket in tickets:
            try:
                # Create searchable text
                text_parts = [
                    ticket.get('ticket_key', ''),
                    ticket.get('summary', ''),
                    ticket.get('description', ''),
                    ticket.get('issue_type', ''),
                    ' '.join(ticket.get('labels', [])),
                    ' '.join(ticket.get('components', []))
                ]
                text = ' '.join(part for part in text_parts if part)

                # Generate embedding
                vector = self.embedder.encode(text).tolist()

                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "entity_type": "jira_ticket",
                        "organization_id": org_id,
                        "ticket_key": ticket.get('ticket_key', ''),
                        "summary": ticket.get('summary', ''),
                        "description": ticket.get('description', '')[:500],
                        "status": ticket.get('status', ''),
                        "assignee": ticket.get('assignee', ''),
                        "issue_type": ticket.get('issue_type', ''),
                        "priority": ticket.get('priority', ''),
                        "created_date": str(ticket.get('created_date', ''))
                    }
                )
                points.append(point)

            except Exception as e:
                logger.error(f"❌ Error preparing ticket {ticket.get('ticket_key')}: {e}")
                continue

        # Batch upsert
        if points:
            try:
                self.qdrant.upsert(
                    collection_name="jira_tickets",
                    points=points
                )
                successful = len(points)
                logger.info(f"✅ Batch indexed {successful} Jira tickets")
            except Exception as e:
                logger.error(f"❌ Error batch indexing tickets: {e}")
                return 0

        return successful

    async def search_jira_tickets(
        self,
        query: str,
        org_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search Jira tickets using semantic search.

        This enables queries like:
        - "authentication issues" → Finds tickets about login, auth, security
        - "payment bugs" → Finds tickets about billing, transactions, checkout

        Args:
            query: Natural language search query
            org_id: Organization ID for filtering
            limit: Max results to return

        Returns:
            List of matching tickets with relevance scores
        """
        try:
            # Generate query embedding
            query_vector = self.embedder.encode(query).tolist()

            # Search in Qdrant with organization filter
            results = self.qdrant.search(
                collection_name="jira_tickets",
                query_vector=query_vector,
                limit=limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="organization_id",
                            match=MatchValue(value=org_id)
                        )
                    ]
                )
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "ticket_key": result.payload.get("ticket_key"),
                    "summary": result.payload.get("summary"),
                    "description": result.payload.get("description", "")[:200] + "...",
                    "status": result.payload.get("status"),
                    "assignee": result.payload.get("assignee"),
                    "issue_type": result.payload.get("issue_type"),
                    "priority": result.payload.get("priority")
                })

            logger.info(f"🔍 Found {len(formatted_results)} tickets for query: '{query}'")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Error searching Jira tickets: {e}")
            return []

    # ========================================================================
    # PHASE 3: GIT COMMITS INDEXING
    # ========================================================================

    async def index_commit(self, commit: Dict, org_id: str) -> bool:
        """
        Index a single Git commit in Qdrant for semantic search.

        Args:
            commit: Dict with commit data (sha, message, author, etc.)
            org_id: Organization ID for isolation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create searchable text from commit
            # Combine message, author, and file paths for better semantic matching
            text_parts = [
                commit.get('message', ''),
                commit.get('author_name', ''),
                ' '.join(commit.get('files_changed', [])),
                ' '.join(commit.get('ticket_references', []))
            ]

            # Filter out empty strings and join
            text = ' '.join(part for part in text_parts if part)

            # Generate embedding
            vector = self.embedder.encode(text).tolist()

            # Create point with metadata
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "entity_type": "commit",
                    "organization_id": org_id,
                    "sha": commit.get('sha', ''),
                    "short_sha": commit.get('sha', '')[:7],
                    "message": commit.get('message', ''),
                    "author_name": commit.get('author_name', ''),
                    "author_email": commit.get('author_email', ''),
                    "commit_date": str(commit.get('commit_date', '')),
                    "files_changed": commit.get('files_changed', [])[:20],  # Limit array size
                    "additions": commit.get('additions', 0),
                    "deletions": commit.get('deletions', 0),
                    "ticket_references": commit.get('ticket_references', []),
                    "repository_id": str(commit.get('repository_id', ''))
                }
            )

            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name="commits",
                points=[point]
            )

            logger.info(f"✅ Indexed commit: {commit.get('sha', '')[:7]}")
            return True

        except Exception as e:
            logger.error(f"❌ Error indexing commit {commit.get('sha', '')[:7]}: {e}")
            return False

    async def index_commits_batch(self, commits: List[Dict], org_id: str) -> int:
        """
        Index multiple Git commits in batch for better performance.

        Args:
            commits: List of commit dicts
            org_id: Organization ID

        Returns:
            Number of successfully indexed commits
        """
        points = []
        successful = 0

        for commit in commits:
            try:
                # Create searchable text
                text_parts = [
                    commit.get('message', ''),
                    commit.get('author_name', ''),
                    ' '.join(commit.get('files_changed', [])),
                    ' '.join(commit.get('ticket_references', []))
                ]
                text = ' '.join(part for part in text_parts if part)

                # Generate embedding
                vector = self.embedder.encode(text).tolist()

                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "entity_type": "commit",
                        "organization_id": org_id,
                        "sha": commit.get('sha', ''),
                        "short_sha": commit.get('sha', '')[:7],
                        "message": commit.get('message', ''),
                        "author_name": commit.get('author_name', ''),
                        "author_email": commit.get('author_email', ''),
                        "commit_date": str(commit.get('commit_date', '')),
                        "files_changed": commit.get('files_changed', [])[:20],
                        "ticket_references": commit.get('ticket_references', []),
                        "repository_id": str(commit.get('repository_id', ''))
                    }
                )
                points.append(point)

            except Exception as e:
                logger.error(f"❌ Error preparing commit {commit.get('sha', '')[:7]}: {e}")
                continue

        # Batch upsert
        if points:
            try:
                self.qdrant.upsert(
                    collection_name="commits",
                    points=points
                )
                successful = len(points)
                logger.info(f"✅ Batch indexed {successful} commits")
            except Exception as e:
                logger.error(f"❌ Error batch indexing commits: {e}")
                return 0

        return successful

    async def search_commits(
        self,
        query: str,
        org_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search Git commits using semantic search.

        This enables queries like:
        - "user authentication" → Finds commits about login, auth, security
        - "payment processing" → Finds commits about billing, checkout, stripe
        - "bug fixes" → Finds commits with bug-related messages

        Args:
            query: Natural language search query
            org_id: Organization ID for filtering
            limit: Max results to return

        Returns:
            List of matching commits with relevance scores
        """
        try:
            # Generate query embedding
            query_vector = self.embedder.encode(query).tolist()

            # Search in Qdrant with organization filter
            results = self.qdrant.search(
                collection_name="commits",
                query_vector=query_vector,
                limit=limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="organization_id",
                            match=MatchValue(value=org_id)
                        )
                    ]
                )
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "sha": result.payload.get("sha"),
                    "short_sha": result.payload.get("short_sha"),
                    "message": result.payload.get("message", "")[:200] + "...",
                    "author_name": result.payload.get("author_name"),
                    "author_email": result.payload.get("author_email"),
                    "commit_date": result.payload.get("commit_date"),
                    "files_changed": result.payload.get("files_changed", []),
                    "ticket_references": result.payload.get("ticket_references", [])
                })

            logger.info(f"🔍 Found {len(formatted_results)} commits for query: '{query}'")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Error searching commits: {e}")
            return []

    # ========================================================================
    # PHASE 4: CODE FILES INDEXING
    # ========================================================================

    async def index_code_file(self, file: Dict, org_id: str) -> bool:
        """
        Index a code file in Qdrant for semantic search.

        Args:
            file: Dict with file data (file_path, language, functions, etc.)
            org_id: Organization ID for isolation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create searchable text from file metadata
            # Combine file path, language, functions, and classes for better semantic matching
            text_parts = [
                file.get('file_path', ''),
                file.get('language', ''),
            ]

            # Add function names if available
            if file.get('functions'):
                func_names = [f.get('name', '') for f in file.get('functions', [])]
                text_parts.append(' '.join(func_names))

            # Add class names if available
            if file.get('classes'):
                class_names = [c.get('name', '') for c in file.get('classes', [])]
                text_parts.append(' '.join(class_names))

            # Filter out empty strings and join
            text = ' '.join(part for part in text_parts if part)

            # Generate embedding
            vector = self.embedder.encode(text).tolist()

            # Create point with metadata
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "entity_type": "code_file",
                    "organization_id": org_id,
                    "file_path": file.get('file_path', ''),
                    "language": file.get('language', ''),
                    "size_bytes": file.get('size_bytes', 0),
                    "functions": [f.get('name', '') for f in file.get('functions', [])][:50],  # Limit array
                    "classes": [c.get('name', '') for c in file.get('classes', [])][:50],  # Limit array
                    "repository_id": str(file.get('repository_id', ''))
                }
            )

            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name="code_files",
                points=[point]
            )

            logger.info(f"✅ Indexed code file: {file.get('file_path', '')}")
            return True

        except Exception as e:
            logger.error(f"❌ Error indexing file {file.get('file_path', '')}: {e}")
            return False

    async def index_code_files_batch(self, files: List[Dict], org_id: str) -> int:
        """
        Index multiple code files in batch for better performance.

        Args:
            files: List of file dicts
            org_id: Organization ID

        Returns:
            Number of successfully indexed files
        """
        points = []
        successful = 0

        for file in files:
            try:
                # Create searchable text
                text_parts = [
                    file.get('file_path', ''),
                    file.get('language', ''),
                ]

                # Add function and class names
                if file.get('functions'):
                    func_names = [f.get('name', '') for f in file.get('functions', [])]
                    text_parts.append(' '.join(func_names))
                if file.get('classes'):
                    class_names = [c.get('name', '') for c in file.get('classes', [])]
                    text_parts.append(' '.join(class_names))

                text = ' '.join(part for part in text_parts if part)

                # Generate embedding
                vector = self.embedder.encode(text).tolist()

                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "entity_type": "code_file",
                        "organization_id": org_id,
                        "file_path": file.get('file_path', ''),
                        "language": file.get('language', ''),
                        "size_bytes": file.get('size_bytes', 0),
                        "functions": [f.get('name', '') for f in file.get('functions', [])][:50],
                        "classes": [c.get('name', '') for c in file.get('classes', [])][:50],
                        "repository_id": str(file.get('repository_id', ''))
                    }
                )
                points.append(point)

            except Exception as e:
                logger.error(f"❌ Error preparing file {file.get('file_path', '')}: {e}")
                continue

        # Batch upsert
        if points:
            try:
                self.qdrant.upsert(
                    collection_name="code_files",
                    points=points
                )
                successful = len(points)
                logger.info(f"✅ Batch indexed {successful} code files")
            except Exception as e:
                logger.error(f"❌ Error batch indexing files: {e}")
                return 0

        return successful

    async def search_code_files(
        self,
        query: str,
        org_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search code files using semantic search.

        This enables queries like:
        - "authentication service" → Finds auth-related files
        - "payment processing" → Finds payment/billing files
        - "database connection" → Finds DB-related files
        - "user management" → Finds user/account files

        Args:
            query: Natural language search query
            org_id: Organization ID for filtering
            limit: Max results to return

        Returns:
            List of matching files with relevance scores
        """
        try:
            # Generate query embedding
            query_vector = self.embedder.encode(query).tolist()

            # Search in Qdrant with organization filter
            results = self.qdrant.search(
                collection_name="code_files",
                query_vector=query_vector,
                limit=limit,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="organization_id",
                            match=MatchValue(value=org_id)
                        )
                    ]
                )
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "file_path": result.payload.get("file_path"),
                    "language": result.payload.get("language"),
                    "size_bytes": result.payload.get("size_bytes"),
                    "functions": result.payload.get("functions", []),
                    "classes": result.payload.get("classes", []),
                    "repository_id": result.payload.get("repository_id")
                })

            logger.info(f"🔍 Found {len(formatted_results)} code files for query: '{query}'")
            return formatted_results

        except Exception as e:
            logger.error(f"❌ Error searching code files: {e}")
            return []

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def delete_by_organization(self, collection_name: str, org_id: str) -> bool:
        """
        Delete all points for an organization from a collection.

        Useful for org cleanup or re-indexing.
        """
        try:
            # Qdrant doesn't support delete by filter in all versions
            # This is a placeholder - might need to be implemented differently
            logger.warning(f"⚠️  Delete by organization not fully implemented for {collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting from {collection_name}: {e}")
            return False

    async def get_collection_count(self, collection_name: str, org_id: str) -> int:
        """
        Get count of indexed items for an organization in a collection.
        """
        try:
            # This is an approximation - Qdrant doesn't support count with filters easily
            # Could be improved with scroll and count
            result = self.qdrant.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="organization_id",
                            match=MatchValue(value=org_id)
                        )
                    ]
                ),
                limit=1
            )

            # This only gives us partial info
            logger.info(f"📊 Collection {collection_name} has items for org {org_id}")
            return 0  # Placeholder

        except Exception as e:
            logger.error(f"❌ Error getting count for {collection_name}: {e}")
            return 0


# Global instance (will be initialized in main.py)
qdrant_indexer = None


def init_qdrant_indexer(
    qdrant_client: QdrantClient,
    embedder: SentenceTransformer
) -> QdrantIndexer:
    """
    Initialize the global Qdrant indexer instance.

    Args:
        qdrant_client: Configured Qdrant client
        embedder: SentenceTransformer model for embeddings

    Returns:
        QdrantIndexer instance
    """
    global qdrant_indexer
    qdrant_indexer = QdrantIndexer(qdrant_client, embedder)
    logger.info("✅ Qdrant indexer service initialized")
    return qdrant_indexer
