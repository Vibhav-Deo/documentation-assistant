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

# Global database service
db_service = DatabaseService()