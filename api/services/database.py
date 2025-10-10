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

# Global database service
db_service = DatabaseService()