#!/usr/bin/env python3
"""
Purge all data and seed with realistic dummy data
This script will:
1. Drop all data from PostgreSQL tables
2. Drop all collections from Qdrant
3. Create realistic dummy data for testing
"""

import asyncio
import asyncpg
from qdrant_client import QdrantClient
from datetime import datetime, timedelta
import random
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "database": "confluence_rag"
}

# Qdrant connection
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# Dummy data templates
REALISTIC_TICKETS = [
    {
        "key": "AUTH-101",
        "summary": "Implement OAuth2 authentication for API",
        "description": "We need to add OAuth2 authentication to secure our REST API. This will replace the current basic auth mechanism.\n\nAcceptance Criteria:\n- Support OAuth2 authorization code flow\n- Implement token refresh mechanism\n- Add role-based access control (RBAC)\n- Update API documentation\n\nRelated: See confluence page on authentication strategy",
        "issue_type": "Story",
        "status": "Done",
        "priority": "High",
        "assignee": "Sarah Johnson",
        "reporter": "Mike Chen",
        "labels": ["security", "api", "authentication"],
        "components": ["Backend", "API"]
    },
    {
        "key": "AUTH-102",
        "summary": "Add JWT token validation middleware",
        "description": "Create middleware to validate JWT tokens on all protected API endpoints.\n\nTechnical Details:\n- Validate token signature\n- Check expiration\n- Extract user claims\n- Handle token refresh\n\nCommit: abc123def456",
        "issue_type": "Task",
        "status": "Done",
        "priority": "High",
        "assignee": "Sarah Johnson",
        "reporter": "Sarah Johnson",
        "labels": ["security", "backend"],
        "components": ["Backend"]
    },
    {
        "key": "DB-201",
        "summary": "Migrate from MongoDB to PostgreSQL",
        "description": "Migrate our user data from MongoDB to PostgreSQL for better relational data support and ACID compliance.\n\nPhases:\n1. Schema design in PostgreSQL\n2. Create migration scripts\n3. Test data integrity\n4. Cutover plan\n5. Rollback strategy\n\nImpact: This will affect AUTH-101 and USER-301",
        "issue_type": "Epic",
        "status": "In Progress",
        "priority": "Critical",
        "assignee": "David Park",
        "reporter": "Mike Chen",
        "labels": ["database", "migration", "infrastructure"],
        "components": ["Database", "Backend"]
    },
    {
        "key": "DB-202",
        "summary": "Optimize database queries for user profile page",
        "description": "User profile page is taking 3+ seconds to load. Need to optimize queries.\n\nInvestigation findings:\n- Missing index on user_id in sessions table\n- N+1 query problem in user_preferences\n- Redundant JOIN on inactive_users table\n\nPR #45 has the fixes",
        "issue_type": "Bug",
        "status": "Done",
        "priority": "High",
        "assignee": "David Park",
        "reporter": "Sarah Johnson",
        "labels": ["performance", "database"],
        "components": ["Database", "Backend"]
    },
    {
        "key": "UI-301",
        "summary": "Redesign dashboard with new component library",
        "description": "Replace legacy dashboard components with Material-UI v5.\n\nScope:\n- Update all chart components\n- Implement responsive grid layout\n- Add dark mode support\n- Improve accessibility (WCAG 2.1 AA)\n\nDesign: See Figma mockups in Confluence",
        "issue_type": "Story",
        "status": "In Progress",
        "priority": "Medium",
        "assignee": "Emma Wilson",
        "reporter": "Mike Chen",
        "labels": ["frontend", "ui", "dashboard"],
        "components": ["Frontend"]
    },
    {
        "key": "UI-302",
        "summary": "Fix broken table sorting on mobile devices",
        "description": "Table sorting doesn't work on mobile screens < 768px.\n\nSteps to reproduce:\n1. Open dashboard on mobile\n2. Try to sort any table column\n3. Nothing happens\n\nExpected: Table should sort\nActual: Click doesn't register\n\nCommit: 789xyz",
        "issue_type": "Bug",
        "status": "Done",
        "priority": "Medium",
        "assignee": "Emma Wilson",
        "reporter": "Sarah Johnson",
        "labels": ["frontend", "mobile", "bug"],
        "components": ["Frontend"]
    },
    {
        "key": "API-401",
        "summary": "Add rate limiting to public API endpoints",
        "description": "Implement rate limiting to prevent API abuse.\n\nRequirements:\n- 100 requests per minute for authenticated users\n- 10 requests per minute for anonymous users\n- Return proper HTTP 429 status\n- Add X-RateLimit headers\n\nSee: Related to AUTH-101",
        "issue_type": "Task",
        "status": "To Do",
        "priority": "High",
        "assignee": "Sarah Johnson",
        "reporter": "Mike Chen",
        "labels": ["api", "security", "infrastructure"],
        "components": ["Backend", "API"]
    },
    {
        "key": "API-402",
        "summary": "GraphQL API endpoint for complex queries",
        "description": "Add GraphQL endpoint alongside REST API for complex data fetching needs.\n\nBenefits:\n- Reduce over-fetching\n- Better mobile performance\n- Type safety with schema\n\nPR #52 has initial implementation",
        "issue_type": "Story",
        "status": "In Review",
        "priority": "Medium",
        "assignee": "David Park",
        "reporter": "Emma Wilson",
        "labels": ["api", "graphql", "enhancement"],
        "components": ["Backend", "API"]
    },
    {
        "key": "INFRA-501",
        "summary": "Setup Kubernetes cluster for production",
        "description": "Migrate from EC2 instances to Kubernetes for better scalability and resource management.\n\nTasks:\n- Setup EKS cluster\n- Configure Helm charts\n- Setup CI/CD pipeline\n- Configure monitoring (Prometheus + Grafana)\n- Setup log aggregation (ELK stack)\n\nBlocked by: DB-201",
        "issue_type": "Epic",
        "status": "To Do",
        "priority": "High",
        "assignee": "Mike Chen",
        "reporter": "Mike Chen",
        "labels": ["infrastructure", "devops", "kubernetes"],
        "components": ["Infrastructure"]
    },
    {
        "key": "INFRA-502",
        "summary": "Configure Redis for session management",
        "description": "Replace in-memory sessions with Redis for horizontal scaling.\n\nConfiguration:\n- Redis Cluster with 3 nodes\n- Persistence enabled (AOF + RDB)\n- TTL of 24 hours for sessions\n\nCommits: Multiple commits in PR #48",
        "issue_type": "Task",
        "status": "Done",
        "priority": "High",
        "assignee": "Mike Chen",
        "reporter": "Sarah Johnson",
        "labels": ["infrastructure", "redis", "scalability"],
        "components": ["Infrastructure", "Backend"]
    }
]

REALISTIC_COMMITS = [
    {
        "sha": "abc123def456",
        "message": "feat(auth): implement JWT token validation middleware\n\nAdded middleware to validate JWT tokens:\n- Verify token signature using RS256\n- Check expiration timestamp\n- Extract user claims (id, email, role)\n- Handle token refresh logic\n\nCloses AUTH-102",
        "author_name": "Sarah Johnson",
        "author_email": "sarah.johnson@acmecorp.com",
        "files_changed": ["src/middleware/auth.ts", "src/utils/jwt.ts", "tests/auth.test.ts"]
    },
    {
        "sha": "def456ghi789",
        "message": "refactor(db): add database indexes for performance\n\nAdded indexes:\n- user_id on sessions table\n- email on users table (unique)\n- created_at on audit_logs table\n\nQuery performance improved by 80%\n\nResolves DB-202",
        "author_name": "David Park",
        "author_email": "david.park@acmecorp.com",
        "files_changed": ["migrations/008_add_indexes.sql", "docs/database_schema.md"]
    },
    {
        "sha": "ghi789jkl012",
        "message": "fix(ui): fix table sorting on mobile devices\n\nIssue: Click events weren't registering on mobile\n\nSolution:\n- Increased touch target size to 44x44px\n- Added proper event listeners for touch events\n- Tested on iOS Safari and Chrome Mobile\n\nFixes UI-302",
        "author_name": "Emma Wilson",
        "author_email": "emma.wilson@acmecorp.com",
        "files_changed": ["src/components/Table/SortableHeader.tsx", "src/components/Table/Table.css"]
    },
    {
        "sha": "jkl012mno345",
        "message": "feat(api): add OAuth2 authorization endpoints\n\nImplemented OAuth2 endpoints:\n- POST /oauth/authorize\n- POST /oauth/token\n- POST /oauth/refresh\n- GET /oauth/userinfo\n\nSupports authorization code flow\n\nPart of AUTH-101",
        "author_name": "Sarah Johnson",
        "author_email": "sarah.johnson@acmecorp.com",
        "files_changed": ["src/routes/oauth.ts", "src/controllers/oauth_controller.ts", "src/services/oauth_service.ts"]
    },
    {
        "sha": "mno345pqr678",
        "message": "chore(infra): configure Redis for session storage\n\nReplaced in-memory sessions with Redis:\n- Setup Redis cluster connection\n- Configure session serialization\n- Add TTL for automatic cleanup\n- Update environment variables\n\nResolves INFRA-502",
        "author_name": "Mike Chen",
        "author_email": "mike.chen@acmecorp.com",
        "files_changed": ["src/config/redis.ts", "src/middleware/session.ts", "docker-compose.yml"]
    },
    {
        "sha": "pqr678stu901",
        "message": "docs: update API authentication documentation\n\nUpdated docs to reflect OAuth2 implementation:\n- Added authentication flow diagram\n- Updated endpoint descriptions\n- Added example requests/responses\n- Added troubleshooting section\n\nRelated to AUTH-101",
        "author_name": "Emma Wilson",
        "author_email": "emma.wilson@acmecorp.com",
        "files_changed": ["docs/api/authentication.md", "docs/diagrams/oauth_flow.png"]
    },
    {
        "sha": "stu901vwx234",
        "message": "test: add integration tests for OAuth flow\n\nAdded comprehensive test coverage:\n- Authorization code flow\n- Token refresh flow\n- Error scenarios (invalid token, expired, etc.)\n- RBAC permission checks\n\nTest coverage: 95%\n\nAUTH-101",
        "author_name": "Sarah Johnson",
        "author_email": "sarah.johnson@acmecorp.com",
        "files_changed": ["tests/integration/oauth.test.ts", "tests/fixtures/oauth_tokens.ts"]
    }
]

REALISTIC_PRS = [
    {
        "pr_number": 45,
        "title": "Optimize database queries for user profile",
        "description": "## Problem\nUser profile page loading was taking 3+ seconds due to inefficient queries.\n\n## Solution\n- Added index on `user_id` in sessions table\n- Fixed N+1 query in user_preferences loading\n- Removed redundant JOIN on inactive_users\n\n## Performance Impact\n- Page load time: 3.2s → 0.4s (87.5% improvement)\n- Database query count: 47 → 5 queries\n\n## Testing\n- [x] Unit tests pass\n- [x] Integration tests pass\n- [x] Tested with 10k+ user accounts\n- [x] Verified indexes in production DB\n\nCloses DB-202",
        "author_name": "David Park",
        "state": "merged",
        "commit_shas": ["def456ghi789"]
    },
    {
        "pr_number": 48,
        "title": "Configure Redis for session management",
        "description": "## Overview\nReplaces in-memory session storage with Redis to enable horizontal scaling.\n\n## Changes\n- Setup Redis cluster connection with 3 nodes\n- Configure session serialization/deserialization\n- Add TTL (24 hours) for automatic cleanup\n- Update environment configuration\n\n## Migration Plan\n1. Deploy Redis cluster\n2. Run in dual-write mode for 1 week\n3. Cutover to Redis-only\n4. Remove old session code\n\n## Rollback Plan\nEnvironment variable `USE_REDIS_SESSIONS=false` reverts to in-memory\n\nCloses INFRA-502",
        "author_name": "Mike Chen",
        "state": "merged",
        "commit_shas": ["mno345pqr678"]
    },
    {
        "pr_number": 52,
        "title": "Add GraphQL API endpoint",
        "description": "## Summary\nAdds GraphQL endpoint at `/graphql` alongside existing REST API.\n\n## Features\n- Type-safe schema with TypeScript\n- Resolvers for User, Post, Comment entities\n- DataLoader for N+1 prevention\n- Query complexity limiting\n- GraphQL Playground in dev mode\n\n## Benefits\n- Reduces over-fetching (mobile bandwidth savings)\n- Single request for complex data needs\n- Better developer experience with typed schemas\n\n## Next Steps\n- Add mutations (this PR is query-only)\n- Add subscriptions for real-time updates\n- Migrate mobile app to use GraphQL\n\nRelated to API-402",
        "author_name": "David Park",
        "state": "open",
        "commit_shas": []
    }
]

REALISTIC_DOCS = [
    {
        "title": "Authentication Strategy Overview",
        "content": """# Authentication Strategy

## Current State
We are migrating from Basic Auth to OAuth2 for improved security and third-party integration support.

## OAuth2 Implementation
- **Grant Type**: Authorization Code Flow
- **Token Type**: JWT (RS256 signed)
- **Token Lifetime**: 1 hour (access), 30 days (refresh)
- **Scopes**: read, write, admin

## RBAC Design
Roles:
- **Admin**: Full system access
- **User**: Read/write own data
- **Guest**: Read-only access

See implementation in AUTH-101 and AUTH-102.

## Related Resources
- API Documentation: /docs/api/authentication
- Security Audit Report: Q4-2024-Security-Audit.pdf
""",
        "space_key": "ENG",
        "page_id": "auth-strategy-001"
    },
    {
        "title": "Database Migration Guide",
        "content": """# MongoDB to PostgreSQL Migration

## Why PostgreSQL?
- ACID compliance for financial transactions
- Better support for complex joins
- Superior JSON query capabilities (JSONB)
- Active community and tooling

## Migration Plan
### Phase 1: Schema Design (Week 1-2)
- Map MongoDB collections to PostgreSQL tables
- Define foreign keys and constraints
- Design indexes for performance

### Phase 2: Dual-Write (Week 3-4)
- Write to both MongoDB and PostgreSQL
- Compare data integrity
- Monitor performance

### Phase 3: Cutover (Week 5)
- Switch reads to PostgreSQL
- Decommission MongoDB
- Archive old data

## Data Mapping
| MongoDB Collection | PostgreSQL Table |
|--------------------|------------------|
| users              | users            |
| sessions           | user_sessions    |
| audit_logs         | audit_logs       |

Related tickets: DB-201, DB-202
""",
        "space_key": "ENG",
        "page_id": "db-migration-001"
    },
    {
        "title": "Frontend Architecture",
        "content": """# Frontend Architecture

## Tech Stack
- **Framework**: React 18 with TypeScript
- **State Management**: Redux Toolkit
- **UI Library**: Material-UI v5
- **Build Tool**: Vite
- **Testing**: Jest + React Testing Library

## Component Structure
```
src/
├── components/     # Reusable UI components
├── pages/          # Page-level components
├── hooks/          # Custom React hooks
├── services/       # API clients
├── store/          # Redux store and slices
└── utils/          # Helper functions
```

## Design System
We follow Material-UI's design principles with custom theme:
- Primary Color: #1976d2
- Secondary Color: #dc004e
- Font: Inter

## Performance Goals
- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Lighthouse Score: > 90

Related: UI-301, UI-302
""",
        "space_key": "ENG",
        "page_id": "frontend-arch-001"
    },
    {
        "title": "API Rate Limiting Policy",
        "content": """# API Rate Limiting

## Rate Limits
- **Authenticated Users**: 100 requests/minute
- **Anonymous Users**: 10 requests/minute
- **Admin Users**: 1000 requests/minute

## Response Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

## HTTP Status Codes
- **429 Too Many Requests**: Rate limit exceeded
- **Retry-After** header indicates wait time in seconds

## Exemptions
- Health check endpoints
- Webhook callbacks
- Internal service-to-service calls

Implementation ticket: API-401
""",
        "space_key": "ENG",
        "page_id": "api-rate-limit-001"
    }
]

REALISTIC_CODE_FILES = [
    {
        "file_path": "src/middleware/auth.ts",
        "content": """import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { User } from '../models/User';

interface JWTPayload {
  userId: string;
  email: string;
  role: string;
}

export const authenticateToken = async (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload;
    const user = await User.findById(decoded.userId);

    if (!user) {
      return res.status(403).json({ error: 'Invalid token' });
    }

    req.user = user;
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Invalid or expired token' });
  }
};

export const requireRole = (role: string) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user || req.user.role !== role) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
};
""",
        "language": "typescript",
        "functions": ["authenticateToken", "requireRole"],
        "classes": []
    },
    {
        "file_path": "src/config/redis.ts",
        "content": """import Redis from 'ioredis';

const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  db: 0,
  retryStrategy: (times: number) => {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
};

// Create Redis cluster client
const redisCluster = new Redis.Cluster([
  { host: 'redis-1', port: 6379 },
  { host: 'redis-2', port: 6379 },
  { host: 'redis-3', port: 6379 },
], {
  redisOptions: redisConfig,
});

redisCluster.on('connect', () => {
  console.log('✅ Redis cluster connected');
});

redisCluster.on('error', (err) => {
  console.error('❌ Redis cluster error:', err);
});

export default redisCluster;
""",
        "language": "typescript",
        "functions": [],
        "classes": []
    },
    {
        "file_path": "src/components/Table/SortableHeader.tsx",
        "content": """import React from 'react';
import { TableCell, TableSortLabel } from '@mui/material';

interface SortableHeaderProps {
  column: string;
  label: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  onSort: (column: string) => void;
}

export const SortableHeader: React.FC<SortableHeaderProps> = ({
  column,
  label,
  sortBy,
  sortOrder,
  onSort,
}) => {
  const handleSort = () => {
    onSort(column);
  };

  return (
    <TableCell
      sx={{
        // Increase touch target size for mobile
        minWidth: '44px',
        minHeight: '44px',
        cursor: 'pointer',
      }}
      onClick={handleSort}
      onTouchEnd={(e) => {
        e.preventDefault();
        handleSort();
      }}
    >
      <TableSortLabel
        active={sortBy === column}
        direction={sortBy === column ? sortOrder : 'asc'}
      >
        {label}
      </TableSortLabel>
    </TableCell>
  );
};
""",
        "language": "typescript",
        "functions": ["SortableHeader", "handleSort"],
        "classes": []
    }
]


async def purge_postgresql():
    """Drop all data from PostgreSQL tables"""
    print("\n🗑️  Purging PostgreSQL data...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Truncate all tables (faster than DELETE)
        tables = [
            "decisions",
            "relationships",
            "pull_requests",
            "commits",
            "code_files",
            "jira_tickets",
            "repositories",
            "documents",
            "chunks",
            "sessions",
            "api_keys"
        ]

        for table in tables:
            try:
                await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
                print(f"  ✅ Truncated {table}")
            except Exception as e:
                print(f"  ⚠️  Could not truncate {table}: {e}")

        print("✅ PostgreSQL purged successfully")
    finally:
        await conn.close()


def purge_qdrant():
    """Drop all collections from Qdrant"""
    print("\n🗑️  Purging Qdrant collections...")

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    try:
        collections = client.get_collections().collections

        for collection in collections:
            client.delete_collection(collection.name)
            print(f"  ✅ Deleted collection: {collection.name}")

        print("✅ Qdrant purged successfully")
    except Exception as e:
        print(f"⚠️  Qdrant purge error: {e}")


async def seed_organization():
    """Create dummy organization and return its ID"""
    print("\n🌱 Seeding organization...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        org_id = await conn.fetchval("""
            INSERT INTO organizations (name, created_at)
            VALUES ($1, $2)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
        """, "Acme Corp", datetime.now())

        print(f"  ✅ Created organization: Acme Corp ({org_id})")
        return str(org_id)
    finally:
        await conn.close()


async def seed_jira_tickets(org_id: str):
    """Seed realistic Jira tickets"""
    print("\n🎫 Seeding Jira tickets...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        for idx, ticket in enumerate(REALISTIC_TICKETS):
            # Calculate realistic dates
            days_ago = (len(REALISTIC_TICKETS) - idx) * 5
            created = datetime.now() - timedelta(days=days_ago)
            updated = created + timedelta(days=random.randint(1, days_ago))
            resolved = updated if ticket["status"] == "Done" else None

            # Build URL
            url = f"https://acmecorp.atlassian.net/browse/{ticket['key']}"

            await conn.execute("""
                INSERT INTO jira_tickets (
                    organization_id, ticket_key, summary, description,
                    issue_type, status, priority, assignee, reporter,
                    created, updated, resolved, labels, components,
                    url, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
                org_id, ticket["key"], ticket["summary"], ticket["description"],
                ticket["issue_type"], ticket["status"], ticket["priority"],
                ticket["assignee"], ticket["reporter"],
                created, updated, resolved,
                ticket["labels"], ticket["components"],
                url, {}
            )

            print(f"  ✅ {ticket['key']}: {ticket['summary']}")

        count = await conn.fetchval("SELECT COUNT(*) FROM jira_tickets WHERE organization_id = $1", org_id)
        print(f"✅ Seeded {count} Jira tickets")
    finally:
        await conn.close()


async def seed_repository(org_id: str):
    """Seed dummy repository"""
    print("\n💻 Seeding repository...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        repo_id = await conn.fetchval("""
            INSERT INTO repositories (
                organization_id, repo_name, repo_url, provider, branch,
                file_count, last_synced, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """,
            org_id, "acme-backend", "https://github.com/acmecorp/backend",
            "github", "main", len(REALISTIC_CODE_FILES), datetime.now(), datetime.now()
        )

        print(f"  ✅ Created repository: acme-backend")
        return str(repo_id)
    finally:
        await conn.close()


async def seed_commits(org_id: str, repo_id: str):
    """Seed realistic commits"""
    print("\n📝 Seeding commits...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        for idx, commit in enumerate(REALISTIC_COMMITS):
            days_ago = (len(REALISTIC_COMMITS) - idx) * 2
            commit_date = datetime.now() - timedelta(days=days_ago)

            url = f"https://github.com/acmecorp/backend/commit/{commit['sha']}"

            await conn.execute("""
                INSERT INTO commits (
                    organization_id, repository_id, sha, message,
                    author_name, author_email, commit_date,
                    files_changed, url, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                org_id, repo_id, commit["sha"], commit["message"],
                commit["author_name"], commit["author_email"], commit_date,
                commit["files_changed"], url, {}
            )

            print(f"  ✅ {commit['sha'][:7]}: {commit['message'].split(chr(10))[0][:50]}...")

        count = await conn.fetchval("SELECT COUNT(*) FROM commits WHERE organization_id = $1", org_id)
        print(f"✅ Seeded {count} commits")
    finally:
        await conn.close()


async def seed_pull_requests(org_id: str, repo_id: str):
    """Seed realistic PRs"""
    print("\n🔀 Seeding pull requests...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        for idx, pr in enumerate(REALISTIC_PRS):
            days_ago = (len(REALISTIC_PRS) - idx) * 3
            created_at = datetime.now() - timedelta(days=days_ago)
            merged_at = created_at + timedelta(days=2) if pr["state"] == "merged" else None

            url = f"https://github.com/acmecorp/backend/pull/{pr['pr_number']}"

            await conn.execute("""
                INSERT INTO pull_requests (
                    organization_id, repository_id, pr_number, title, description,
                    author_name, state, created_at, merged_at, commit_shas, url, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
                org_id, repo_id, pr["pr_number"], pr["title"], pr["description"],
                pr["author_name"], pr["state"], created_at, merged_at,
                pr["commit_shas"], url, {}
            )

            print(f"  ✅ PR #{pr['pr_number']}: {pr['title']}")

        count = await conn.fetchval("SELECT COUNT(*) FROM pull_requests WHERE organization_id = $1", org_id)
        print(f"✅ Seeded {count} pull requests")
    finally:
        await conn.close()


async def seed_code_files(org_id: str, repo_id: str):
    """Seed realistic code files"""
    print("\n📂 Seeding code files...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        for file in REALISTIC_CODE_FILES:
            url = f"https://github.com/acmecorp/backend/blob/main/{file['file_path']}"

            await conn.execute("""
                INSERT INTO code_files (
                    organization_id, repository_id, file_path, file_name,
                    file_type, language, content, functions, classes,
                    line_count, url, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """,
                org_id, repo_id, file["file_path"], file["file_path"].split("/")[-1],
                file["file_path"].split(".")[-1], file["language"], file["content"],
                file["functions"], file["classes"],
                len(file["content"].split("\n")), url, {}
            )

            print(f"  ✅ {file['file_path']}")

        count = await conn.fetchval("SELECT COUNT(*) FROM code_files WHERE organization_id = $1", org_id)
        print(f"✅ Seeded {count} code files")
    finally:
        await conn.close()


async def seed_confluence_docs(org_id: str):
    """Seed realistic Confluence documents"""
    print("\n📄 Seeding Confluence documents...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        for idx, doc in enumerate(REALISTIC_DOCS):
            created = datetime.now() - timedelta(days=(len(REALISTIC_DOCS) - idx) * 7)
            url = f"https://acmecorp.atlassian.net/wiki/spaces/{doc['space_key']}/pages/{doc['page_id']}"

            await conn.execute("""
                INSERT INTO documents (
                    organization_id, title, content, source_type,
                    space_key, page_id, url, created_at, updated_at, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                org_id, doc["title"], doc["content"], "confluence",
                doc["space_key"], doc["page_id"], url, created, created, {}
            )

            print(f"  ✅ {doc['title']}")

        count = await conn.fetchval("SELECT COUNT(*) FROM documents WHERE organization_id = $1", org_id)
        print(f"✅ Seeded {count} Confluence documents")
    finally:
        await conn.close()


async def main():
    """Main execution"""
    print("=" * 60)
    print("🧹 PURGE AND SEED DATABASE")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete ALL data!")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    input()

    # Purge
    await purge_postgresql()
    purge_qdrant()

    # Seed
    org_id = await seed_organization()
    await seed_jira_tickets(org_id)

    repo_id = await seed_repository(org_id)
    await seed_commits(org_id, repo_id)
    await seed_pull_requests(org_id, repo_id)
    await seed_code_files(org_id, repo_id)

    await seed_confluence_docs(org_id)

    print("\n" + "=" * 60)
    print("✅ PURGE AND SEED COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Organization ID: {org_id}")
    print(f"📊 Repository ID: {repo_id}")
    print("\n🎯 Next Steps:")
    print("1. Login to UI with: admin@acmecorp.com / password")
    print("2. Test Decision Analysis with ticket: AUTH-101")
    print("3. Test Knowledge Graph relationships")
    print("4. Ask questions like: 'How does OAuth authentication work?'")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
