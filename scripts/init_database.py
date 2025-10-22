#!/usr/bin/env python3
"""
Database initialization script
Executes the SQL file to create schema and seed data
"""
import os
import sys
import asyncpg
import asyncio


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
