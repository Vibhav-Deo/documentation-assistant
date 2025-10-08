import asyncio
import asyncpg
import bcrypt
import os
from datetime import datetime

async def create_seed_data():
    """Create seed data for demo purposes"""
    
    # Database connection
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/confluence_rag")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("Creating seed data...")
        
        # Create Demo Organization
        demo_org = await conn.fetchrow("""
            INSERT INTO organizations (name, plan, monthly_quota, used_quota)
            VALUES ('Demo Organization', 'enterprise', -1, 0)
            ON CONFLICT DO NOTHING
            RETURNING id, name, plan
        """)
        
        if demo_org:
            print(f"✅ Created organization: {demo_org['name']} ({demo_org['plan']})")
            demo_org_id = demo_org['id']
        else:
            # Get existing demo org
            demo_org = await conn.fetchrow("SELECT id FROM organizations WHERE name = 'Demo Organization'")
            demo_org_id = demo_org['id']
            print("ℹ️ Demo organization already exists")
        
        # Create Acme Corp Organization
        acme_org = await conn.fetchrow("""
            INSERT INTO organizations (name, plan, monthly_quota, used_quota)
            VALUES ('Acme Corp', 'pro', 10000, 0)
            ON CONFLICT DO NOTHING
            RETURNING id, name, plan
        """)
        
        if acme_org:
            print(f"✅ Created organization: {acme_org['name']} ({acme_org['plan']})")
            acme_org_id = acme_org['id']
        else:
            # Get existing acme org
            acme_org = await conn.fetchrow("SELECT id FROM organizations WHERE name = 'Acme Corp'")
            acme_org_id = acme_org['id']
            print("ℹ️ Acme Corp organization already exists")
        
        # Hash passwords
        demo_password = bcrypt.hashpw("demo123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create Demo User
        demo_user = await conn.fetchrow("""
            INSERT INTO users (email, password_hash, name, role, organization_id)
            VALUES ('demo@example.com', $1, 'Demo User', 'user', $2)
            ON CONFLICT (email) DO NOTHING
            RETURNING id, email, name, role
        """, demo_password, demo_org_id)
        
        if demo_user:
            print(f"✅ Created user: {demo_user['name']} ({demo_user['email']}) - Role: {demo_user['role']}")
        else:
            print("ℹ️ Demo user already exists")
        
        # Create Admin User for Acme Corp
        admin_user = await conn.fetchrow("""
            INSERT INTO users (email, password_hash, name, role, organization_id)
            VALUES ('admin@acmecorp.com', $1, 'John Admin', 'admin', $2)
            ON CONFLICT (email) DO NOTHING
            RETURNING id, email, name, role
        """, admin_password, acme_org_id)
        
        if admin_user:
            print(f"✅ Created user: {admin_user['name']} ({admin_user['email']}) - Role: {admin_user['role']}")
        else:
            print("ℹ️ Admin user already exists")
        
        # Create Regular User for Acme Corp
        user_password = bcrypt.hashpw("user123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        regular_user = await conn.fetchrow("""
            INSERT INTO users (email, password_hash, name, role, organization_id)
            VALUES ('user@acmecorp.com', $1, 'Jane User', 'user', $2)
            ON CONFLICT (email) DO NOTHING
            RETURNING id, email, name, role
        """, user_password, acme_org_id)
        
        if regular_user:
            print(f"✅ Created user: {regular_user['name']} ({regular_user['email']}) - Role: {regular_user['role']}")
        else:
            print("ℹ️ Regular user already exists")
        
        print("\n🎉 Seed data creation completed!")
        print("\n📋 Login Credentials:")
        print("=" * 50)
        print("Demo User (Enterprise Plan - Unlimited):")
        print("  Email: demo@example.com")
        print("  Password: demo123")
        print()
        print("Acme Corp Admin (Pro Plan - 10,000 requests):")
        print("  Email: admin@acmecorp.com")
        print("  Password: admin123")
        print()
        print("Acme Corp User (Pro Plan - 10,000 requests):")
        print("  Email: user@acmecorp.com")
        print("  Password: user123")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_seed_data())