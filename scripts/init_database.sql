-- ============================================================
-- Database Initialization Script
-- Combines schema creation and seed data
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- DROP EXISTING TABLES (if any)
-- ============================================================
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS decisions CASCADE;
DROP TABLE IF EXISTS pull_requests CASCADE;
DROP TABLE IF EXISTS code_files CASCADE;
DROP TABLE IF EXISTS commits CASCADE;
DROP TABLE IF EXISTS jira_tickets CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

-- ============================================================
-- CREATE TABLES
-- ============================================================

-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    monthly_quota INTEGER DEFAULT 1000,
    used_quota INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT,
    name VARCHAR(255) NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Repositories table
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repo_url TEXT NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    provider VARCHAR(50),
    branch VARCHAR(255),
    file_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jira tickets table
CREATE TABLE jira_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    ticket_key VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50),
    issue_type VARCHAR(50),
    priority VARCHAR(50),
    assignee VARCHAR(255),
    reporter VARCHAR(255),
    labels TEXT[],
    components TEXT[],
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    resolved_date TIMESTAMP,
    story_points INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Commits table
CREATE TABLE commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    sha VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    commit_date TIMESTAMP,
    files_changed TEXT[],
    additions INTEGER,
    deletions INTEGER,
    ticket_references TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Code files table
CREATE TABLE code_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    language VARCHAR(50),
    size_bytes INTEGER,
    functions TEXT[],
    classes TEXT[],
    imports TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pull requests table
CREATE TABLE pull_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    pr_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50),
    author VARCHAR(255),
    created_date TIMESTAMP,
    merged_date TIMESTAMP,
    ticket_references TEXT[],
    files_changed TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Decisions table
CREATE TABLE decisions (
    id VARCHAR(255) PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    ticket_key VARCHAR(50) NOT NULL,
    decision_summary TEXT,
    problem_statement TEXT,
    alternatives_considered JSONB,
    chosen_approach TEXT,
    constraints TEXT[],
    risks TEXT[],
    stakeholders TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- CREATE INDEXES
-- ============================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_active ON users(organization_id) WHERE is_active = true;

-- Repositories indexes
CREATE INDEX idx_repos_org ON repositories(organization_id);

-- Jira tickets indexes
CREATE INDEX idx_jira_org ON jira_tickets(organization_id);
CREATE INDEX idx_jira_key ON jira_tickets(ticket_key);
CREATE INDEX idx_jira_status ON jira_tickets(status);
CREATE INDEX idx_jira_assignee ON jira_tickets(assignee);
CREATE INDEX idx_jira_org_status ON jira_tickets(organization_id, status);
CREATE INDEX idx_jira_org_created ON jira_tickets(organization_id, created_date);
CREATE INDEX idx_jira_open ON jira_tickets(organization_id, ticket_key) WHERE status NOT IN ('Done', 'Closed', 'Resolved');

-- GIN indexes for array searches
CREATE INDEX idx_jira_labels_gin ON jira_tickets USING GIN (labels);
CREATE INDEX idx_jira_components_gin ON jira_tickets USING GIN (components);

-- Trigram indexes for text search
CREATE INDEX idx_jira_summary_trgm ON jira_tickets USING GIN (summary gin_trgm_ops);
CREATE INDEX idx_jira_description_trgm ON jira_tickets USING GIN (description gin_trgm_ops);

-- Commits indexes
CREATE INDEX idx_commits_org ON commits(organization_id);
CREATE INDEX idx_commits_repo ON commits(repository_id);
CREATE INDEX idx_commits_sha ON commits(sha);
CREATE INDEX idx_commits_author ON commits(author_email);
CREATE INDEX idx_commits_org_date ON commits(organization_id, commit_date);
CREATE INDEX idx_commits_repo_date ON commits(repository_id, commit_date);
CREATE INDEX idx_commits_files_gin ON commits USING GIN (files_changed);
CREATE INDEX idx_commits_tickets_gin ON commits USING GIN (ticket_references);
CREATE INDEX idx_commits_message_trgm ON commits USING GIN (message gin_trgm_ops);

-- Code files indexes
CREATE INDEX idx_code_org ON code_files(organization_id);
CREATE INDEX idx_code_repo ON code_files(repository_id);
CREATE INDEX idx_code_path ON code_files(file_path);
CREATE INDEX idx_code_lang ON code_files(language);
CREATE INDEX idx_code_org_lang ON code_files(organization_id, language);
CREATE INDEX idx_code_functions_gin ON code_files USING GIN (functions);
CREATE INDEX idx_code_classes_gin ON code_files USING GIN (classes);
CREATE INDEX idx_code_path_trgm ON code_files USING GIN (file_path gin_trgm_ops);

-- Pull requests indexes
CREATE INDEX idx_pr_org ON pull_requests(organization_id);
CREATE INDEX idx_pr_repo ON pull_requests(repository_id);
CREATE INDEX idx_pr_number ON pull_requests(pr_number);
CREATE INDEX idx_pr_org_status ON pull_requests(organization_id, status);
CREATE INDEX idx_pr_files_gin ON pull_requests USING GIN (files_changed);
CREATE INDEX idx_pr_tickets_gin ON pull_requests USING GIN (ticket_references);
CREATE INDEX idx_pr_title_trgm ON pull_requests USING GIN (title gin_trgm_ops);

-- Decisions indexes
CREATE INDEX idx_decisions_org ON decisions(organization_id);
CREATE INDEX idx_decisions_ticket ON decisions(ticket_key);

-- Audit logs indexes
CREATE INDEX idx_audit_org ON audit_logs(organization_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- Organizations indexes
CREATE INDEX idx_orgs_active ON organizations(id) WHERE is_active = true;

-- ============================================================
-- SEED DATA - Organizations and Users
-- ============================================================

-- Create Demo Organization
INSERT INTO organizations (id, name, plan, monthly_quota, used_quota)
VALUES
    ('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'Acme Corp', 'enterprise', -1, 0),
    ('19cf9fd1-71b0-4401-a325-a971d19b79e7', 'Demo Organization', 'pro', 10000, 0);

-- Create Users (password hashes are for: demo123, admin123, user123)
-- Note: These are bcrypt hashes, you may need to regenerate them
INSERT INTO users (email, password_hash, name, role, organization_id)
VALUES
    ('admin@acmecorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW7nJfK5F5aq', 'John Admin', 'admin', '529d2ca9-6fd1-4fee-9105-dbde1499f937'),
    ('user@acmecorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW7nJfK5F5aq', 'Jane User', 'user', '529d2ca9-6fd1-4fee-9105-dbde1499f937'),
    ('demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW7nJfK5F5aq', 'Demo User', 'user', '19cf9fd1-71b0-4401-a325-a971d19b79e7');

-- ============================================================
-- SEED DATA - Repositories
-- ============================================================

INSERT INTO repositories (id, organization_id, repo_name, repo_url, provider, branch, file_count, metadata)
VALUES
    ('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'backend-api', 'https://github.com/acmecorp/backend-api', 'github', 'main', 156, '{"language": "Python", "framework": "FastAPI", "stars": 234}'),
    ('22222222-2222-2222-2222-222222222222', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'frontend-web', 'https://github.com/acmecorp/frontend-web', 'github', 'main', 203, '{"language": "TypeScript", "framework": "React", "stars": 189}'),
    ('33333333-3333-3333-3333-333333333333', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'mobile-app', 'https://github.com/acmecorp/mobile-app', 'github', 'main', 178, '{"language": "Kotlin", "framework": "Jetpack Compose", "stars": 145}'),
    ('44444444-4444-4444-4444-444444444444', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'infrastructure', 'https://github.com/acmecorp/infrastructure', 'github', 'main', 89, '{"language": "Terraform", "provider": "AWS", "stars": 67}');

-- ============================================================
-- SEED DATA - Jira Tickets (30 tickets)
-- ============================================================

INSERT INTO jira_tickets (organization_id, ticket_key, summary, description, issue_type, status, priority, assignee, reporter, created_date, updated_date, resolved_date, story_points, labels, components)
VALUES
-- AUTHENTICATION & AUTHORIZATION (AUTH) - 6 tickets
('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'AUTH-101', 'Implement OAuth2 Authentication System',
'As a user, I need to authenticate using OAuth2 so that I can securely access the application.

Requirements:
- Support Google and GitHub OAuth providers
- Implement token refresh mechanism
- Store encrypted tokens
- Add role-based access control (RBAC)

Technical Considerations:
- Use JWT for session management
- Implement token rotation
- Add rate limiting for auth endpoints',
'Story', 'Done', 'High', 'Sarah Johnson', 'Product Manager', '2024-01-05', '2024-01-25', '2024-01-25', 8, ARRAY['security', 'authentication'], ARRAY['backend', 'security']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'AUTH-102', 'Add Multi-Factor Authentication',
'Implement MFA using TOTP (Time-based One-Time Password) for enhanced security.

Acceptance Criteria:
- Users can enable/disable MFA
- Support authenticator apps (Google Authenticator, Authy)
- Provide backup codes
- Add recovery mechanism',
'Story', 'In Progress', 'High', 'Mike Chen', 'Security Lead', '2024-01-15', '2024-02-10', NULL, 5, ARRAY['security', 'authentication', 'mfa'], ARRAY['backend', 'security']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'AUTH-103', 'Session Management Improvements',
'Improve session handling to support multiple devices and concurrent sessions.

Tasks:
- Track active sessions per user
- Allow users to revoke sessions
- Implement session timeout policies
- Add device fingerprinting',
'Story', 'To Do', 'Medium', 'Sarah Johnson', 'Product Manager', '2024-02-01', '2024-02-01', NULL, 3, ARRAY['security', 'sessions'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'AUTH-104', 'Fix JWT Token Expiration Bug',
'Users are getting logged out prematurely. JWT tokens are expiring before the configured timeout.

Steps to Reproduce:
1. Log in to application
2. Wait 30 minutes
3. Try to make API call
4. Observe 401 Unauthorized error

Expected: Token should be valid for 8 hours
Actual: Token expires after ~45 minutes',
'Bug', 'Done', 'Critical', 'Mike Chen', 'QA Team', '2024-01-18', '2024-01-19', '2024-01-19', 2, ARRAY['bug', 'authentication'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'AUTH-105', 'Add Password Strength Requirements',
'Implement password strength validation and password complexity requirements.

Requirements:
- Minimum 12 characters
- Must include uppercase, lowercase, numbers, special chars
- Check against common password lists
- Add password strength meter in UI',
'Story', 'Done', 'Medium', 'Emily Zhang', 'Security Lead', '2024-01-20', '2024-01-28', '2024-01-28', 2, ARRAY['security', 'authentication'], ARRAY['backend', 'frontend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'AUTH-106', 'Implement API Key Management',
'Allow users to generate and manage API keys for programmatic access.

Features:
- Generate multiple API keys
- Set expiration dates
- Scope permissions per key
- Revoke keys
- Track key usage',
'Story', 'In Progress', 'Medium', 'Sarah Johnson', 'Product Manager', '2024-02-05', '2024-02-12', NULL, 5, ARRAY['api', 'security'], ARRAY['backend']),

-- DATABASE (DB) - 5 tickets
('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'DB-201', 'Database Schema Migration to PostgreSQL',
'Migrate from MySQL to PostgreSQL for better performance and features.

Migration Plan:
1. Set up PostgreSQL cluster
2. Create schema migration scripts
3. Migrate data with zero downtime
4. Update application connection strings
5. Test thoroughly

Risks:
- Data loss during migration
- Application downtime
- Query performance differences',
'Epic', 'Done', 'Critical', 'David Park', 'Tech Lead', '2023-12-01', '2024-01-15', '2024-01-15', 13, ARRAY['database', 'migration'], ARRAY['backend', 'infrastructure']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'DB-202', 'Add Database Connection Pooling',
'Implement connection pooling to improve database performance and reduce connection overhead.

Implementation:
- Use PgBouncer for connection pooling
- Configure pool size based on load testing
- Add monitoring for pool utilization
- Handle connection failures gracefully',
'Story', 'Done', 'High', 'David Park', 'Tech Lead', '2024-01-10', '2024-01-22', '2024-01-22', 3, ARRAY['database', 'performance'], ARRAY['backend', 'infrastructure']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'DB-203', 'Optimize Slow Queries',
'Several queries are taking >5 seconds to execute. Need to optimize with proper indexes.

Slow Queries:
- User search by email pattern
- Order history with joins
- Product catalog filtering
- Analytics aggregations

Solution: Add composite indexes, rewrite queries, consider materialized views',
'Story', 'In Progress', 'High', 'David Park', 'Performance Team', '2024-02-01', '2024-02-10', NULL, 5, ARRAY['database', 'performance', 'optimization'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'DB-204', 'Implement Database Backup Strategy',
'Set up automated backups with point-in-time recovery capability.

Requirements:
- Daily full backups
- Continuous WAL archiving
- Retention policy: 30 days
- Test restore procedures monthly
- Backup to S3 with encryption',
'Story', 'To Do', 'High', 'David Park', 'DevOps Team', '2024-02-05', '2024-02-05', NULL, 3, ARRAY['database', 'backup', 'disaster-recovery'], ARRAY['infrastructure']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'DB-205', 'Add Database Monitoring and Alerts',
'Set up comprehensive monitoring for database health and performance.

Metrics to Track:
- Query performance (slow queries)
- Connection pool usage
- Disk space utilization
- Replication lag
- Cache hit ratios

Alerts:
- Disk space >80%
- Replication lag >1 minute
- Connection pool exhaustion',
'Story', 'To Do', 'Medium', 'David Park', 'DevOps Team', '2024-02-08', '2024-02-08', NULL, 3, ARRAY['database', 'monitoring', 'observability'], ARRAY['infrastructure']),

-- USER INTERFACE (UI) - 6 tickets
('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'UI-301', 'Redesign Dashboard Layout',
'Complete overhaul of the main dashboard to improve user experience and information density.

Design Goals:
- Modern, clean interface
- Responsive design for mobile/tablet
- Dark mode support
- Customizable widgets
- Improved data visualization',
'Story', 'Done', 'High', 'Emily Zhang', 'Design Lead', '2024-01-08', '2024-02-05', '2024-02-05', 8, ARRAY['ui', 'design', 'dashboard'], ARRAY['frontend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'UI-302', 'Implement Responsive Navigation Menu',
'Create a responsive navigation menu that works well on all screen sizes.

Features:
- Hamburger menu for mobile
- Collapsible sidebar for desktop
- Search functionality
- Breadcrumbs for deep navigation
- Keyboard shortcuts',
'Story', 'Done', 'Medium', 'Emily Zhang', 'Frontend Team', '2024-01-15', '2024-01-30', '2024-01-30', 5, ARRAY['ui', 'navigation', 'responsive'], ARRAY['frontend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'UI-303', 'Add Dark Mode Support',
'Implement system-wide dark mode with user preference persistence.

Requirements:
- Toggle between light/dark/system
- Save user preference
- Smooth transitions
- Consistent color palette
- Accessibility compliance (WCAG 2.1)',
'Story', 'In Progress', 'Medium', 'Emily Zhang', 'Frontend Team', '2024-02-01', '2024-02-12', NULL, 3, ARRAY['ui', 'dark-mode', 'accessibility'], ARRAY['frontend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'UI-304', 'Fix Chart Rendering Performance',
'Charts with large datasets (>10k points) are causing browser lag and freezing.

Issue:
- Charts freeze when rendering large datasets
- Browser becomes unresponsive
- Memory usage spikes

Solutions:
- Implement data sampling for large datasets
- Use canvas instead of SVG
- Add virtualization for chart legends
- Debounce zoom/pan operations',
'Bug', 'Done', 'High', 'Alex Rivera', 'Frontend Team', '2024-01-25', '2024-01-27', '2024-01-27', 3, ARRAY['bug', 'performance', 'charts'], ARRAY['frontend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'UI-305', 'Implement Form Validation Framework',
'Create a reusable form validation framework for consistent UX across all forms.

Features:
- Real-time validation
- Custom validation rules
- Error message display
- Async validation (email uniqueness, etc.)
- Form state management
- Accessibility support',
'Story', 'Done', 'Medium', 'Alex Rivera', 'Frontend Team', '2024-01-20', '2024-02-03', '2024-02-03', 5, ARRAY['ui', 'forms', 'validation'], ARRAY['frontend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'UI-306', 'Add Loading States and Skeletons',
'Improve perceived performance by adding skeleton screens and loading states.

Implementation:
- Skeleton screens for all major views
- Loading spinners for async operations
- Progressive loading for images
- Optimistic UI updates',
'Story', 'To Do', 'Low', 'Emily Zhang', 'Frontend Team', '2024-02-10', '2024-02-10', NULL, 2, ARRAY['ui', 'loading', 'ux'], ARRAY['frontend']),

-- API (API) - 5 tickets
('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'API-401', 'Design RESTful API v2',
'Design and implement version 2 of the API with improved consistency and functionality.

Key Changes:
- Consistent resource naming
- HATEOAS implementation
- Better error responses
- Pagination standardization
- Rate limiting
- API versioning strategy',
'Epic', 'In Progress', 'High', 'Michael Torres', 'API Team', '2024-01-10', '2024-02-12', NULL, 13, ARRAY['api', 'design', 'architecture'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'API-402', 'Implement GraphQL Endpoint',
'Add GraphQL endpoint alongside REST API for flexible data querying.

Features:
- Schema definition
- Query optimization
- Nested resource fetching
- Real-time subscriptions
- DataLoader for N+1 prevention
- Apollo Server integration',
'Story', 'Done', 'Medium', 'Michael Torres', 'API Team', '2024-01-15', '2024-02-08', '2024-02-08', 8, ARRAY['api', 'graphql'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'API-403', 'Add Rate Limiting and Throttling',
'Implement rate limiting to prevent API abuse and ensure fair usage.

Strategy:
- Token bucket algorithm
- Per-user and per-IP limits
- Different limits for authenticated vs anonymous
- Rate limit headers in responses
- Redis for distributed rate limiting',
'Story', 'Done', 'High', 'Sarah Johnson', 'Backend Team', '2024-01-18', '2024-01-26', '2024-01-26', 5, ARRAY['api', 'security', 'rate-limiting'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'API-404', 'Fix 500 Error on User Profile Update',
'Intermittent 500 errors when updating user profile with specific field combinations.

Error Log:
SQLAlchemy.exc.IntegrityError: duplicate key value violates unique constraint "users_email_key"

Root Cause:
Race condition when multiple simultaneous updates occur. Email uniqueness check happens before transaction commit.

Solution: Use SELECT FOR UPDATE or implement optimistic locking',
'Bug', 'Done', 'Critical', 'Michael Torres', 'Customer Support', '2024-02-01', '2024-02-02', '2024-02-02', 2, ARRAY['bug', 'api', 'critical'], ARRAY['backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'API-405', 'Add API Documentation with OpenAPI',
'Generate comprehensive API documentation using OpenAPI 3.0 specification.

Requirements:
- Interactive documentation (Swagger UI)
- Code examples in multiple languages
- Authentication documentation
- Error code reference
- Rate limit documentation
- Webhook documentation',
'Story', 'In Progress', 'Medium', 'Michael Torres', 'API Team', '2024-02-05', '2024-02-12', NULL, 3, ARRAY['api', 'documentation'], ARRAY['backend']),

-- MOBILE (MOB) - 4 tickets
('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'MOB-501', 'Implement Offline Mode',
'Add offline support for core features using local database synchronization.

Features:
- Local SQLite database
- Sync when connection restored
- Conflict resolution
- Offline indicators
- Queue failed requests',
'Story', 'In Progress', 'High', 'Jessica Martinez', 'Mobile Team', '2024-01-20', '2024-02-12', NULL, 13, ARRAY['mobile', 'offline', 'sync'], ARRAY['mobile']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'MOB-502', 'Add Push Notifications',
'Implement push notifications for important events and updates.

Notification Types:
- New messages
- Task assignments
- System alerts
- Marketing (opt-in)

Technical:
- FCM for Android
- APNs for iOS
- Backend notification service
- User preferences
- Rich notifications with actions',
'Story', 'Done', 'High', 'Jessica Martinez', 'Mobile Team', '2024-01-25', '2024-02-10', '2024-02-10', 5, ARRAY['mobile', 'notifications', 'engagement'], ARRAY['mobile', 'backend']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'MOB-503', 'Fix App Crash on Image Upload',
'App crashes when uploading images larger than 10MB on Android 12+.

Error:
android.os.TransactionTooLargeException: data parcel size 10485760 bytes

Root Cause:
Trying to pass large bitmap through Intent extras. Android has 1MB limit.

Solution: Use FileProvider and pass URI instead of bitmap data',
'Bug', 'Done', 'Critical', 'Roberto Silva', 'Mobile Team', '2024-02-03', '2024-02-04', '2024-02-04', 2, ARRAY['bug', 'mobile', 'android'], ARRAY['mobile']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'MOB-504', 'Optimize App Startup Time',
'App takes 5+ seconds to start on mid-range devices. Need to optimize cold start time.

Issues:
- Large dependency injection graph initialization
- Loading unnecessary data on startup
- Synchronous network calls blocking UI
- Heavy image processing on main thread

Target: <2 seconds cold start',
'Story', 'To Do', 'Medium', 'Roberto Silva', 'Mobile Team', '2024-02-08', '2024-02-08', NULL, 5, ARRAY['mobile', 'performance', 'optimization'], ARRAY['mobile']),

-- INFRASTRUCTURE (INFRA) - 4 tickets
('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'INFRA-601', 'Migrate to Kubernetes',
'Migrate from EC2-based deployment to Kubernetes for better scalability and management.

Migration Plan:
1. Set up EKS cluster
2. Containerize all services
3. Create Kubernetes manifests
4. Set up CI/CD pipelines
5. Blue-green deployment strategy
6. Migrate production with zero downtime',
'Epic', 'In Progress', 'Critical', 'Chris Anderson', 'DevOps Team', '2024-01-15', '2024-02-12', NULL, 21, ARRAY['infrastructure', 'kubernetes', 'migration'], ARRAY['infrastructure']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'INFRA-602', 'Set Up Monitoring and Logging',
'Implement comprehensive monitoring and centralized logging infrastructure.

Stack:
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for logs
- Jaeger for distributed tracing
- PagerDuty for alerts',
'Story', 'Done', 'High', 'Chris Anderson', 'DevOps Team', '2024-01-20', '2024-02-05', '2024-02-05', 8, ARRAY['infrastructure', 'monitoring', 'observability'], ARRAY['infrastructure']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'INFRA-603', 'Implement Blue-Green Deployment',
'Set up blue-green deployment strategy for zero-downtime releases.

Requirements:
- Automated deployment pipeline
- Traffic switching mechanism
- Rollback capability
- Smoke tests before traffic switch
- Database migration handling',
'Story', 'Done', 'High', 'Chris Anderson', 'DevOps Team', '2024-02-01', '2024-02-08', '2024-02-08', 5, ARRAY['infrastructure', 'deployment', 'cicd'], ARRAY['infrastructure']),

('529d2ca9-6fd1-4fee-9105-dbde1499f937', 'INFRA-604', 'Optimize AWS Costs',
'Reduce AWS spending by optimizing resource usage and purchasing reserved instances.

Analysis:
- Current monthly cost: $15,000
- Target: $10,000 (33% reduction)

Optimization Strategies:
- Reserved instances for steady workloads
- Spot instances for batch jobs
- Right-size overprovisioned instances
- Remove unused resources
- Implement auto-scaling policies',
'Story', 'To Do', 'Medium', 'Chris Anderson', 'Finance Team', '2024-02-10', '2024-02-10', NULL, 3, ARRAY['infrastructure', 'cost-optimization', 'aws'], ARRAY['infrastructure']);

-- ============================================================
-- SEED DATA - Commits (45 commits)
-- ============================================================

INSERT INTO commits (repository_id, organization_id, sha, message, author_name, author_email, commit_date, additions, deletions, ticket_references, metadata)
VALUES
-- AUTH-101 commits
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'feat(auth): implement OAuth2 authorization flow

- Add OAuth2 provider configuration for Google and GitHub
- Implement authorization code flow
- Add token exchange endpoints
- Store encrypted tokens in database
- Add refresh token mechanism

Breaking change: New /oauth2/authorize endpoint replaces /login',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-01-12 10:30:00', 1245, 230, ARRAY['AUTH-101'],
'{"pr_number": 101, "review_comments": 8}'),

('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(auth): add RBAC system with role hierarchy

- Implement role-based access control
- Define roles: admin, developer, viewer
- Add permission checking middleware
- Create role assignment API endpoints

Implements AUTH-101 RBAC requirements',
'Mike Chen', 'mike.chen@acmecorp.com', '2024-01-18 14:15:00', 890, 45, ARRAY['AUTH-101'],
'{"pr_number": 101, "review_comments": 5}'),

('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(auth): add JWT token management service

- Implement JWT signing and verification
- Add token refresh endpoint
- Implement token rotation for security
- Add rate limiting for token endpoints

Related to AUTH-101',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-01-22 09:45:00', 567, 23, ARRAY['AUTH-101'],
'{"pr_number": 101, "review_comments": 3}'),

-- AUTH-104 commits (JWT bug fix)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'g1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'fix(auth): correct JWT expiration time calculation

The JWT tokens were expiring after 45 minutes instead of 8 hours
due to incorrect time unit conversion. Changed from seconds to hours.

Before: exp = now + timedelta(seconds=28800)
After: exp = now + timedelta(hours=8)

Fixes AUTH-104',
'Mike Chen', 'mike.chen@acmecorp.com', '2024-01-19 08:30:00', 15, 8, ARRAY['AUTH-104'],
'{"pr_number": 105, "review_comments": 1}'),

-- DB-201 commits (PostgreSQL migration)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'k5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'feat(db): add PostgreSQL schema migration scripts

- Create Alembic migration setup
- Add initial schema migration
- Convert MySQL-specific queries to PostgreSQL
- Update ORM models for PostgreSQL

Part of DB-201 migration',
'David Park', 'david.park@acmecorp.com', '2024-01-08 09:00:00', 1567, 892, ARRAY['DB-201'],
'{"pr_number": 95, "review_comments": 12}'),

-- DB-202 commits (Connection pooling)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'm1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'feat(db): implement connection pooling with PgBouncer

- Add PgBouncer configuration
- Configure pool size based on load tests (pool_size=20)
- Add connection retry logic
- Implement health checks for connections

Implements DB-202',
'David Park', 'david.park@acmecorp.com', '2024-01-20 10:15:00', 345, 45, ARRAY['DB-202'],
'{"pr_number": 106, "review_comments": 4}'),

-- DB-203 commits (Query optimization)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'n2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'perf(db): add indexes for slow user search queries

- Add GIN index on user email with trigram support
- Add composite index on (organization_id, created_at)
- Add index on user status for filtering
- Query time reduced from 5.2s to 0.3s

Addresses DB-203',
'David Park', 'david.park@acmecorp.com', '2024-02-06 14:20:00', 45, 8, ARRAY['DB-203'],
'{"pr_number": 117, "review_comments": 2}'),

-- UI-301 commits (Dashboard redesign)
('22222222-2222-2222-2222-222222222222', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'o3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(ui): implement new dashboard layout

- Create responsive grid layout
- Add customizable widget system
- Implement drag-and-drop for widgets
- Add dashboard persistence
- Improve mobile experience

Major redesign for UI-301',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-01-25 11:00:00', 1234, 567, ARRAY['UI-301'],
'{"pr_number": 107, "review_comments": 15}'),

-- UI-304 commits (Chart performance fix)
('22222222-2222-2222-2222-222222222222', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 's1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'fix(ui): optimize chart rendering for large datasets

- Implement data sampling for datasets >10k points
- Switch from SVG to Canvas rendering
- Add virtualization for chart legends
- Debounce zoom/pan operations (300ms)

Fixes UI-304 performance issue',
'Alex Rivera', 'alex.rivera@acmecorp.com', '2024-01-27 09:30:00', 234, 178, ARRAY['UI-304'],
'{"pr_number": 109, "review_comments": 4}'),

-- API-402 commits (GraphQL)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'v4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(api): add GraphQL endpoint with Apollo Server

- Set up Apollo Server
- Define GraphQL schema
- Implement resolvers for main entities
- Add DataLoader for N+1 prevention
- Add GraphQL playground

Implements API-402',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-05 11:30:00', 1567, 23, ARRAY['API-402'],
'{"pr_number": 117, "review_comments": 12}'),

-- API-403 commits (Rate limiting)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'w5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'feat(api): implement rate limiting with Redis

- Add token bucket rate limiter
- Configure per-user and per-IP limits
- Add rate limit headers to responses
- Implement distributed rate limiting with Redis
- Add rate limit bypass for admin users

Implements API-403',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-01-24 09:15:00', 567, 34, ARRAY['API-403'],
'{"pr_number": 107, "review_comments": 6}'),

-- API-404 commits (Bug fix)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'x6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'fix(api): resolve race condition in user profile update

Added SELECT FOR UPDATE to prevent concurrent updates from
violating unique constraints. Also added optimistic locking
with version field.

Fixes API-404 critical bug',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-02 08:45:00', 45, 23, ARRAY['API-404'],
'{"pr_number": 115, "review_comments": 2}'),

-- MOB-502 commits (Push notifications)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'b4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(api): add push notification service

- Implement FCM server-side integration
- Create notification templates
- Add notification scheduling
- Implement user preference handling
- Add notification analytics

Backend for MOB-502',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-09 15:00:00', 678, 23, ARRAY['MOB-502'],
'{"pr_number": 119, "review_comments": 5}'),

-- MOB-503 commits (Image upload bug fix)
('33333333-3333-3333-3333-333333333333', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'c5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'fix(mobile): use FileProvider for large image uploads

Changed image upload to use FileProvider and URI passing
instead of passing bitmap data through Intent extras.
This fixes TransactionTooLargeException on Android 12+.

Fixes MOB-503',
'Roberto Silva', 'roberto.silva@acmecorp.com', '2024-02-04 09:15:00', 89, 67, ARRAY['MOB-503'],
'{"pr_number": 115, "review_comments": 2}'),

-- INFRA-602 commits (Monitoring)
('44444444-4444-4444-4444-444444444444', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'f2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(infra): set up Prometheus and Grafana

- Deploy Prometheus with Helm
- Configure service discovery
- Create Grafana dashboards
- Set up alerting rules
- Add PagerDuty integration

Implements INFRA-602',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-02 10:00:00', 1456, 123, ARRAY['INFRA-602'],
'{"pr_number": 113, "review_comments": 8}'),

-- INFRA-603 commits (Blue-green deployment)
('44444444-4444-4444-4444-444444444444', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'h4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(infra): implement blue-green deployment pipeline

- Create deployment pipeline with GitLab CI
- Add smoke tests before traffic switch
- Implement automatic rollback on failure
- Add manual approval gate
- Configure traffic switching

Implements INFRA-603',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-07 09:30:00', 890, 67, ARRAY['INFRA-603'],
'{"pr_number": 118, "review_comments": 7}'),

-- Commits without ticket references (for gap detection testing)
('11111111-1111-1111-1111-111111111111', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'i5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'refactor: improve error handling in API middleware

Refactored error handling to be more consistent across all
endpoints. Added custom exception classes and improved
error messages for better debugging.',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-11 10:15:00', 234, 123, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0}'),

('22222222-2222-2222-2222-222222222222', '529d2ca9-6fd1-4fee-9105-dbde1499f937', 'j6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'chore: update npm dependencies to latest versions

Updated all npm packages to their latest stable versions.
Fixed breaking changes in React 18 migration.',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-02-12 11:30:00', 45, 38, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0}');

-- ============================================================
-- SUMMARY
-- ============================================================

DO $$
DECLARE
    org_count INTEGER;
    user_count INTEGER;
    repo_count INTEGER;
    ticket_count INTEGER;
    commit_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_count FROM organizations;
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO repo_count FROM repositories;
    SELECT COUNT(*) INTO ticket_count FROM jira_tickets;
    SELECT COUNT(*) INTO commit_count FROM commits;

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Database Initialization Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Organizations: %', org_count;
    RAISE NOTICE 'Users: %', user_count;
    RAISE NOTICE 'Repositories: %', repo_count;
    RAISE NOTICE 'Jira Tickets: %', ticket_count;
    RAISE NOTICE 'Commits: %', commit_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Login Credentials:';
    RAISE NOTICE '  Admin: admin@acmecorp.com / admin123';
    RAISE NOTICE '  User: user@acmecorp.com / user123';
    RAISE NOTICE '  Demo: demo@example.com / demo123';
    RAISE NOTICE '========================================';
END $$;
