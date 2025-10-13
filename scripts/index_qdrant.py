#!/usr/bin/env python3
"""
Index all PostgreSQL data into Qdrant for semantic search
"""

import asyncio
import asyncpg
import sys
import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

# Configuration
DB_CONFIG = {
    "host": "postgres",  # Docker service name
    "port": 5432,
    "user": "postgres",
    "password": "password",
    "database": "confluence_rag"
}

QDRANT_HOST = "qdrant"  # Docker service name
QDRANT_PORT = 6333
ORG_ID = "529d2ca9-6fd1-4fee-9105-dbde1499f937"

# Initialize embedding model
print("🔄 Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding model loaded")

# Initialize Qdrant client
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def create_collections():
    """Create Qdrant collections"""
    print("\n📦 Creating Qdrant collections...")

    collections = [
        "jira_tickets",
        "commits",
        "pull_requests",
        "code_files"
    ]

    for collection_name in collections:
        try:
            qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"  ✅ Created collection: {collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  ℹ️  Collection {collection_name} already exists")
            else:
                print(f"  ❌ Error creating {collection_name}: {e}")


async def index_jira_tickets():
    """Index Jira tickets into Qdrant"""
    print("\n🎫 Indexing Jira tickets...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        tickets = await conn.fetch("""
            SELECT id, ticket_key, summary, description, issue_type,
                   status, priority, assignee, labels, components
            FROM jira_tickets
            WHERE organization_id = $1
        """, ORG_ID)

        if not tickets:
            print("  ⚠️  No tickets found")
            return

        points = []
        for ticket in tickets:
            # Create searchable text
            text = f"{ticket['ticket_key']}: {ticket['summary']}\n\n{ticket['description'] or ''}"

            # Generate embedding
            embedding = embedder.encode(text).tolist()

            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "ticket_id": str(ticket['id']),
                    "ticket_key": ticket['ticket_key'],
                    "summary": ticket['summary'],
                    "description": ticket['description'],
                    "issue_type": ticket['issue_type'],
                    "status": ticket['status'],
                    "priority": ticket['priority'],
                    "assignee": ticket['assignee'],
                    "labels": ticket['labels'],
                    "components": ticket['components'],
                    "source_type": "jira",
                    "organization_id": ORG_ID
                }
            )
            points.append(point)

        # Upsert to Qdrant
        qdrant.upsert(
            collection_name="jira_tickets",
            points=points
        )

        print(f"  ✅ Indexed {len(points)} Jira tickets")

    finally:
        await conn.close()


async def index_commits():
    """Index commits into Qdrant"""
    print("\n📝 Indexing commits...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        commits = await conn.fetch("""
            SELECT id, sha, message, author_name, author_email,
                   commit_date, files_changed
            FROM commits
            WHERE organization_id = $1
        """, ORG_ID)

        if not commits:
            print("  ⚠️  No commits found")
            return

        points = []
        for commit in commits:
            # Create searchable text
            text = f"Commit {commit['sha'][:7]}: {commit['message']}\nFiles: {', '.join(commit['files_changed'] or [])}"

            # Generate embedding
            embedding = embedder.encode(text).tolist()

            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "commit_id": str(commit['id']),
                    "sha": commit['sha'],
                    "message": commit['message'],
                    "author_name": commit['author_name'],
                    "author_email": commit['author_email'],
                    "commit_date": str(commit['commit_date']),
                    "files_changed": commit['files_changed'],
                    "source_type": "commit",
                    "organization_id": ORG_ID
                }
            )
            points.append(point)

        # Upsert to Qdrant
        qdrant.upsert(
            collection_name="commits",
            points=points
        )

        print(f"  ✅ Indexed {len(points)} commits")

    finally:
        await conn.close()


async def index_pull_requests():
    """Index pull requests into Qdrant"""
    print("\n🔀 Indexing pull requests...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        prs = await conn.fetch("""
            SELECT id, pr_number, title, description, author_name,
                   state, created_at, merged_at
            FROM pull_requests
            WHERE organization_id = $1
        """, ORG_ID)

        if not prs:
            print("  ⚠️  No pull requests found")
            return

        points = []
        for pr in prs:
            # Create searchable text
            text = f"PR #{pr['pr_number']}: {pr['title']}\n\n{pr['description'] or ''}"

            # Generate embedding
            embedding = embedder.encode(text).tolist()

            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "pr_id": str(pr['id']),
                    "pr_number": pr['pr_number'],
                    "title": pr['title'],
                    "description": pr['description'],
                    "author_name": pr['author_name'],
                    "state": pr['state'],
                    "created_at": str(pr['created_at']),
                    "merged_at": str(pr['merged_at']) if pr['merged_at'] else None,
                    "source_type": "pull_request",
                    "organization_id": ORG_ID
                }
            )
            points.append(point)

        # Upsert to Qdrant
        qdrant.upsert(
            collection_name="pull_requests",
            points=points
        )

        print(f"  ✅ Indexed {len(points)} pull requests")

    finally:
        await conn.close()


async def index_code_files():
    """Index code files into Qdrant"""
    print("\n📂 Indexing code files...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        files = await conn.fetch("""
            SELECT id, file_path, file_name, file_type, language,
                   content, functions, classes, line_count
            FROM code_files
            WHERE organization_id = $1
        """, ORG_ID)

        if not files:
            print("  ⚠️  No code files found")
            return

        points = []
        for file in files:
            # Create searchable text
            text = f"{file['file_path']}\n\n{file['content'][:1000]}"  # First 1000 chars

            # Generate embedding
            embedding = embedder.encode(text).tolist()

            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "file_id": str(file['id']),
                    "file_path": file['file_path'],
                    "file_name": file['file_name'],
                    "file_type": file['file_type'],
                    "language": file['language'],
                    "content": file['content'][:2000],  # Store first 2000 chars
                    "functions": file['functions'],
                    "classes": file['classes'],
                    "line_count": file['line_count'],
                    "source_type": "code",
                    "organization_id": ORG_ID
                }
            )
            points.append(point)

        # Upsert to Qdrant
        qdrant.upsert(
            collection_name="code_files",
            points=points
        )

        print(f"  ✅ Indexed {len(points)} code files")

    finally:
        await conn.close()


async def main():
    """Main execution"""
    print("=" * 60)
    print("🚀 INDEXING DATA INTO QDRANT")
    print("=" * 60)

    # Create collections
    create_collections()

    # Index all data types
    await index_jira_tickets()
    await index_commits()
    await index_pull_requests()
    await index_code_files()

    # Verify
    print("\n" + "=" * 60)
    print("✅ INDEXING COMPLETE!")
    print("=" * 60)

    print("\n📊 Qdrant Collections:")
    for collection in ["jira_tickets", "commits", "pull_requests", "code_files"]:
        try:
            info = qdrant.get_collection(collection)
            print(f"  • {collection}: {info.points_count} points")
        except:
            print(f"  • {collection}: 0 points")

    print("\n🎯 Test semantic search:")
    print("  • Ask: 'How does authentication work?'")
    print("  • Ask: 'How was performance improved?'")
    print("  • Ask: 'Mobile sorting bug fix'")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
