# Database Initialization

This directory contains the database initialization scripts that replace the previous migration-based approach.

## Files

- **init_database.sql** - Complete SQL script that creates all tables, indexes, and seeds initial data
- **init_database.py** - Python script that executes the SQL file

## Usage

### Option 1: Using start.sh (Recommended)

```bash
./start.sh --init-db
```

This will start all services and initialize the database with schema and seed data.

### Option 2: Standalone execution

If you need to reinitialize the database without restarting services:

```bash
# Make sure PostgreSQL is running
python3 scripts/init_database.py
```

Or directly via psql:

```bash
psql -U postgres -d confluence_rag -f scripts/init_database.sql
```

### Option 3: Via Docker

```bash
docker compose exec -T postgres psql -U postgres -d confluence_rag -f /scripts/init_database.sql
```

## What Gets Created

### Schema
- Organizations table
- Users table
- Repositories table
- Jira tickets table
- Commits table
- Code files table
- Pull requests table
- Decisions table
- Audit logs table
- All necessary indexes (B-tree, GIN, trigram)

### Seed Data
- 2 Organizations (Acme Corp, Demo Organization)
- 3 Users with credentials:
  - `admin@acmecorp.com` / `admin123` (Admin role, Enterprise plan)
  - `user@acmecorp.com` / `user123` (User role, Pro plan)
  - `demo@example.com` / `demo123` (User role, Pro plan)
- 4 Repositories (backend-api, frontend-web, mobile-app, infrastructure)
- 30 Jira tickets across different categories (AUTH, DB, UI, API, MOB, INFRA)
- 20+ commits with ticket references
- Realistic project data for testing all features

## Reset Database

To completely reset the database:

```bash
docker compose down -v
docker compose up -d
./start.sh --init-db
```

This will:
1. Stop all services and remove volumes
2. Start services again
3. Initialize a fresh database with schema and seed data

## Notes

- The script is idempotent - it drops existing tables before creating new ones
- Password hashes use bcrypt with the demo passwords shown above
- Organization IDs and repository IDs are fixed UUIDs for consistency
- All timestamps use PostgreSQL's CURRENT_TIMESTAMP
- The script creates comprehensive indexes for optimal performance
