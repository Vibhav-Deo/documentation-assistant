"""performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-01-10 00:01:00

"""
from alembic import op

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GIN indexes for array searches
    op.execute('CREATE INDEX idx_jira_labels_gin ON jira_tickets USING GIN (labels)')
    op.execute('CREATE INDEX idx_jira_components_gin ON jira_tickets USING GIN (components)')
    op.execute('CREATE INDEX idx_commits_files_gin ON commits USING GIN (files_changed)')
    op.execute('CREATE INDEX idx_commits_tickets_gin ON commits USING GIN (ticket_references)')
    op.execute('CREATE INDEX idx_code_functions_gin ON code_files USING GIN (functions)')
    op.execute('CREATE INDEX idx_code_classes_gin ON code_files USING GIN (classes)')
    op.execute('CREATE INDEX idx_pr_files_gin ON pull_requests USING GIN (files_changed)')
    op.execute('CREATE INDEX idx_pr_tickets_gin ON pull_requests USING GIN (ticket_references)')
    
    # Trigram indexes for text search
    op.execute('CREATE INDEX idx_jira_summary_trgm ON jira_tickets USING GIN (summary gin_trgm_ops)')
    op.execute('CREATE INDEX idx_jira_description_trgm ON jira_tickets USING GIN (description gin_trgm_ops)')
    op.execute('CREATE INDEX idx_commits_message_trgm ON commits USING GIN (message gin_trgm_ops)')
    op.execute('CREATE INDEX idx_code_path_trgm ON code_files USING GIN (file_path gin_trgm_ops)')
    op.execute('CREATE INDEX idx_pr_title_trgm ON pull_requests USING GIN (title gin_trgm_ops)')
    
    # Composite indexes for common queries
    op.create_index('idx_jira_org_status', 'jira_tickets', ['organization_id', 'status'])
    op.create_index('idx_jira_org_created', 'jira_tickets', ['organization_id', 'created_date'])
    op.create_index('idx_commits_org_date', 'commits', ['organization_id', 'commit_date'])
    op.create_index('idx_commits_repo_date', 'commits', ['repository_id', 'commit_date'])
    op.create_index('idx_code_org_lang', 'code_files', ['organization_id', 'language'])
    op.create_index('idx_pr_org_status', 'pull_requests', ['organization_id', 'status'])
    
    # Partial indexes for active records
    op.execute('CREATE INDEX idx_users_active ON users (organization_id) WHERE is_active = true')
    op.execute('CREATE INDEX idx_orgs_active ON organizations (id) WHERE is_active = true')
    op.execute('CREATE INDEX idx_jira_open ON jira_tickets (organization_id, ticket_key) WHERE status NOT IN (\'Done\', \'Closed\', \'Resolved\')')


def downgrade() -> None:
    op.drop_index('idx_jira_open')
    op.drop_index('idx_orgs_active')
    op.drop_index('idx_users_active')
    op.drop_index('idx_pr_org_status')
    op.drop_index('idx_code_org_lang')
    op.drop_index('idx_commits_repo_date')
    op.drop_index('idx_commits_org_date')
    op.drop_index('idx_jira_org_created')
    op.drop_index('idx_jira_org_status')
    op.drop_index('idx_pr_title_trgm')
    op.drop_index('idx_code_path_trgm')
    op.drop_index('idx_commits_message_trgm')
    op.drop_index('idx_jira_description_trgm')
    op.drop_index('idx_jira_summary_trgm')
    op.drop_index('idx_pr_tickets_gin')
    op.drop_index('idx_pr_files_gin')
    op.drop_index('idx_code_classes_gin')
    op.drop_index('idx_code_functions_gin')
    op.drop_index('idx_commits_tickets_gin')
    op.drop_index('idx_commits_files_gin')
    op.drop_index('idx_jira_components_gin')
    op.drop_index('idx_jira_labels_gin')
