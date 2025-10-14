#!/usr/bin/env python3
"""Database migration runner"""
import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run all pending migrations"""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/confluence_rag"))
    
    try:
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
