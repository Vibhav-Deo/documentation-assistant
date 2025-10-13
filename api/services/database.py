import os
import asyncpg
import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from models import User, Organization, UserRole, PlanType
import json
import uuid

class DatabaseService:
    def __init__(self):
        self.pool = None
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/confluence_rag")
    
    async def init_pool(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(self.db_url, min_size=5, max_size=20)
        await self.create_tables()
    
    async def create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                
                CREATE TABLE IF NOT EXISTS organizations (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(255) NOT NULL,
                    plan VARCHAR(50) DEFAULT 'free',
                    monthly_quota INTEGER DEFAULT 100,
                    used_quota INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    organization_id UUID REFERENCES organizations(id),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id),
                    session_data JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id),
                    organization_id UUID REFERENCES organizations(id),
                    action VARCHAR(255) NOT NULL,
                    resource VARCHAR(255),
                    details JSONB,
                    ip_address INET,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_org ON audit_logs(organization_id);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

                -- Jira tickets table
                CREATE TABLE IF NOT EXISTS jira_tickets (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                    ticket_key VARCHAR(50) NOT NULL,
                    summary TEXT NOT NULL,
                    description TEXT,
                    issue_type VARCHAR(50),
                    status VARCHAR(50),
                    priority VARCHAR(50),
                    assignee VARCHAR(255),
                    reporter VARCHAR(255),
                    created_date TIMESTAMP,
                    updated_date TIMESTAMP,
                    resolved_date TIMESTAMP,
                    story_points INTEGER,
                    labels TEXT[],
                    components TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(organization_id, ticket_key)
                );

                CREATE INDEX IF NOT EXISTS idx_jira_tickets_org ON jira_tickets(organization_id);
                CREATE INDEX IF NOT EXISTS idx_jira_tickets_key ON jira_tickets(ticket_key);
                CREATE INDEX IF NOT EXISTS idx_jira_tickets_status ON jira_tickets(status);
                CREATE INDEX IF NOT EXISTS idx_jira_tickets_search ON jira_tickets USING gin(to_tsvector('english', summary || ' ' || COALESCE(description, '')));

                -- Repositories table
                CREATE TABLE IF NOT EXISTS repositories (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                    repo_url TEXT NOT NULL,
                    repo_name VARCHAR(255) NOT NULL,
                    provider VARCHAR(50),
                    branch VARCHAR(100) DEFAULT 'main',
                    last_synced TIMESTAMP,
                    file_count INTEGER DEFAULT 0,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(organization_id, repo_url)
                );

                -- Code files table
                CREATE TABLE IF NOT EXISTS code_files (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
                    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                    file_path TEXT NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50),
                    language VARCHAR(50),
                    content TEXT,
                    functions TEXT[],
                    classes TEXT[],
                    imports TEXT[],
                    line_count INTEGER,
                    last_modified TIMESTAMP,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(repository_id, file_path)
                );

                CREATE INDEX IF NOT EXISTS idx_repositories_org ON repositories(organization_id);
                CREATE INDEX IF NOT EXISTS idx_code_files_repo ON code_files(repository_id);
                CREATE INDEX IF NOT EXISTS idx_code_files_org ON code_files(organization_id);
                CREATE INDEX IF NOT EXISTS idx_code_files_type ON code_files(file_type);
                CREATE INDEX IF NOT EXISTS idx_code_files_lang ON code_files(language);
                CREATE INDEX IF NOT EXISTS idx_code_files_search ON code_files USING gin(to_tsvector('english', file_name || ' ' || COALESCE(content, '')));

                -- Commits table
                CREATE TABLE IF NOT EXISTS commits (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
                    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                    sha VARCHAR(40) NOT NULL,
                    message TEXT,
                    author_name VARCHAR(255),
                    author_email VARCHAR(255),
                    commit_date TIMESTAMP,
                    files_changed TEXT[],
                    additions INTEGER DEFAULT 0,
                    deletions INTEGER DEFAULT 0,
                    ticket_references TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(repository_id, sha)
                );

                -- Pull requests table
                CREATE TABLE IF NOT EXISTS pull_requests (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
                    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                    pr_number INTEGER NOT NULL,
                    title TEXT,
                    description TEXT,
                    author_name VARCHAR(255),
                    state VARCHAR(50),
                    created_at_pr TIMESTAMP,
                    merged_at TIMESTAMP,
                    closed_at TIMESTAMP,
                    commit_shas TEXT[],
                    ticket_references TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(repository_id, pr_number)
                );

                CREATE INDEX IF NOT EXISTS idx_commits_repo ON commits(repository_id);
                CREATE INDEX IF NOT EXISTS idx_commits_org ON commits(organization_id);
                CREATE INDEX IF NOT EXISTS idx_commits_sha ON commits(sha);
                CREATE INDEX IF NOT EXISTS idx_commits_author ON commits(author_email);
                CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(commit_date);
                CREATE INDEX IF NOT EXISTS idx_commits_tickets ON commits USING gin(ticket_references);
                CREATE INDEX IF NOT EXISTS idx_commits_search ON commits USING gin(to_tsvector('english', message));

                CREATE INDEX IF NOT EXISTS idx_prs_repo ON pull_requests(repository_id);
                CREATE INDEX IF NOT EXISTS idx_prs_org ON pull_requests(organization_id);
                CREATE INDEX IF NOT EXISTS idx_prs_number ON pull_requests(pr_number);
                CREATE INDEX IF NOT EXISTS idx_prs_tickets ON pull_requests USING gin(ticket_references);
                CREATE INDEX IF NOT EXISTS idx_prs_search ON pull_requests USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
            """)
    
    async def create_organization(self, name: str, plan: str = "free") -> Dict:
        """Create new organization"""
        quota_map = {"free": 100, "pro": 10000, "enterprise": -1}
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO organizations (name, plan, monthly_quota)
                VALUES ($1, $2, $3)
                RETURNING id, name, plan, monthly_quota, used_quota, is_active, created_at
            """, name, plan, quota_map.get(plan, 100))
            
            return dict(row)
    
    async def create_user(self, email: str, password_hash: str, name: str, organization_id: str, role: str = "user") -> Dict:
        """Create new user"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO users (email, password_hash, name, organization_id, role)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, email, name, role, organization_id, is_active, created_at
            """, email, password_hash, name, organization_id, role)
            
            return dict(row)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, name, password_hash, role, organization_id, is_active, created_at
                FROM users WHERE email = $1 AND is_active = true
            """, email)
            
            return dict(row) if row else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, email, name, role, organization_id, is_active, created_at
                FROM users WHERE id = $1 AND is_active = true
            """, user_id)
            
            return dict(row) if row else None
    
    async def get_organization(self, org_id: str) -> Optional[Dict]:
        """Get organization by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name, plan, monthly_quota, used_quota, is_active, created_at
                FROM organizations WHERE id = $1 AND is_active = true
            """, org_id)
            
            return dict(row) if row else None
    
    async def check_and_increment_quota(self, org_id: str) -> bool:
        """Check quota and increment if available"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                org = await conn.fetchrow("""
                    SELECT plan, monthly_quota, used_quota
                    FROM organizations WHERE id = $1 AND is_active = true
                """, org_id)
                
                if not org:
                    return False
                
                if org['plan'] == 'enterprise':
                    await conn.execute("""
                        UPDATE organizations SET used_quota = used_quota + 1
                        WHERE id = $1
                    """, org_id)
                    return True
                
                if org['used_quota'] >= org['monthly_quota']:
                    return False
                
                await conn.execute("""
                    UPDATE organizations SET used_quota = used_quota + 1
                    WHERE id = $1
                """, org_id)
                return True
    
    async def log_audit(self, user_id: str, org_id: str, action: str, resource: str = None, details: Dict = None, ip: str = None):
        """Log audit event"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_logs (user_id, organization_id, action, resource, details, ip_address)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user_id, org_id, action, resource, json.dumps(details) if details else None, ip)
    
    async def get_organization_users(self, org_id: str) -> List[Dict]:
        """Get all users in organization"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, email, name, role, created_at
                FROM users WHERE organization_id = $1 AND is_active = true
                ORDER BY created_at DESC
            """, org_id)
            
            return [dict(row) for row in rows]
    
    async def get_organization_usage_stats(self, org_id: str) -> Dict:
        """Get organization usage statistics"""
        async with self.pool.acquire() as conn:
            # Get total requests from audit logs
            total_requests = await conn.fetchval("""
                SELECT COUNT(*) FROM audit_logs 
                WHERE organization_id = $1 AND action = 'api_request'
            """, org_id)
            
            # Get requests by user
            user_requests = await conn.fetch("""
                SELECT u.name, u.email, COUNT(a.id) as request_count
                FROM users u
                LEFT JOIN audit_logs a ON u.id = a.user_id AND a.action = 'api_request'
                WHERE u.organization_id = $1 AND u.is_active = true
                GROUP BY u.id, u.name, u.email
                ORDER BY request_count DESC
            """, org_id)
            
            # Get recent activity (last 30 days)
            recent_activity = await conn.fetch("""
                SELECT DATE(created_at) as date, COUNT(*) as requests
                FROM audit_logs
                WHERE organization_id = $1 AND action = 'api_request'
                AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 30
            """, org_id)
            
            return {
                "total_requests": total_requests or 0,
                "user_requests": [dict(row) for row in user_requests],
                "recent_activity": [dict(row) for row in recent_activity]
            }

    # Jira ticket operations
    async def create_jira_ticket(self, ticket_data: Dict, org_id: str) -> Dict:
        """Create or update a Jira ticket"""
        from dateutil import parser as date_parser

        # Parse date strings to datetime objects, removing timezone info
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                dt = date_parser.parse(date_str)
                # Convert to UTC and make timezone-naive for PostgreSQL
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except:
                return None
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO jira_tickets (
                    organization_id, ticket_key, summary, description,
                    issue_type, status, priority, assignee, reporter,
                    created_date, updated_date, resolved_date,
                    story_points, labels, components, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (organization_id, ticket_key)
                DO UPDATE SET
                    summary = EXCLUDED.summary,
                    description = EXCLUDED.description,
                    issue_type = EXCLUDED.issue_type,
                    status = EXCLUDED.status,
                    priority = EXCLUDED.priority,
                    assignee = EXCLUDED.assignee,
                    reporter = EXCLUDED.reporter,
                    updated_date = EXCLUDED.updated_date,
                    resolved_date = EXCLUDED.resolved_date,
                    story_points = EXCLUDED.story_points,
                    labels = EXCLUDED.labels,
                    components = EXCLUDED.components,
                    metadata = EXCLUDED.metadata
                RETURNING id, ticket_key, summary, status
            """,
                org_id,
                ticket_data['key'],
                ticket_data['summary'],
                ticket_data.get('description'),
                ticket_data.get('issue_type'),
                ticket_data.get('status'),
                ticket_data.get('priority'),
                ticket_data.get('assignee'),
                ticket_data.get('reporter'),
                parse_date(ticket_data.get('created')),
                parse_date(ticket_data.get('updated')),
                parse_date(ticket_data.get('resolved')),
                ticket_data.get('story_points'),
                ticket_data.get('labels', []),
                ticket_data.get('components', []),
                json.dumps(ticket_data.get('metadata', {}))
            )
            return dict(row)

    async def get_jira_tickets(self, org_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all Jira tickets for an organization"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, ticket_key, summary, description, issue_type, status,
                       priority, assignee, reporter, created_date, updated_date,
                       resolved_date, story_points, labels, components,
                       created_at
                FROM jira_tickets
                WHERE organization_id = $1
                ORDER BY updated_date DESC NULLS LAST
                LIMIT $2 OFFSET $3
            """, org_id, limit, offset)
            return [dict(row) for row in rows]

    async def count_jira_tickets(self, org_id: str) -> int:
        """Count total Jira tickets for an organization"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM jira_tickets WHERE organization_id = $1
            """, org_id)
            return count or 0

    async def search_jira_tickets(self, query: str, org_id: str, limit: int = 10) -> List[Dict]:
        """Search Jira tickets by text"""
        async with self.pool.acquire() as conn:
            # Extract potential ticket key from query (e.g., "DEMO-002" from "What is DEMO-002 about?")
            import re
            ticket_key_pattern = r'\b([A-Z]{2,10}-\d+)\b'
            ticket_keys = re.findall(ticket_key_pattern, query.upper())
            
            if ticket_keys:
                # If query contains ticket keys, search for them specifically
                rows = await conn.fetch("""
                    SELECT id, ticket_key, summary, description, issue_type, status,
                           priority, assignee, reporter, created_date, updated_date
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND ticket_key = ANY($2::text[])
                    LIMIT $3
                """, org_id, ticket_keys, limit)
            elif len(query.split()) > 3:
                # For multi-word queries, extract keywords
                import string
                keywords = [w.lower().strip(string.punctuation) for w in query.split() 
                           if len(w) > 2 and w.lower() not in ['what', 'show', 'are', 'the', 'is', 'in', 'me', 'about', 'with']]
                
                # Search for each keyword individually
                conditions = []
                params = [org_id]
                param_idx = 2
                
                for kw in keywords:
                    conditions.append(f"(LOWER(summary) LIKE ${param_idx} OR LOWER(description) LIKE ${param_idx} OR LOWER(issue_type) LIKE ${param_idx} OR LOWER(status) LIKE ${param_idx} OR LOWER(priority) LIKE ${param_idx})")
                    params.append(f'%{kw}%')
                    param_idx += 1
                
                if conditions:
                    query_sql = f"""
                        SELECT id, ticket_key, summary, description, issue_type, status,
                               priority, assignee, reporter, created_date, updated_date
                        FROM jira_tickets
                        WHERE organization_id = $1
                        AND ({' OR '.join(conditions)})
                        ORDER BY updated_date DESC NULLS LAST
                        LIMIT ${param_idx}
                    """
                    params.append(limit)
                    rows = await conn.fetch(query_sql, *params)
                else:
                    rows = []
            else:
                # Otherwise do full-text search with field matching
                rows = await conn.fetch("""
                    SELECT id, ticket_key, summary, description, issue_type, status,
                           priority, assignee, reporter, created_date, updated_date
                    FROM jira_tickets
                    WHERE organization_id = $1
                    AND (
                        to_tsvector('english', summary || ' ' || COALESCE(description, ''))
                        @@ plainto_tsquery('english', $2)
                        OR ticket_key ILIKE $3
                        OR summary ILIKE $3
                        OR issue_type ILIKE $3
                        OR status ILIKE $3
                        OR priority ILIKE $3
                    )
                    ORDER BY 
                        CASE WHEN ticket_key ILIKE $3 THEN 1
                             WHEN issue_type ILIKE $3 THEN 2
                             WHEN status ILIKE $3 THEN 3
                             WHEN priority ILIKE $3 THEN 4
                             ELSE 5 END,
                        updated_date DESC NULLS LAST
                    LIMIT $4
                """, org_id, query, f'%{query}%', limit)
            
            return [dict(row) for row in rows]

    async def create_repository(self, repo_data: Dict, org_id: str) -> Dict:
        """Create or update repository"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO repositories (
                    organization_id, repo_url, repo_name, provider, branch,
                    last_synced, file_count, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (organization_id, repo_url)
                DO UPDATE SET
                    repo_name = EXCLUDED.repo_name,
                    branch = EXCLUDED.branch,
                    last_synced = EXCLUDED.last_synced,
                    file_count = EXCLUDED.file_count,
                    metadata = EXCLUDED.metadata
                RETURNING id, organization_id, repo_url, repo_name, provider, branch
            """,
                org_id,
                repo_data.get('repo_url'),
                repo_data.get('repo_name'),
                repo_data.get('provider'),
                repo_data.get('branch', 'main'),
                datetime.now(),
                repo_data.get('file_count', 0),
                json.dumps(repo_data.get('metadata', {}))
            )
            return dict(row)

    async def create_code_file(self, file_data: Dict, repo_id: str, org_id: str) -> Dict:
        """Create or update code file"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO code_files (
                    repository_id, organization_id, file_path, file_name, file_type,
                    language, content, functions, classes, imports, line_count,
                    last_modified, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (repository_id, file_path)
                DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    file_type = EXCLUDED.file_type,
                    language = EXCLUDED.language,
                    content = EXCLUDED.content,
                    functions = EXCLUDED.functions,
                    classes = EXCLUDED.classes,
                    imports = EXCLUDED.imports,
                    line_count = EXCLUDED.line_count,
                    last_modified = EXCLUDED.last_modified,
                    metadata = EXCLUDED.metadata
                RETURNING id, file_path, file_name, language
            """,
                repo_id,
                org_id,
                file_data.get('file_path'),
                file_data.get('file_name'),
                file_data.get('file_type'),
                file_data.get('language'),
                file_data.get('content'),
                file_data.get('functions', []),
                file_data.get('classes', []),
                file_data.get('imports', []),
                file_data.get('line_count', 0),
                file_data.get('last_modified'),
                json.dumps(file_data.get('metadata', {}))
            )
            return dict(row)

    async def get_repositories(self, org_id: str) -> List[Dict]:
        """Get all repositories for organization"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, repo_url, repo_name, provider, branch,
                       last_synced, file_count, created_at
                FROM repositories
                WHERE organization_id = $1
                ORDER BY last_synced DESC NULLS LAST
            """, org_id)
            return [dict(row) for row in rows]

    async def get_code_files(self, repo_id: str, org_id: str, limit: int = 100) -> List[Dict]:
        """Get code files for a repository"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, file_path, file_name, file_type, language,
                       line_count, last_modified, created_at
                FROM code_files
                WHERE repository_id = $1 AND organization_id = $2
                ORDER BY file_path
                LIMIT $3
            """, repo_id, org_id, limit)
            return [dict(row) for row in rows]

    async def search_code_files(self, query: str, org_id: str, limit: int = 10) -> List[Dict]:
        """Search code files by text"""
        async with self.pool.acquire() as conn:
            # Extract potential function/class names (CamelCase or snake_case patterns)
            import re
            code_patterns = re.findall(r'\b([A-Z][a-zA-Z0-9]+|[a-z_][a-z0-9_]+)\b', query)

            if code_patterns:
                # Search for function/class names
                rows = await conn.fetch("""
                    SELECT id, repository_id, file_path, file_name, language, content,
                           functions, classes, line_count
                    FROM code_files
                    WHERE organization_id = $1
                    AND (
                        functions && $2::text[]
                        OR classes && $2::text[]
                        OR file_name ILIKE $3
                    )
                    LIMIT $4
                """, org_id, code_patterns, f'%{query}%', limit)
            else:
                # Full-text search in code content
                rows = await conn.fetch("""
                    SELECT id, repository_id, file_path, file_name, language, content,
                           functions, classes, line_count
                    FROM code_files
                    WHERE organization_id = $1
                    AND (
                        to_tsvector('english', file_name || ' ' || COALESCE(content, ''))
                        @@ plainto_tsquery('english', $2)
                        OR file_name ILIKE $3
                        OR content ILIKE $3
                    )
                    ORDER BY
                        CASE WHEN file_name ILIKE $3 THEN 1 ELSE 2 END,
                        last_modified DESC NULLS LAST
                    LIMIT $4
                """, org_id, query, f'%{query}%', limit)

            return [dict(row) for row in rows]

    async def create_commit(self, commit_data: Dict, repo_id: str, org_id: str) -> Dict:
        """Create or update commit"""
        async with self.pool.acquire() as conn:
            # Extract ticket references from commit message
            import re
            from dateutil import parser as date_parser
            ticket_pattern = r'\b([A-Z]{2,10}-\d+)\b'
            ticket_refs = re.findall(ticket_pattern, commit_data.get('message', ''))

            # Parse commit date if it's a string
            commit_date = commit_data.get('commit_date')
            if isinstance(commit_date, str):
                try:
                    commit_date = date_parser.parse(commit_date)
                    # Remove timezone info to make it naive (PostgreSQL TIMESTAMP requirement)
                    if commit_date.tzinfo is not None:
                        commit_date = commit_date.replace(tzinfo=None)
                except Exception:
                    commit_date = None

            row = await conn.fetchrow("""
                INSERT INTO commits (
                    repository_id, organization_id, sha, message, author_name,
                    author_email, commit_date, files_changed, additions, deletions,
                    ticket_references, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (repository_id, sha)
                DO UPDATE SET
                    message = EXCLUDED.message,
                    author_name = EXCLUDED.author_name,
                    author_email = EXCLUDED.author_email,
                    commit_date = EXCLUDED.commit_date,
                    files_changed = EXCLUDED.files_changed,
                    ticket_references = EXCLUDED.ticket_references
                RETURNING id, sha, author_name, commit_date
            """,
                repo_id,
                org_id,
                commit_data.get('sha'),
                commit_data.get('message'),
                commit_data.get('author_name'),
                commit_data.get('author_email'),
                commit_date,
                commit_data.get('files_changed', []),
                commit_data.get('additions', 0),
                commit_data.get('deletions', 0),
                ticket_refs,
                json.dumps(commit_data.get('metadata', {}))
            )
            return dict(row)

    async def create_pull_request(self, pr_data: Dict, repo_id: str, org_id: str) -> Dict:
        """Create or update pull request"""
        async with self.pool.acquire() as conn:
            # Extract ticket references from PR title and description
            import re
            from dateutil import parser as date_parser
            ticket_pattern = r'\b([A-Z]{2,10}-\d+)\b'
            text = f"{pr_data.get('title', '')} {pr_data.get('description', '')}"
            ticket_refs = re.findall(ticket_pattern, text)

            # Parse PR dates if they're strings
            created_at = pr_data.get('created_at')
            if isinstance(created_at, str):
                try:
                    created_at = date_parser.parse(created_at)
                    # Remove timezone info to make it naive (PostgreSQL TIMESTAMP requirement)
                    if created_at.tzinfo is not None:
                        created_at = created_at.replace(tzinfo=None)
                except Exception:
                    created_at = None

            merged_at = pr_data.get('merged_at')
            if isinstance(merged_at, str):
                try:
                    merged_at = date_parser.parse(merged_at)
                    # Remove timezone info to make it naive
                    if merged_at.tzinfo is not None:
                        merged_at = merged_at.replace(tzinfo=None)
                except Exception:
                    merged_at = None

            closed_at = pr_data.get('closed_at')
            if isinstance(closed_at, str):
                try:
                    closed_at = date_parser.parse(closed_at)
                    # Remove timezone info to make it naive
                    if closed_at.tzinfo is not None:
                        closed_at = closed_at.replace(tzinfo=None)
                except Exception:
                    closed_at = None

            row = await conn.fetchrow("""
                INSERT INTO pull_requests (
                    repository_id, organization_id, pr_number, title, description,
                    author_name, state, created_at_pr, merged_at, closed_at,
                    commit_shas, ticket_references, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (repository_id, pr_number)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    state = EXCLUDED.state,
                    merged_at = EXCLUDED.merged_at,
                    closed_at = EXCLUDED.closed_at,
                    ticket_references = EXCLUDED.ticket_references
                RETURNING id, pr_number, title, state
            """,
                repo_id,
                org_id,
                pr_data.get('pr_number'),
                pr_data.get('title'),
                pr_data.get('description'),
                pr_data.get('author_name'),
                pr_data.get('state'),
                created_at,
                merged_at,
                closed_at,
                pr_data.get('commit_shas', []),
                ticket_refs,
                json.dumps(pr_data.get('metadata', {}))
            )
            return dict(row)

    async def get_commits_for_repository(self, repo_id: str, org_id: str, limit: int = 100) -> List[Dict]:
        """Get commits for a repository"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, sha, message, author_name, author_email, commit_date,
                       files_changed, ticket_references, additions, deletions
                FROM commits
                WHERE repository_id = $1 AND organization_id = $2
                ORDER BY commit_date DESC NULLS LAST
                LIMIT $3
            """, repo_id, org_id, limit)
            return [dict(row) for row in rows]

    async def get_commits_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get all commits that reference a Jira ticket"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT c.id, c.sha, c.message, c.author_name, c.author_email,
                       c.commit_date, c.files_changed, r.repo_name, r.repo_url
                FROM commits c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.organization_id = $1
                AND $2 = ANY(c.ticket_references)
                ORDER BY c.commit_date DESC
            """, org_id, ticket_key)
            return [dict(row) for row in rows]

    async def get_pull_requests_for_repository(self, repo_id: str, org_id: str, limit: int = 50) -> List[Dict]:
        """Get pull requests for a repository"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, pr_number, title, description, author_name, state,
                       created_at_pr, merged_at, closed_at, ticket_references
                FROM pull_requests
                WHERE repository_id = $1 AND organization_id = $2
                ORDER BY created_at_pr DESC NULLS LAST
                LIMIT $3
            """, repo_id, org_id, limit)
            return [dict(row) for row in rows]

    async def get_pull_requests_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get all PRs that reference a Jira ticket"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT pr.id, pr.pr_number, pr.title, pr.description, pr.author_name,
                       pr.state, pr.merged_at, r.repo_name, r.repo_url
                FROM pull_requests pr
                JOIN repositories r ON pr.repository_id = r.id
                WHERE pr.organization_id = $1
                AND $2 = ANY(pr.ticket_references)
                ORDER BY pr.created_at_pr DESC
            """, org_id, ticket_key)
            return [dict(row) for row in rows]

    async def search_commits(self, query: str, org_id: str, limit: int = 10) -> List[Dict]:
        """Search commits by message"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT c.id, c.sha, c.message, c.author_name, c.commit_date,
                       c.ticket_references, r.repo_name
                FROM commits c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.organization_id = $1
                AND (
                    to_tsvector('english', c.message) @@ plainto_tsquery('english', $2)
                    OR c.message ILIKE $3
                )
                ORDER BY c.commit_date DESC
                LIMIT $4
            """, org_id, query, f'%{query}%', limit)
            return [dict(row) for row in rows]

    # ========================================================================
    # INTENT ANALYZER: Decision Storage Methods
    # ========================================================================

    async def get_jira_ticket_by_key(self, ticket_key: str, org_id: str) -> Optional[Dict]:
        """Get a single Jira ticket by its key."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM jira_tickets
                WHERE organization_id = $1 AND ticket_key = $2
            """, org_id, ticket_key)
            return dict(row) if row else None

    async def get_commits_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get all commits that reference a specific ticket."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM commits
                WHERE organization_id = $1
                AND $2 = ANY(ticket_references)
                ORDER BY commit_date DESC
            """, org_id, ticket_key)
            return [dict(row) for row in rows]

    async def get_prs_for_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get all PRs that reference a specific ticket."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM pull_requests
                WHERE organization_id = $1
                AND (
                    title ILIKE $2
                    OR description ILIKE $2
                )
                ORDER BY created_at DESC
            """, org_id, f'%{ticket_key}%')
            return [dict(row) for row in rows]

    async def create_decision(self, decision_data: Dict, org_id: str) -> Dict:
        """Store a decision analysis in the database."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO decisions (
                    organization_id, decision_id, ticket_key, decision_summary,
                    problem_statement, alternatives_considered, chosen_approach,
                    rationale, constraints, risks, tradeoffs, stakeholders,
                    implementation_commits, related_prs, related_docs,
                    raw_analysis, confidence_score
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
                )
                ON CONFLICT (organization_id, decision_id)
                DO UPDATE SET
                    decision_summary = EXCLUDED.decision_summary,
                    problem_statement = EXCLUDED.problem_statement,
                    alternatives_considered = EXCLUDED.alternatives_considered,
                    chosen_approach = EXCLUDED.chosen_approach,
                    rationale = EXCLUDED.rationale,
                    constraints = EXCLUDED.constraints,
                    risks = EXCLUDED.risks,
                    tradeoffs = EXCLUDED.tradeoffs,
                    stakeholders = EXCLUDED.stakeholders,
                    implementation_commits = EXCLUDED.implementation_commits,
                    related_prs = EXCLUDED.related_prs,
                    related_docs = EXCLUDED.related_docs,
                    raw_analysis = EXCLUDED.raw_analysis,
                    confidence_score = EXCLUDED.confidence_score,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
            """,
                org_id,
                decision_data.get('decision_id'),
                decision_data.get('ticket_key'),
                decision_data.get('decision_summary'),
                decision_data.get('problem_statement'),
                json.dumps(decision_data.get('alternatives_considered', [])),
                decision_data.get('chosen_approach'),
                decision_data.get('rationale', decision_data.get('chosen_approach')),  # Use chosen_approach as rationale if not provided
                json.dumps(decision_data.get('constraints', [])),
                json.dumps(decision_data.get('risks', [])),
                decision_data.get('tradeoffs', ''),
                json.dumps(decision_data.get('stakeholders', [])),
                json.dumps(decision_data.get('implementation_commits', [])),
                json.dumps(decision_data.get('related_prs', [])),
                json.dumps(decision_data.get('related_docs', [])),
                decision_data.get('raw_analysis', ''),
                decision_data.get('confidence_score', 0.8)
            )
            return dict(row)

    async def get_decision(self, decision_id: str, org_id: str) -> Optional[Dict]:
        """Get a decision by its ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM decisions
                WHERE organization_id = $1 AND decision_id = $2
            """, org_id, decision_id)
            return dict(row) if row else None

    async def get_decisions_by_ticket(self, ticket_key: str, org_id: str) -> List[Dict]:
        """Get all decisions related to a specific ticket."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM decisions
                WHERE organization_id = $1 AND ticket_key = $2
                ORDER BY created_at DESC
            """, org_id, ticket_key)
            return [dict(row) for row in rows]

    async def search_decisions(self, query: str, org_id: str, limit: int = 10) -> List[Dict]:
        """Search decisions using full-text search."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *,
                    ts_rank(to_tsvector('english', decision_summary || ' ' || COALESCE(problem_statement, '') || ' ' || COALESCE(chosen_approach, '')), plainto_tsquery('english', $2)) as rank
                FROM decisions
                WHERE organization_id = $1
                AND (
                    to_tsvector('english', decision_summary) @@ plainto_tsquery('english', $2)
                    OR to_tsvector('english', problem_statement) @@ plainto_tsquery('english', $2)
                    OR to_tsvector('english', chosen_approach) @@ plainto_tsquery('english', $2)
                )
                ORDER BY rank DESC, created_at DESC
                LIMIT $3
            """, org_id, query, limit)
            return [dict(row) for row in rows]

    async def get_all_decisions(self, org_id: str, limit: int = 100) -> List[Dict]:
        """Get all decisions for an organization."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM decisions
                WHERE organization_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, org_id, limit)
            return [dict(row) for row in rows]

# Global database service
db_service = DatabaseService()