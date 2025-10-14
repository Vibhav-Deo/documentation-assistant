"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-10 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    
    # Organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(50), server_default='free'),
        sa.Column('monthly_quota', sa.Integer, server_default='1000'),
        sa.Column('used_quota', sa.Integer, server_default='0'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), server_default='user'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_org', 'users', ['organization_id'])
    
    # Repositories table
    op.create_table('repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('repo_url', sa.Text, nullable=False),
        sa.Column('repo_name', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(50)),
        sa.Column('branch', sa.String(255)),
        sa.Column('file_count', sa.Integer, server_default='0'),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_repos_org', 'repositories', ['organization_id'])
    
    # Jira tickets table
    op.create_table('jira_tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticket_key', sa.String(50), nullable=False),
        sa.Column('summary', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50)),
        sa.Column('issue_type', sa.String(50)),
        sa.Column('priority', sa.String(50)),
        sa.Column('assignee', sa.String(255)),
        sa.Column('reporter', sa.String(255)),
        sa.Column('labels', postgresql.ARRAY(sa.String)),
        sa.Column('components', postgresql.ARRAY(sa.String)),
        sa.Column('created_date', sa.TIMESTAMP),
        sa.Column('updated_date', sa.TIMESTAMP),
        sa.Column('resolved_date', sa.TIMESTAMP),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_jira_org', 'jira_tickets', ['organization_id'])
    op.create_index('idx_jira_key', 'jira_tickets', ['ticket_key'])
    op.create_index('idx_jira_status', 'jira_tickets', ['status'])
    op.create_index('idx_jira_assignee', 'jira_tickets', ['assignee'])
    
    # Commits table
    op.create_table('commits',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sha', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('author_name', sa.String(255)),
        sa.Column('author_email', sa.String(255)),
        sa.Column('commit_date', sa.TIMESTAMP),
        sa.Column('files_changed', postgresql.ARRAY(sa.Text)),
        sa.Column('additions', sa.Integer),
        sa.Column('deletions', sa.Integer),
        sa.Column('ticket_references', postgresql.ARRAY(sa.String)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_commits_org', 'commits', ['organization_id'])
    op.create_index('idx_commits_repo', 'commits', ['repository_id'])
    op.create_index('idx_commits_sha', 'commits', ['sha'])
    op.create_index('idx_commits_author', 'commits', ['author_email'])
    
    # Code files table
    op.create_table('code_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_path', sa.Text, nullable=False),
        sa.Column('language', sa.String(50)),
        sa.Column('size_bytes', sa.Integer),
        sa.Column('functions', postgresql.ARRAY(sa.String)),
        sa.Column('classes', postgresql.ARRAY(sa.String)),
        sa.Column('imports', postgresql.ARRAY(sa.String)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_code_org', 'code_files', ['organization_id'])
    op.create_index('idx_code_repo', 'code_files', ['repository_id'])
    op.create_index('idx_code_path', 'code_files', ['file_path'])
    op.create_index('idx_code_lang', 'code_files', ['language'])
    
    # Pull requests table
    op.create_table('pull_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('repositories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pr_number', sa.Integer, nullable=False),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50)),
        sa.Column('author', sa.String(255)),
        sa.Column('created_date', sa.TIMESTAMP),
        sa.Column('merged_date', sa.TIMESTAMP),
        sa.Column('ticket_references', postgresql.ARRAY(sa.String)),
        sa.Column('files_changed', postgresql.ARRAY(sa.Text)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_pr_org', 'pull_requests', ['organization_id'])
    op.create_index('idx_pr_repo', 'pull_requests', ['repository_id'])
    op.create_index('idx_pr_number', 'pull_requests', ['pr_number'])
    
    # Decisions table
    op.create_table('decisions',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticket_key', sa.String(50), nullable=False),
        sa.Column('decision_summary', sa.Text),
        sa.Column('problem_statement', sa.Text),
        sa.Column('alternatives_considered', postgresql.JSONB),
        sa.Column('chosen_approach', sa.Text),
        sa.Column('constraints', postgresql.ARRAY(sa.Text)),
        sa.Column('risks', postgresql.ARRAY(sa.Text)),
        sa.Column('stakeholders', postgresql.ARRAY(sa.String)),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_decisions_org', 'decisions', ['organization_id'])
    op.create_index('idx_decisions_ticket', 'decisions', ['ticket_key'])
    
    # Audit logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('details', postgresql.JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_audit_org', 'audit_logs', ['organization_id'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('decisions')
    op.drop_table('pull_requests')
    op.drop_table('code_files')
    op.drop_table('commits')
    op.drop_table('jira_tickets')
    op.drop_table('repositories')
    op.drop_table('users')
    op.drop_table('organizations')
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
