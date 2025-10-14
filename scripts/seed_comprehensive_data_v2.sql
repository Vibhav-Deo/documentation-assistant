-- Comprehensive Test Data Seed Script for Documentation Assistant v2
-- This creates a realistic dataset for testing all features
-- Corrected to match actual database schema

-- Use the existing organization
\set org_id '72fa38cc-f166-4ff4-ba76-411765b3cb94'

-- Clear existing test data (keeping organization)
DELETE FROM decisions WHERE organization_id = :'org_id';
DELETE FROM pull_requests WHERE organization_id = :'org_id';
DELETE FROM commits WHERE organization_id = :'org_id';
DELETE FROM code_files WHERE organization_id = :'org_id';
DELETE FROM jira_tickets WHERE organization_id = :'org_id';
DELETE FROM repositories WHERE organization_id = :'org_id';

-- Insert repositories first (needed for foreign keys)
INSERT INTO repositories (id, organization_id, repo_name, repo_url, provider, branch, file_count, metadata) VALUES
('11111111-1111-1111-1111-111111111111', :'org_id', 'backend-api', 'https://github.com/acmecorp/backend-api', 'github', 'main', 156, '{"language": "Python", "framework": "FastAPI", "stars": 234}'),
('22222222-2222-2222-2222-222222222222', :'org_id', 'frontend-web', 'https://github.com/acmecorp/frontend-web', 'github', 'main', 203, '{"language": "TypeScript", "framework": "React", "stars": 189}'),
('33333333-3333-3333-3333-333333333333', :'org_id', 'mobile-app', 'https://github.com/acmecorp/mobile-app', 'github', 'main', 178, '{"language": "Kotlin", "framework": "Jetpack Compose", "stars": 145}'),
('44444444-4444-4444-4444-444444444444', :'org_id', 'infrastructure', 'https://github.com/acmecorp/infrastructure', 'github', 'main', 89, '{"language": "Terraform", "provider": "AWS", "stars": 67}');

-- ============================================================
-- JIRA TICKETS - Comprehensive Dataset (30 tickets)
-- ============================================================

-- AUTHENTICATION & AUTHORIZATION (AUTH) - 6 tickets
INSERT INTO jira_tickets (organization_id, ticket_key, summary, description, issue_type, status, priority, assignee, reporter, created_date, updated_date, resolved_date, story_points, labels, components) VALUES
(:'org_id', 'AUTH-101', 'Implement OAuth2 Authentication System',
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

(:'org_id', 'AUTH-102', 'Add Multi-Factor Authentication',
'Implement MFA using TOTP (Time-based One-Time Password) for enhanced security.

Acceptance Criteria:
- Users can enable/disable MFA
- Support authenticator apps (Google Authenticator, Authy)
- Provide backup codes
- Add recovery mechanism',
'Story', 'In Progress', 'High', 'Mike Chen', 'Security Lead', '2024-01-15', '2024-02-10', NULL, 5, ARRAY['security', 'authentication', 'mfa'], ARRAY['backend', 'security']),

(:'org_id', 'AUTH-103', 'Session Management Improvements',
'Improve session handling to support multiple devices and concurrent sessions.

Tasks:
- Track active sessions per user
- Allow users to revoke sessions
- Implement session timeout policies
- Add device fingerprinting',
'Story', 'To Do', 'Medium', 'Sarah Johnson', 'Product Manager', '2024-02-01', '2024-02-01', NULL, 3, ARRAY['security', 'sessions'], ARRAY['backend']),

(:'org_id', 'AUTH-104', 'Fix JWT Token Expiration Bug',
'Users are getting logged out prematurely. JWT tokens are expiring before the configured timeout.

Steps to Reproduce:
1. Log in to application
2. Wait 30 minutes
3. Try to make API call
4. Observe 401 Unauthorized error

Expected: Token should be valid for 8 hours
Actual: Token expires after ~45 minutes',
'Bug', 'Done', 'Critical', 'Mike Chen', 'QA Team', '2024-01-18', '2024-01-19', '2024-01-19', 2, ARRAY['bug', 'authentication'], ARRAY['backend']),

(:'org_id', 'AUTH-105', 'Add Password Strength Requirements',
'Implement password strength validation and password complexity requirements.

Requirements:
- Minimum 12 characters
- Must include uppercase, lowercase, numbers, special chars
- Check against common password lists
- Add password strength meter in UI',
'Story', 'Done', 'Medium', 'Emily Zhang', 'Security Lead', '2024-01-20', '2024-01-28', '2024-01-28', 2, ARRAY['security', 'authentication'], ARRAY['backend', 'frontend']),

(:'org_id', 'AUTH-106', 'Implement API Key Management',
'Allow users to generate and manage API keys for programmatic access.

Features:
- Generate multiple API keys
- Set expiration dates
- Scope permissions per key
- Revoke keys
- Track key usage',
'Story', 'In Progress', 'Medium', 'Sarah Johnson', 'Product Manager', '2024-02-05', '2024-02-12', NULL, 5, ARRAY['api', 'security'], ARRAY['backend']),

-- DATABASE (DB) - 5 tickets
(:'org_id', 'DB-201', 'Database Schema Migration to PostgreSQL',
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

(:'org_id', 'DB-202', 'Add Database Connection Pooling',
'Implement connection pooling to improve database performance and reduce connection overhead.

Implementation:
- Use PgBouncer for connection pooling
- Configure pool size based on load testing
- Add monitoring for pool utilization
- Handle connection failures gracefully',
'Story', 'Done', 'High', 'David Park', 'Tech Lead', '2024-01-10', '2024-01-22', '2024-01-22', 3, ARRAY['database', 'performance'], ARRAY['backend', 'infrastructure']),

(:'org_id', 'DB-203', 'Optimize Slow Queries',
'Several queries are taking >5 seconds to execute. Need to optimize with proper indexes.

Slow Queries:
- User search by email pattern
- Order history with joins
- Product catalog filtering
- Analytics aggregations

Solution: Add composite indexes, rewrite queries, consider materialized views',
'Story', 'In Progress', 'High', 'David Park', 'Performance Team', '2024-02-01', '2024-02-10', NULL, 5, ARRAY['database', 'performance', 'optimization'], ARRAY['backend']),

(:'org_id', 'DB-204', 'Implement Database Backup Strategy',
'Set up automated backups with point-in-time recovery capability.

Requirements:
- Daily full backups
- Continuous WAL archiving
- Retention policy: 30 days
- Test restore procedures monthly
- Backup to S3 with encryption',
'Story', 'To Do', 'High', 'David Park', 'DevOps Team', '2024-02-05', '2024-02-05', NULL, 3, ARRAY['database', 'backup', 'disaster-recovery'], ARRAY['infrastructure']),

(:'org_id', 'DB-205', 'Add Database Monitoring and Alerts',
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
(:'org_id', 'UI-301', 'Redesign Dashboard Layout',
'Complete overhaul of the main dashboard to improve user experience and information density.

Design Goals:
- Modern, clean interface
- Responsive design for mobile/tablet
- Dark mode support
- Customizable widgets
- Improved data visualization

User Research:
- Conducted 12 user interviews
- Key pain points: cluttered layout, hard to find key metrics
- Users want: customizable dashboard, better charts',
'Story', 'Done', 'High', 'Emily Zhang', 'Design Lead', '2024-01-08', '2024-02-05', '2024-02-05', 8, ARRAY['ui', 'design', 'dashboard'], ARRAY['frontend']),

(:'org_id', 'UI-302', 'Implement Responsive Navigation Menu',
'Create a responsive navigation menu that works well on all screen sizes.

Features:
- Hamburger menu for mobile
- Collapsible sidebar for desktop
- Search functionality
- Breadcrumbs for deep navigation
- Keyboard shortcuts',
'Story', 'Done', 'Medium', 'Emily Zhang', 'Frontend Team', '2024-01-15', '2024-01-30', '2024-01-30', 5, ARRAY['ui', 'navigation', 'responsive'], ARRAY['frontend']),

(:'org_id', 'UI-303', 'Add Dark Mode Support',
'Implement system-wide dark mode with user preference persistence.

Requirements:
- Toggle between light/dark/system
- Save user preference
- Smooth transitions
- Consistent color palette
- Accessibility compliance (WCAG 2.1)',
'Story', 'In Progress', 'Medium', 'Emily Zhang', 'Frontend Team', '2024-02-01', '2024-02-12', NULL, 3, ARRAY['ui', 'dark-mode', 'accessibility'], ARRAY['frontend']),

(:'org_id', 'UI-304', 'Fix Chart Rendering Performance',
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

(:'org_id', 'UI-305', 'Implement Form Validation Framework',
'Create a reusable form validation framework for consistent UX across all forms.

Features:
- Real-time validation
- Custom validation rules
- Error message display
- Async validation (email uniqueness, etc.)
- Form state management
- Accessibility support',
'Story', 'Done', 'Medium', 'Alex Rivera', 'Frontend Team', '2024-01-20', '2024-02-03', '2024-02-03', 5, ARRAY['ui', 'forms', 'validation'], ARRAY['frontend']),

(:'org_id', 'UI-306', 'Add Loading States and Skeletons',
'Improve perceived performance by adding skeleton screens and loading states.

Implementation:
- Skeleton screens for all major views
- Loading spinners for async operations
- Progressive loading for images
- Optimistic UI updates',
'Story', 'To Do', 'Low', 'Emily Zhang', 'Frontend Team', '2024-02-10', '2024-02-10', NULL, 2, ARRAY['ui', 'loading', 'ux'], ARRAY['frontend']),

-- API (API) - 5 tickets
(:'org_id', 'API-401', 'Design RESTful API v2',
'Design and implement version 2 of the API with improved consistency and functionality.

Key Changes:
- Consistent resource naming
- HATEOAS implementation
- Better error responses
- Pagination standardization
- Rate limiting
- API versioning strategy

Breaking Changes:
- Date format: ISO 8601
- Error response structure
- Authentication headers',
'Epic', 'In Progress', 'High', 'Michael Torres', 'API Team', '2024-01-10', '2024-02-12', NULL, 13, ARRAY['api', 'design', 'architecture'], ARRAY['backend']),

(:'org_id', 'API-402', 'Implement GraphQL Endpoint',
'Add GraphQL endpoint alongside REST API for flexible data querying.

Features:
- Schema definition
- Query optimization
- Nested resource fetching
- Real-time subscriptions
- DataLoader for N+1 prevention
- Apollo Server integration',
'Story', 'Done', 'Medium', 'Michael Torres', 'API Team', '2024-01-15', '2024-02-08', '2024-02-08', 8, ARRAY['api', 'graphql'], ARRAY['backend']),

(:'org_id', 'API-403', 'Add Rate Limiting and Throttling',
'Implement rate limiting to prevent API abuse and ensure fair usage.

Strategy:
- Token bucket algorithm
- Per-user and per-IP limits
- Different limits for authenticated vs anonymous
- Rate limit headers in responses
- Redis for distributed rate limiting

Limits:
- Authenticated: 1000 req/hour
- Anonymous: 100 req/hour
- GraphQL: 500 req/hour',
'Story', 'Done', 'High', 'Sarah Johnson', 'Backend Team', '2024-01-18', '2024-01-26', '2024-01-26', 5, ARRAY['api', 'security', 'rate-limiting'], ARRAY['backend']),

(:'org_id', 'API-404', 'Fix 500 Error on User Profile Update',
'Intermittent 500 errors when updating user profile with specific field combinations.

Error Log:
SQLAlchemy.exc.IntegrityError: duplicate key value violates unique constraint "users_email_key"

Root Cause:
Race condition when multiple simultaneous updates occur. Email uniqueness check happens before transaction commit.

Solution: Use SELECT FOR UPDATE or implement optimistic locking',
'Bug', 'Done', 'Critical', 'Michael Torres', 'Customer Support', '2024-02-01', '2024-02-02', '2024-02-02', 2, ARRAY['bug', 'api', 'critical'], ARRAY['backend']),

(:'org_id', 'API-405', 'Add API Documentation with OpenAPI',
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
(:'org_id', 'MOB-501', 'Implement Offline Mode',
'Add offline support for core features using local database synchronization.

Features:
- Local SQLite database
- Sync when connection restored
- Conflict resolution
- Offline indicators
- Queue failed requests

Core Offline Features:
- View cached data
- Create/edit items offline
- Queue sync when online',
'Story', 'In Progress', 'High', 'Jessica Martinez', 'Mobile Team', '2024-01-20', '2024-02-12', NULL, 13, ARRAY['mobile', 'offline', 'sync'], ARRAY['mobile']),

(:'org_id', 'MOB-502', 'Add Push Notifications',
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

(:'org_id', 'MOB-503', 'Fix App Crash on Image Upload',
'App crashes when uploading images larger than 10MB on Android 12+.

Error:
android.os.TransactionTooLargeException: data parcel size 10485760 bytes

Root Cause:
Trying to pass large bitmap through Intent extras. Android has 1MB limit.

Solution: Use FileProvider and pass URI instead of bitmap data',
'Bug', 'Done', 'Critical', 'Roberto Silva', 'Mobile Team', '2024-02-03', '2024-02-04', '2024-02-04', 2, ARRAY['bug', 'mobile', 'android'], ARRAY['mobile']),

(:'org_id', 'MOB-504', 'Optimize App Startup Time',
'App takes 5+ seconds to start on mid-range devices. Need to optimize cold start time.

Issues:
- Large dependency injection graph initialization
- Loading unnecessary data on startup
- Synchronous network calls blocking UI
- Heavy image processing on main thread

Target: <2 seconds cold start',
'Story', 'To Do', 'Medium', 'Roberto Silva', 'Mobile Team', '2024-02-08', '2024-02-08', NULL, 5, ARRAY['mobile', 'performance', 'optimization'], ARRAY['mobile']),

-- INFRASTRUCTURE (INFRA) - 4 tickets
(:'org_id', 'INFRA-601', 'Migrate to Kubernetes',
'Migrate from EC2-based deployment to Kubernetes for better scalability and management.

Migration Plan:
1. Set up EKS cluster
2. Containerize all services
3. Create Kubernetes manifests
4. Set up CI/CD pipelines
5. Blue-green deployment strategy
6. Migrate production with zero downtime

Benefits:
- Auto-scaling
- Self-healing
- Rolling updates
- Resource optimization',
'Epic', 'In Progress', 'Critical', 'Chris Anderson', 'DevOps Team', '2024-01-15', '2024-02-12', NULL, 21, ARRAY['infrastructure', 'kubernetes', 'migration'], ARRAY['infrastructure']),

(:'org_id', 'INFRA-602', 'Set Up Monitoring and Logging',
'Implement comprehensive monitoring and centralized logging infrastructure.

Stack:
- Prometheus for metrics
- Grafana for dashboards
- ELK stack for logs
- Jaeger for distributed tracing
- PagerDuty for alerts

Dashboards:
- Service health
- Resource utilization
- Application metrics
- Business KPIs',
'Story', 'Done', 'High', 'Chris Anderson', 'DevOps Team', '2024-01-20', '2024-02-05', '2024-02-05', 8, ARRAY['infrastructure', 'monitoring', 'observability'], ARRAY['infrastructure']),

(:'org_id', 'INFRA-603', 'Implement Blue-Green Deployment',
'Set up blue-green deployment strategy for zero-downtime releases.

Requirements:
- Automated deployment pipeline
- Traffic switching mechanism
- Rollback capability
- Smoke tests before traffic switch
- Database migration handling',
'Story', 'Done', 'High', 'Chris Anderson', 'DevOps Team', '2024-02-01', '2024-02-08', '2024-02-08', 5, ARRAY['infrastructure', 'deployment', 'cicd'], ARRAY['infrastructure']),

(:'org_id', 'INFRA-604', 'Optimize AWS Costs',
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
-- COMMITS - Comprehensive Dataset (45 commits)
-- ============================================================

INSERT INTO commits (repository_id, organization_id, sha, message, author_name, author_email, commit_date, additions, deletions, ticket_references, metadata) VALUES

-- AUTH-101 commits (OAuth2 implementation)
('11111111-1111-1111-1111-111111111111', :'org_id', 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'feat(auth): implement OAuth2 authorization flow

- Add OAuth2 provider configuration for Google and GitHub
- Implement authorization code flow
- Add token exchange endpoints
- Store encrypted tokens in database
- Add refresh token mechanism

Breaking change: New /oauth2/authorize endpoint replaces /login',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-01-12 10:30:00', 1245, 230, ARRAY['AUTH-101'],
'{"pr_number": 101, "review_comments": 8, "files": ["api/auth/oauth.py", "api/auth/providers.py", "api/models/token.py"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(auth): add RBAC system with role hierarchy

- Implement role-based access control
- Define roles: admin, developer, viewer
- Add permission checking middleware
- Create role assignment API endpoints

Implements AUTH-101 RBAC requirements',
'Mike Chen', 'mike.chen@acmecorp.com', '2024-01-18 14:15:00', 890, 45, ARRAY['AUTH-101'],
'{"pr_number": 101, "review_comments": 5, "files": ["api/auth/rbac.py", "api/middleware/permissions.py", "api/models/role.py"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(auth): add JWT token management service

- Implement JWT signing and verification
- Add token refresh endpoint
- Implement token rotation for security
- Add rate limiting for token endpoints

Related to AUTH-101',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-01-22 09:45:00', 567, 23, ARRAY['AUTH-101'],
'{"pr_number": 101, "review_comments": 3, "files": ["api/auth/jwt.py", "api/auth/tokens.py"]}'),

('22222222-2222-2222-2222-222222222222', :'org_id', 'd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(auth): add OAuth2 login UI components

- Create OAuth provider buttons (Google, GitHub)
- Add OAuth callback handler page
- Implement token storage in secure cookies
- Add loading states and error handling

Frontend for AUTH-101',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-01-24 11:20:00', 423, 12, ARRAY['AUTH-101'],
'{"pr_number": 102, "review_comments": 4, "files": ["src/components/Auth/OAuthButton.tsx", "src/pages/OAuthCallback.tsx"]}'),

-- AUTH-102 commits (MFA implementation)
('11111111-1111-1111-1111-111111111111', :'org_id', 'e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'feat(auth): implement TOTP-based MFA

- Add TOTP generation and verification
- Create MFA enrollment endpoints
- Generate QR codes for authenticator apps
- Add backup codes generation

Implements AUTH-102',
'Mike Chen', 'mike.chen@acmecorp.com', '2024-02-05 10:00:00', 756, 18, ARRAY['AUTH-102'],
'{"pr_number": 115, "review_comments": 6, "files": ["api/auth/mfa.py", "api/auth/totp.py", "api/models/mfa.py"]}'),

('22222222-2222-2222-2222-222222222222', :'org_id', 'f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'feat(auth): add MFA enrollment UI

- Create MFA setup wizard
- Display QR code for TOTP
- Add manual entry option
- Show backup codes UI
- Add MFA verification screen

Part of AUTH-102',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-02-08 15:30:00', 512, 25, ARRAY['AUTH-102'],
'{"pr_number": 118, "review_comments": 5, "files": ["src/components/Auth/MFASetup.tsx", "src/pages/MFAEnroll.tsx"]}'),

-- AUTH-104 commits (JWT bug fix)
('11111111-1111-1111-1111-111111111111', :'org_id', 'g1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'fix(auth): correct JWT expiration time calculation

The JWT tokens were expiring after 45 minutes instead of 8 hours
due to incorrect time unit conversion. Changed from seconds to hours.

Before: exp = now + timedelta(seconds=28800)
After: exp = now + timedelta(hours=8)

Fixes AUTH-104',
'Mike Chen', 'mike.chen@acmecorp.com', '2024-01-19 08:30:00', 15, 8, ARRAY['AUTH-104'],
'{"pr_number": 105, "review_comments": 1, "files": ["api/auth/jwt.py"]}'),

-- AUTH-105 commits (Password strength)
('11111111-1111-1111-1111-111111111111', :'org_id', 'h2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(auth): add password strength validation

- Implement zxcvbn password strength checker
- Check against common password lists
- Enforce minimum complexity requirements
- Add password validation API endpoint

Implements AUTH-105',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-01-26 11:15:00', 234, 12, ARRAY['AUTH-105'],
'{"pr_number": 108, "review_comments": 3, "files": ["api/auth/password.py", "api/validators/password.py"]}'),

('22222222-2222-2222-2222-222222222222', :'org_id', 'i3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(auth): add password strength meter UI

- Real-time password strength visualization
- Color-coded strength indicator
- Show strength score and feedback
- Display requirement checklist

Frontend for AUTH-105',
'Alex Rivera', 'alex.rivera@acmecorp.com', '2024-01-27 14:45:00', 178, 6, ARRAY['AUTH-105'],
'{"pr_number": 109, "review_comments": 2, "files": ["src/components/Auth/PasswordStrengthMeter.tsx"]}'),

-- AUTH-106 commits (API key management)
('11111111-1111-1111-1111-111111111111', :'org_id', 'j4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(auth): implement API key generation and management

- Add API key model and database table
- Implement key generation with crypto.randomBytes
- Add CRUD endpoints for API keys
- Add API key authentication middleware

Part of AUTH-106',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-02-09 10:30:00', 645, 15, ARRAY['AUTH-106'],
'{"pr_number": 120, "review_comments": 7, "files": ["api/models/api_key.py", "api/routes/api_keys.py", "api/middleware/api_key_auth.py"]}'),

-- DB-201 commits (PostgreSQL migration)
('11111111-1111-1111-1111-111111111111', :'org_id', 'k5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'feat(db): add PostgreSQL schema migration scripts

- Create Alembic migration setup
- Add initial schema migration
- Convert MySQL-specific queries to PostgreSQL
- Update ORM models for PostgreSQL

Part of DB-201 migration',
'David Park', 'david.park@acmecorp.com', '2024-01-08 09:00:00', 1567, 892, ARRAY['DB-201'],
'{"pr_number": 95, "review_comments": 12, "files": ["alembic/versions/001_initial.py", "api/models/*.py", "api/database.py"]}'),

('44444444-4444-4444-4444-444444444444', :'org_id', 'l6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'feat(infra): add PostgreSQL RDS configuration

- Create PostgreSQL RDS instance with Terraform
- Configure multi-AZ deployment
- Set up read replicas
- Configure automated backups

Infrastructure for DB-201',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-01-10 11:30:00', 456, 123, ARRAY['DB-201'],
'{"pr_number": 96, "review_comments": 5, "files": ["terraform/rds.tf", "terraform/rds-replica.tf", "terraform/backup.tf"]}'),

-- DB-202 commits (Connection pooling)
('11111111-1111-1111-1111-111111111111', :'org_id', 'm1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'feat(db): implement connection pooling with PgBouncer

- Add PgBouncer configuration
- Configure pool size based on load tests (pool_size=20)
- Add connection retry logic
- Implement health checks for connections

Implements DB-202',
'David Park', 'david.park@acmecorp.com', '2024-01-20 10:15:00', 345, 45, ARRAY['DB-202'],
'{"pr_number": 106, "review_comments": 4, "files": ["config/pgbouncer.ini", "api/database.py", "api/health.py"]}'),

-- DB-203 commits (Query optimization)
('11111111-1111-1111-1111-111111111111', :'org_id', 'n2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'perf(db): add indexes for slow user search queries

- Add GIN index on user email with trigram support
- Add composite index on (organization_id, created_at)
- Add index on user status for filtering
- Query time reduced from 5.2s to 0.3s

Addresses DB-203',
'David Park', 'david.park@acmecorp.com', '2024-02-06 14:20:00', 45, 8, ARRAY['DB-203'],
'{"pr_number": 117, "review_comments": 2, "files": ["alembic/versions/015_add_indexes.py"]}'),

-- UI-301 commits (Dashboard redesign)
('22222222-2222-2222-2222-222222222222', :'org_id', 'o3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(ui): implement new dashboard layout

- Create responsive grid layout
- Add customizable widget system
- Implement drag-and-drop for widgets
- Add dashboard persistence
- Improve mobile experience

Major redesign for UI-301',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-01-25 11:00:00', 1234, 567, ARRAY['UI-301'],
'{"pr_number": 107, "review_comments": 15, "files": ["src/pages/Dashboard.tsx", "src/components/Dashboard/*.tsx", "src/hooks/useDashboard.ts"]}'),

('22222222-2222-2222-2222-222222222222', :'org_id', 'p4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(ui): add dark mode support to dashboard

- Implement theme context
- Create dark mode color palette
- Add theme toggle component
- Persist theme preference

Part of UI-301',
'Alex Rivera', 'alex.rivera@acmecorp.com', '2024-02-01 15:45:00', 789, 123, ARRAY['UI-301'],
'{"pr_number": 113, "review_comments": 6, "files": ["src/context/ThemeContext.tsx", "src/styles/darkTheme.ts"]}'),

-- UI-302 commits (Responsive navigation)
('22222222-2222-2222-2222-222222222222', :'org_id', 'q5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'feat(ui): implement responsive navigation menu

- Create collapsible sidebar
- Add hamburger menu for mobile
- Implement keyboard navigation
- Add breadcrumb component
- Add search in navigation

Implements UI-302',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-01-28 10:30:00', 1012, 345, ARRAY['UI-302'],
'{"pr_number": 110, "review_comments": 8, "files": ["src/components/Navigation/*.tsx", "src/components/Breadcrumbs.tsx"]}'),

-- UI-303 commits (Dark mode)
('22222222-2222-2222-2222-222222222222', :'org_id', 'r6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'feat(ui): implement system-wide dark mode

- Add theme provider to root component
- Create light/dark/system theme options
- Add smooth theme transitions
- Ensure WCAG 2.1 contrast compliance

Part of UI-303',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-02-07 11:15:00', 1456, 234, ARRAY['UI-303'],
'{"pr_number": 119, "review_comments": 9, "files": ["src/App.tsx", "src/styles/*.ts", "src/components/ThemeToggle.tsx"]}'),

-- UI-304 commits (Chart performance fix)
('22222222-2222-2222-2222-222222222222', :'org_id', 's1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'fix(ui): optimize chart rendering for large datasets

- Implement data sampling for datasets >10k points
- Switch from SVG to Canvas rendering
- Add virtualization for chart legends
- Debounce zoom/pan operations (300ms)

Fixes UI-304 performance issue',
'Alex Rivera', 'alex.rivera@acmecorp.com', '2024-01-27 09:30:00', 234, 178, ARRAY['UI-304'],
'{"pr_number": 109, "review_comments": 4, "files": ["src/components/Charts/LineChart.tsx", "src/utils/dataSampling.ts"]}'),

-- UI-305 commits (Form validation)
('22222222-2222-2222-2222-222222222222', :'org_id', 't2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(ui): create reusable form validation framework

- Implement React Hook Form integration
- Create custom validation rules
- Add async validation support
- Create error message components
- Add form state management

Implements UI-305',
'Alex Rivera', 'alex.rivera@acmecorp.com', '2024-02-01 14:00:00', 1123, 89, ARRAY['UI-305'],
'{"pr_number": 114, "review_comments": 11, "files": ["src/hooks/useForm.ts", "src/components/Form/*.tsx", "src/validators/*.ts"]}'),

-- API-401 commits (API v2 design)
('11111111-1111-1111-1111-111111111111', :'org_id', 'u3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(api): implement API v2 with improved design

- Create versioned API routing (v1, v2)
- Standardize resource naming conventions
- Implement HATEOAS links
- Add standardized pagination
- Improve error response format

Major API redesign for API-401',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-03 10:00:00', 2134, 456, ARRAY['API-401'],
'{"pr_number": 116, "review_comments": 18, "files": ["api/v2/*.py", "api/pagination.py", "api/errors.py"]}'),

-- API-402 commits (GraphQL)
('11111111-1111-1111-1111-111111111111', :'org_id', 'v4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(api): add GraphQL endpoint with Apollo Server

- Set up Apollo Server
- Define GraphQL schema
- Implement resolvers for main entities
- Add DataLoader for N+1 prevention
- Add GraphQL playground

Implements API-402',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-05 11:30:00', 1567, 23, ARRAY['API-402'],
'{"pr_number": 117, "review_comments": 12, "files": ["api/graphql/*.py", "api/schema.graphql", "api/resolvers/*.py"]}'),

-- API-403 commits (Rate limiting)
('11111111-1111-1111-1111-111111111111', :'org_id', 'w5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'feat(api): implement rate limiting with Redis

- Add token bucket rate limiter
- Configure per-user and per-IP limits
- Add rate limit headers to responses
- Implement distributed rate limiting with Redis
- Add rate limit bypass for admin users

Implements API-403',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-01-24 09:15:00', 567, 34, ARRAY['API-403'],
'{"pr_number": 107, "review_comments": 6, "files": ["api/middleware/rate_limit.py", "api/rate_limiter.py"]}'),

-- API-404 commits (Bug fix)
('11111111-1111-1111-1111-111111111111', :'org_id', 'x6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'fix(api): resolve race condition in user profile update

Added SELECT FOR UPDATE to prevent concurrent updates from
violating unique constraints. Also added optimistic locking
with version field.

Fixes API-404 critical bug',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-02 08:45:00', 45, 23, ARRAY['API-404'],
'{"pr_number": 115, "review_comments": 2, "files": ["api/routes/users.py", "api/models/user.py"]}'),

-- API-405 commits (API documentation)
('11111111-1111-1111-1111-111111111111', :'org_id', 'y1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'feat(api): add OpenAPI 3.0 documentation

- Generate OpenAPI spec from FastAPI
- Add Swagger UI at /docs
- Add ReDoc at /redoc
- Include authentication documentation
- Add code examples for all endpoints

Part of API-405',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-10 10:00:00', 890, 45, ARRAY['API-405'],
'{"pr_number": 121, "review_comments": 5, "files": ["api/docs/*.py", "api/openapi.py"]}'),

-- MOB-501 commits (Offline mode)
('33333333-3333-3333-3333-333333333333', :'org_id', 'z2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(mobile): implement offline data storage with Room

- Add Room database for local caching
- Implement sync manager
- Add conflict resolution strategy
- Queue failed requests
- Add offline indicators

Part of MOB-501',
'Jessica Martinez', 'jessica.martinez@acmecorp.com', '2024-02-05 11:00:00', 1234, 67, ARRAY['MOB-501'],
'{"pr_number": 116, "review_comments": 10, "files": ["app/src/main/java/com/acme/data/local/*.kt", "app/src/main/java/com/acme/sync/*.kt"]}'),

-- MOB-502 commits (Push notifications)
('33333333-3333-3333-3333-333333333333', :'org_id', 'a3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(mobile): add FCM push notification support

- Integrate Firebase Cloud Messaging
- Handle notification permissions
- Implement notification handlers
- Add rich notifications
- Add notification preferences

Implements MOB-502',
'Jessica Martinez', 'jessica.martinez@acmecorp.com', '2024-02-08 14:30:00', 789, 34, ARRAY['MOB-502'],
'{"pr_number": 118, "review_comments": 7, "files": ["app/src/main/java/com/acme/notifications/*.kt", "app/google-services.json"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'b4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(api): add push notification service

- Implement FCM server-side integration
- Create notification templates
- Add notification scheduling
- Implement user preference handling
- Add notification analytics

Backend for MOB-502',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-09 15:00:00', 678, 23, ARRAY['MOB-502'],
'{"pr_number": 119, "review_comments": 5, "files": ["api/services/notifications.py", "api/routes/notifications.py"]}'),

-- MOB-503 commits (Image upload bug fix)
('33333333-3333-3333-3333-333333333333', :'org_id', 'c5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'fix(mobile): use FileProvider for large image uploads

Changed image upload to use FileProvider and URI passing
instead of passing bitmap data through Intent extras.
This fixes TransactionTooLargeException on Android 12+.

Fixes MOB-503',
'Roberto Silva', 'roberto.silva@acmecorp.com', '2024-02-04 09:15:00', 89, 67, ARRAY['MOB-503'],
'{"pr_number": 115, "review_comments": 2, "files": ["app/src/main/java/com/acme/upload/ImageUploader.kt"]}'),

-- INFRA-601 commits (Kubernetes migration)
('44444444-4444-4444-4444-444444444444', :'org_id', 'd6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'feat(infra): create Kubernetes manifests for all services

- Create Deployment manifests
- Add Service definitions
- Configure Ingress rules
- Add ConfigMaps and Secrets
- Set up resource limits

Part of INFRA-601',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-03 10:30:00', 1890, 234, ARRAY['INFRA-601'],
'{"pr_number": 114, "review_comments": 14, "files": ["k8s/deployments/*.yaml", "k8s/services/*.yaml", "k8s/ingress.yaml"]}'),

('44444444-4444-4444-4444-444444444444', :'org_id', 'e1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'feat(infra): set up EKS cluster with Terraform

- Create EKS cluster configuration
- Configure node groups
- Set up cluster autoscaling
- Add IAM roles and policies
- Configure VPC and networking

Infrastructure for INFRA-601',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-06 11:45:00', 1123, 345, ARRAY['INFRA-601'],
'{"pr_number": 117, "review_comments": 9, "files": ["terraform/eks.tf", "terraform/eks-nodes.tf", "terraform/iam.tf", "terraform/vpc.tf"]}'),

-- INFRA-602 commits (Monitoring)
('44444444-4444-4444-4444-444444444444', :'org_id', 'f2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat(infra): set up Prometheus and Grafana

- Deploy Prometheus with Helm
- Configure service discovery
- Create Grafana dashboards
- Set up alerting rules
- Add PagerDuty integration

Implements INFRA-602',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-02 10:00:00', 1456, 123, ARRAY['INFRA-602'],
'{"pr_number": 113, "review_comments": 8, "files": ["k8s/monitoring/*.yaml", "grafana/dashboards/*.json", "prometheus/alerts/*.yaml"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'g3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'feat(observability): add Prometheus metrics to API

- Add counter for request count
- Add histogram for response times
- Add gauge for active connections
- Add custom business metrics
- Export metrics at /metrics endpoint

Instrumentation for INFRA-602',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-03 14:20:00', 456, 23, ARRAY['INFRA-602'],
'{"pr_number": 114, "review_comments": 4, "files": ["api/metrics.py", "api/middleware/metrics.py"]}'),

-- INFRA-603 commits (Blue-green deployment)
('44444444-4444-4444-4444-444444444444', :'org_id', 'h4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'feat(infra): implement blue-green deployment pipeline

- Create deployment pipeline with GitLab CI
- Add smoke tests before traffic switch
- Implement automatic rollback on failure
- Add manual approval gate
- Configure traffic switching

Implements INFRA-603',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-07 09:30:00', 890, 67, ARRAY['INFRA-603'],
'{"pr_number": 118, "review_comments": 7, "files": [".gitlab-ci.yml", "scripts/deploy.sh", "scripts/smoke-tests.sh"]}'),

-- Commits without ticket references (for gap detection testing)
('11111111-1111-1111-1111-111111111111', :'org_id', 'i5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'refactor: improve error handling in API middleware

Refactored error handling to be more consistent across all
endpoints. Added custom exception classes and improved
error messages for better debugging.',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-11 10:15:00', 234, 123, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["api/middleware/errors.py", "api/exceptions.py"]}'),

('22222222-2222-2222-2222-222222222222', :'org_id', 'j6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'chore: update npm dependencies to latest versions

Updated all npm packages to their latest stable versions.
Fixed breaking changes in React 18 migration.',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-02-12 11:30:00', 45, 38, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["package.json", "package-lock.json"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'k1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
'perf: optimize database query performance

Added strategic indexes and optimized slow queries.
Reduced average response time from 800ms to 200ms.',
'David Park', 'david.park@acmecorp.com', '2024-02-13 14:45:00', 123, 56, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["alembic/versions/020_optimize.py"]}'),

('33333333-3333-3333-3333-333333333333', :'org_id', 'l2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3',
'feat: add biometric authentication support

Added fingerprint and face recognition support for
faster and more secure login experience.',
'Jessica Martinez', 'jessica.martinez@acmecorp.com', '2024-02-14 15:00:00', 567, 23, ARRAY[]::text[],
'{"pr_number": 122, "review_comments": 6, "files": ["app/src/main/java/com/acme/auth/Biometric.kt"]}'),

('22222222-2222-2222-2222-222222222222', :'org_id', 'm3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4',
'style: update component styling and layout

Improved visual consistency across components.
Updated color palette and spacing.',
'Emily Zhang', 'emily.zhang@acmecorp.com', '2024-02-15 09:30:00', 189, 145, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["src/styles/*.css"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'n4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5',
'docs: update API documentation

Updated API documentation with new endpoints and examples.
Added troubleshooting section.',
'Michael Torres', 'michael.torres@acmecorp.com', '2024-02-16 11:00:00', 345, 67, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["docs/api/*.md"]}'),

('44444444-4444-4444-4444-444444444444', :'org_id', 'o5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6',
'fix: correct S3 bucket permissions

Fixed S3 bucket policy to prevent public access while
allowing necessary application access.',
'Chris Anderson', 'chris.anderson@acmecorp.com', '2024-02-17 10:30:00', 78, 34, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["terraform/s3.tf"]}'),

('11111111-1111-1111-1111-111111111111', :'org_id', 'p6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1',
'test: add integration tests for payment flow

Added comprehensive integration tests for payment
processing flow including edge cases.',
'Sarah Johnson', 'sarah.johnson@acmecorp.com', '2024-02-18 14:15:00', 456, 12, ARRAY[]::text[],
'{"pr_number": null, "review_comments": 0, "files": ["tests/integration/test_payment.py"]}');

COMMIT;

-- Show summary
\echo '\n==========================================';
\echo 'DATA SEED SUMMARY';
\echo '==========================================\n';

SELECT 'Repositories' as entity, COUNT(*) as count FROM repositories WHERE organization_id = :'org_id'
UNION ALL
SELECT 'Jira Tickets', COUNT(*) FROM jira_tickets WHERE organization_id = :'org_id'
UNION ALL
SELECT 'Commits', COUNT(*) FROM commits WHERE organization_id = :'org_id'
UNION ALL
SELECT 'Commits with Tickets', COUNT(*) FROM commits WHERE organization_id = :'org_id' AND array_length(ticket_references, 1) > 0
UNION ALL
SELECT 'Commits without Tickets', COUNT(*) FROM commits WHERE organization_id = :'org_id' AND (ticket_references IS NULL OR array_length(ticket_references, 1) = 0);

\echo '\nTickets by Status:\n';
SELECT status, COUNT(*) as count FROM jira_tickets WHERE organization_id = :'org_id' GROUP BY status ORDER BY count DESC;

\echo '\nCommits by Repository:\n';
SELECT r.repo_name, COUNT(c.id) as commit_count
FROM repositories r
LEFT JOIN commits c ON c.repository_id = r.id
WHERE r.organization_id = :'org_id'
GROUP BY r.repo_name
ORDER BY commit_count DESC;
