"""
Qdrant Collection Setup Service

Creates and manages Qdrant collections for multi-source semantic search.
This enables the AI to search across Confluence, Jira, Git commits, and code files.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class QdrantSetup:
    """
    Manages Qdrant collections for multi-source knowledge base.

    Collections:
    - confluence_docs: Already exists (Confluence pages)
    - jira_tickets: NEW - Jira tickets for semantic search
    - commits: NEW - Git commits for semantic search
    - code_files: NEW - Code files for semantic search
    - pull_requests: NEW - Pull requests for semantic search
    """

    def __init__(self, qdrant_client: QdrantClient):
        self.qdrant = qdrant_client
        self.vector_size = 384  # BAAI/bge-small-en-v1.5 embedding dimension

    async def create_all_collections(self) -> Dict[str, str]:
        """
        Create all required Qdrant collections if they don't exist.

        Returns:
            Dict with status for each collection (created, exists, or error)
        """
        collections = {
            "confluence_docs": "Confluence documentation pages",
            "jira_tickets": "Jira tickets and issues",
            "commits": "Git commit history",
            "code_files": "Source code files",
            "pull_requests": "Pull requests and merge requests"
        }

        results = {}

        for collection_name, description in collections.items():
            try:
                # Check if collection exists
                existing_collections = self.qdrant.get_collections()
                exists = any(c.name == collection_name for c in existing_collections.collections)

                if not exists:
                    # Create new collection
                    self.qdrant.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    results[collection_name] = "created"
                    logger.info(f"✅ Created collection: {collection_name} ({description})")
                else:
                    results[collection_name] = "exists"
                    logger.info(f"⏭️  Collection already exists: {collection_name}")

            except Exception as e:
                results[collection_name] = f"error: {str(e)}"
                logger.error(f"❌ Error creating collection {collection_name}: {e}")

        return results

    async def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """
        Get information about a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dict with collection info (vectors_count, points_count, etc.)
        """
        try:
            info = self.qdrant.get_collection(collection_name)

            collection_info = {
                "name": collection_name,
                "vectors_count": info.vectors_count if hasattr(info, 'vectors_count') else 0,
                "points_count": info.points_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status.status if hasattr(info, 'optimizer_status') else "unknown"
            }

            logger.info(f"📊 Collection: {collection_name}")
            logger.info(f"   Points: {collection_info['points_count']}")
            logger.info(f"   Vectors: {collection_info['vectors_count']}")

            return collection_info

        except Exception as e:
            logger.error(f"❌ Error getting collection info for {collection_name}: {e}")
            return None

    async def get_all_collections_info(self) -> Dict[str, Dict]:
        """
        Get information about all collections.

        Returns:
            Dict mapping collection names to their info
        """
        collections = [
            "confluence_docs",
            "jira_tickets",
            "commits",
            "code_files",
            "pull_requests"
        ]

        results = {}
        for collection_name in collections:
            info = await self.get_collection_info(collection_name)
            if info:
                results[collection_name] = info

        return results

    async def drop_collection(self, collection_name: str) -> bool:
        """
        Drop a collection (for testing/reset).

        WARNING: This deletes all data in the collection!

        Args:
            collection_name: Name of the collection to drop

        Returns:
            True if successful, False otherwise
        """
        try:
            self.qdrant.delete_collection(collection_name)
            logger.warning(f"🗑️  Dropped collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Error dropping collection {collection_name}: {e}")
            return False

    async def verify_setup(self) -> Dict[str, bool]:
        """
        Verify that all collections are properly set up.

        Returns:
            Dict mapping collection names to their existence status
        """
        required_collections = [
            "confluence_docs",
            "jira_tickets",
            "commits",
            "code_files",
            "pull_requests"
        ]

        results = {}

        try:
            existing_collections = self.qdrant.get_collections()
            existing_names = {c.name for c in existing_collections.collections}

            for collection_name in required_collections:
                results[collection_name] = collection_name in existing_names

            all_exist = all(results.values())

            if all_exist:
                logger.info("✅ All required collections exist")
            else:
                missing = [name for name, exists in results.items() if not exists]
                logger.warning(f"⚠️  Missing collections: {missing}")

        except Exception as e:
            logger.error(f"❌ Error verifying setup: {e}")

        return results

    async def get_storage_stats(self) -> Dict:
        """
        Get storage statistics across all collections.

        Returns:
            Dict with total points, estimated storage size, etc.
        """
        try:
            all_info = await self.get_all_collections_info()

            total_points = sum(info.get('points_count', 0) for info in all_info.values())

            # Rough estimate: each point is ~1.5KB (384 float32 + payload)
            estimated_size_mb = (total_points * 1.5) / 1024

            stats = {
                "total_collections": len(all_info),
                "total_points": total_points,
                "estimated_size_mb": round(estimated_size_mb, 2),
                "collections": all_info
            }

            logger.info(f"📊 Storage Stats:")
            logger.info(f"   Total collections: {stats['total_collections']}")
            logger.info(f"   Total points: {stats['total_points']}")
            logger.info(f"   Estimated size: {stats['estimated_size_mb']} MB")

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting storage stats: {e}")
            return {
                "error": str(e),
                "total_collections": 0,
                "total_points": 0,
                "estimated_size_mb": 0
            }


# Global instance (will be initialized in main.py)
qdrant_setup = None


def init_qdrant_setup(qdrant_client: QdrantClient) -> QdrantSetup:
    """
    Initialize the global Qdrant setup instance.

    Args:
        qdrant_client: Configured Qdrant client

    Returns:
        QdrantSetup instance
    """
    global qdrant_setup
    qdrant_setup = QdrantSetup(qdrant_client)
    logger.info("✅ Qdrant setup service initialized")
    return qdrant_setup
