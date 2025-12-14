# Database Initialization & Data Seeding

This directory contains database initialization scripts and comprehensive data seeding for development.

## Files

- **init_database.sql** - Complete SQL script that creates all tables, indexes, and seeds basic data
- **init_database.py** - Python script that executes the SQL file
- **purge_and_seed.py** - Alternative comprehensive seeding script (standalone)
- **index_qdrant.py** - Qdrant vector database indexing script

## Automatic Development Data Seeding

**🚀 NEW: Automatic Comprehensive Data Seeding**

When running in development mode (`ENVIRONMENT=development`), the API automatically seeds comprehensive data during startup. This includes:

- **50+ Enhanced Tickets** across all feature categories (PRED, TAG, INTENT, GAP, etc.)
- **Realistic Commits** with proper ticket relationships and orphaned examples
- **Complex Decisions** with stakeholder conflicts for intent analysis testing
- **Code Files** for impact analysis
- **Orphaned Data** for gap detection testing

### How It Works

1. **Automatic Detection**: Checks if running in development environment
2. **Smart Seeding**: Only seeds if enhanced data doesn't already exist
3. **Non-Blocking**: Seeding failures don't prevent API startup
4. **Comprehensive**: Tests all investor demo features

### Manual Usage

### Option 1: Docker Compose (Recommended)

```bash
# Start services (automatic seeding in development)
docker compose up -d

# Check logs to see seeding progress
docker compose logs api | grep -i seed
```

### Option 2: Standalone Database Initialization

```bash
# Initialize basic schema and data only
python3 scripts/init_database.py
```

### Option 3: Manual Comprehensive Seeding

```bash
# Run comprehensive seeding manually
docker compose exec api python /scripts/purge_and_seed.py
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

### Basic Seed Data (init_database.sql)
- 2 Organizations (Acme Corp, Demo Organization)
- 3 Users with credentials:
  - `admin@acmecorp.com` / `admin123` (Admin role, Enterprise plan)
  - `user@acmecorp.com` / `user123` (User role, Pro plan)
  - `demo@example.com` / `demo123` (User role, Pro plan)
- 4 Repositories (backend-api, frontend-web, mobile-app, infrastructure)
- 30 Basic Jira tickets across different categories (AUTH, DB, UI, API, MOB, INFRA)
- 20+ commits with ticket references

### Enhanced Development Data (Automatic in Development)
- **50+ Comprehensive Tickets** for testing all investor demo features:
  - **PRED-xxx**: Predictive Analytics & ML tickets with historical data
  - **TAG-xxx**: Auto-Tagging & Classification tickets with diverse content
  - **INTENT-xxx**: Intent Analysis tickets with complex decisions
  - **GAP-xxx**: Gap Detection tickets for orphaned content testing
  - **IMPACT-xxx**: Impact Analysis tickets for dependency testing
  - **SEARCH-xxx**: Streaming Search tickets with rich content
  - **AI-xxx**: AI Enhancement tickets with varied scenarios
- **Realistic Commits** with proper relationships and orphaned examples
- **Complex Decisions** with stakeholder conflicts and alternatives
- **Code Files** for impact analysis testing
- **Orphaned Data** specifically for gap detection features

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

## Features Tested by Enhanced Data

The comprehensive development data is specifically designed to test all investor demo features:

### 🔮 Predictive Analytics
- Historical velocity data for ML model training
- Tickets with complexity factors and completion patterns
- Realistic story point distributions and team assignments

### 🏷️ Auto-Tagging & Classification
- Diverse ticket content across multiple categories
- Varied description styles and technical terminology
- Mixed issue types (bugs, features, tasks, epics)

### 🤔 Intent Analysis & Decision Extraction
- Complex decisions with multiple alternatives
- Stakeholder conflicts and resolution patterns
- Structured decision documentation with rationale

### 📊 Gap Detection
- Orphaned commits without ticket references
- Undocumented features and hotfixes
- Stale tickets and missing relationships

### 🔗 Impact Analysis
- Interconnected code changes and dependencies
- File modification patterns and hotspots
- Cross-system impact scenarios

### 🔍 Streaming Search
- Rich content for semantic search testing
- Varied document types and structures
- Comprehensive indexing scenarios

### 🤖 AI Enhancement
- Diverse query patterns and contexts
- Multi-model testing scenarios
- Complex prompt engineering cases

## Notes

- **Automatic Seeding**: Only runs in development environment (`ENVIRONMENT=development`)
- **Smart Detection**: Checks for existing enhanced data to avoid duplicates
- **Non-Destructive**: Doesn't interfere with basic seed data from init_database.sql
- **Performance Optimized**: Seeding completes in <30 seconds
- **Comprehensive Coverage**: Tests all investor demo features
- Password hashes use bcrypt with the demo passwords shown above
- Organization IDs and repository IDs are fixed UUIDs for consistency
- All timestamps use PostgreSQL's CURRENT_TIMESTAMP
- The script creates comprehensive indexes for optimal performance
