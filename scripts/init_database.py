#!/usr/bin/env python3
"""
Database initialization script
Executes the SQL file to create schema and seed data, then indexes into Qdrant
"""
import os
import sys
import asyncpg
import asyncio
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid


def create_qdrant_collections(qdrant_client):
    """Create Qdrant collections for vector search"""
    print("\n📦 Creating Qdrant collections...")

    collections = [
        "jira_tickets",
        "commits",
        "pull_requests",
        "code_files"
    ]

    for collection_name in collections:
        try:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"  ✅ Created collection: {collection_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  ℹ️  Collection {collection_name} already exists, recreating...")
                qdrant_client.delete_collection(collection_name)
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"  ✅ Recreated collection: {collection_name}")
            else:
                print(f"  ❌ Error creating {collection_name}: {e}")


async def index_to_qdrant(conn, org_id, qdrant_client, embedder):
    """Index all data into Qdrant for semantic search"""
    print("\n🔍 Indexing data into Qdrant...")

    # Index Jira tickets
    print("  🎫 Indexing Jira tickets...")
    tickets = await conn.fetch("""
        SELECT id, ticket_key, summary, description, issue_type,
               status, priority, assignee, labels, components
        FROM jira_tickets
        WHERE organization_id = $1
    """, org_id)

    if tickets:
        points = []
        for ticket in tickets:
            text = f"{ticket['ticket_key']}: {ticket['summary']}\n\n{ticket['description'] or ''}"
            embedding = embedder.encode(text).tolist()

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
                    "organization_id": str(org_id)
                }
            )
            points.append(point)

        qdrant_client.upsert(collection_name="jira_tickets", points=points)
        print(f"    ✅ Indexed {len(points)} Jira tickets")

    # Index commits
    print("  📝 Indexing commits...")
    commits = await conn.fetch("""
        SELECT id, sha, message, author_name, author_email,
               commit_date, files_changed
        FROM commits
        WHERE organization_id = $1
    """, org_id)

    if commits:
        points = []
        for commit in commits:
            text = f"Commit {commit['sha'][:7]}: {commit['message']}\nFiles: {', '.join(commit['files_changed'] or [])}"
            embedding = embedder.encode(text).tolist()

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
                    "organization_id": str(org_id)
                }
            )
            points.append(point)

        qdrant_client.upsert(collection_name="commits", points=points)
        print(f"    ✅ Indexed {len(points)} commits")

    # Index pull requests
    print("  🔀 Indexing pull requests...")
    prs = await conn.fetch("""
        SELECT id, pr_number, title, description, author_name,
               state, created_at, merged_at
        FROM pull_requests
        WHERE organization_id = $1
    """, org_id)

    if prs:
        points = []
        for pr in prs:
            text = f"PR #{pr['pr_number']}: {pr['title']}\n\n{pr['description'] or ''}"
            embedding = embedder.encode(text).tolist()

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
                    "organization_id": str(org_id)
                }
            )
            points.append(point)

        qdrant_client.upsert(collection_name="pull_requests", points=points)
        print(f"    ✅ Indexed {len(points)} pull requests")

    # Index code files
    print("  📂 Indexing code files...")
    files = await conn.fetch("""
        SELECT id, file_path, file_name, file_type, language,
               content, functions, classes, line_count
        FROM code_files
        WHERE organization_id = $1
    """, org_id)

    if files:
        points = []
        for file in files:
            text = f"{file['file_path']}\n\n{file['content'][:1000]}"
            embedding = embedder.encode(text).tolist()

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "file_id": str(file['id']),
                    "file_path": file['file_path'],
                    "file_name": file['file_name'],
                    "file_type": file['file_type'],
                    "language": file['language'],
                    "content": file['content'][:2000],
                    "functions": file['functions'],
                    "classes": file['classes'],
                    "line_count": file['line_count'],
                    "source_type": "code",
                    "organization_id": str(org_id)
                }
            )
            points.append(point)

        qdrant_client.upsert(collection_name="code_files", points=points)
        print(f"    ✅ Indexed {len(points)} code files")


async def init_database():
    """Initialize database with schema and seed data"""

    # Database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/confluence_rag")

    # Parse connection URL
    # Format: postgresql://user:password@host:port/database
    parts = db_url.replace("postgresql://", "").split("@")
    user_pass = parts[0].split(":")
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")

    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 5432
    database = host_port_db[1] if len(host_port_db) > 1 else "confluence_rag"

    print("🔗 Connecting to database...")
    print(f"   Host: {host}:{port}")
    print(f"   Database: {database}")
    print(f"   User: {user}")

    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )

        print("✅ Connected to database")

        # Read SQL file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, "init_database.sql")

        print(f"📄 Reading SQL file: {sql_file}")

        with open(sql_file, 'r') as f:
            sql_content = f.read()

        print("🔄 Executing database initialization...")

        # Execute the SQL
        await conn.execute(sql_content)

        print("✅ Database initialization completed successfully!")

        # Get counts
        org_count = await conn.fetchval("SELECT COUNT(*) FROM organizations")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        repo_count = await conn.fetchval("SELECT COUNT(*) FROM repositories")
        ticket_count = await conn.fetchval("SELECT COUNT(*) FROM jira_tickets")
        commit_count = await conn.fetchval("SELECT COUNT(*) FROM commits")

        print("\n" + "=" * 60)
        print("DATABASE SUMMARY")
        print("=" * 60)
        print(f"Organizations: {org_count}")
        print(f"Users: {user_count}")
        print(f"Repositories: {repo_count}")
        print(f"Jira Tickets: {ticket_count}")
        print(f"Commits: {commit_count}")
        print("=" * 60)

        # Initialize Qdrant
        print("\n" + "=" * 60)
        print("INITIALIZING QDRANT VECTOR DATABASE")
        print("=" * 60)

        qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

        try:
            print(f"🔗 Connecting to Qdrant at {qdrant_host}:{qdrant_port}...")
            qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)

            print("🔄 Loading embedding model (all-MiniLM-L6-v2)...")
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embedding model loaded")

            # Create collections
            create_qdrant_collections(qdrant_client)

            # Get the organization ID for indexing
            org_id = await conn.fetchval("SELECT id FROM organizations LIMIT 1")

            if org_id:
                # Index all data
                await index_to_qdrant(conn, org_id, qdrant_client, embedder)

                # Verify indexing
                print("\n" + "=" * 60)
                print("QDRANT INDEXING COMPLETE")
                print("=" * 60)
                print("📊 Qdrant Collections:")
                for collection in ["jira_tickets", "commits", "pull_requests", "code_files"]:
                    try:
                        info = qdrant_client.get_collection(collection)
                        print(f"  • {collection}: {info.points_count} points")
                    except:
                        print(f"  • {collection}: 0 points")
                print("=" * 60)
            else:
                print("⚠️  No organization found, skipping Qdrant indexing")

        except Exception as e:
            print(f"⚠️  Warning: Could not initialize Qdrant: {e}")
            print("   Database initialization completed but vector search may not work.")

        print("\n📋 Login Credentials:")
        print("=" * 60)
        print("Admin User (Enterprise - Unlimited):")
        print("  Email: admin@acmecorp.com")
        print("  Password: admin123")
        print()
        print("Regular User (Pro - 10K requests):")
        print("  Email: user@acmecorp.com")
        print("  Password: user123")
        print()
        print("Demo User (Pro - 10K requests):")
        print("  Email: demo@example.com")
        print("  Password: demo123")
        print("=" * 60)

        await conn.close()

    except FileNotFoundError:
        print(f"❌ Error: SQL file not found at {sql_file}")
        sys.exit(1)
    except asyncpg.exceptions.PostgresError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database())
