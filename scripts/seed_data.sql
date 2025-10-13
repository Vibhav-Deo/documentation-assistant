-- Seed realistic dummy data for testing
-- Organization: Acme Corp

-- Get organization ID (should exist from initial setup)
\set org_id '19cf9fd1-71b0-4401-a325-a971d19b79e7'

-- Insert Jira Tickets
INSERT INTO jira_tickets (organization_id, ticket_key, summary, description, issue_type, status, priority, assignee, reporter, created, updated, resolved, labels, components, url, metadata) VALUES
(:org_id, 'AUTH-101', 'Implement OAuth2 authentication for API', 'We need to add OAuth2 authentication to secure our REST API. This will replace the current basic auth mechanism.

Acceptance Criteria:
- Support OAuth2 authorization code flow
- Implement token refresh mechanism
- Add role-based access control (RBAC)
- Update API documentation

Related: See confluence page on authentication strategy', 'Story', 'Done', 'High', 'Sarah Johnson', 'Mike Chen', NOW() - INTERVAL '50 days', NOW() - INTERVAL '45 days', NOW() - INTERVAL '40 days', ARRAY['security', 'api', 'authentication'], ARRAY['Backend', 'API'], 'https://acmecorp.atlassian.net/browse/AUTH-101', '{}'),

(:org_id, 'AUTH-102', 'Add JWT token validation middleware', 'Create middleware to validate JWT tokens on all protected API endpoints.

Technical Details:
- Validate token signature
- Check expiration
- Extract user claims
- Handle token refresh

Commit: abc123def456', 'Task', 'Done', 'High', 'Sarah Johnson', 'Sarah Johnson', NOW() - INTERVAL '45 days', NOW() - INTERVAL '40 days', NOW() - INTERVAL '38 days', ARRAY['security', 'backend'], ARRAY['Backend'], 'https://acmecorp.atlassian.net/browse/AUTH-102', '{}'),

(:org_id, 'DB-201', 'Migrate from MongoDB to PostgreSQL', 'Migrate our user data from MongoDB to PostgreSQL for better relational data support and ACID compliance.

Phases:
1. Schema design in PostgreSQL
2. Create migration scripts
3. Test data integrity
4. Cutover plan
5. Rollback strategy

Impact: This will affect AUTH-101 and USER-301', 'Epic', 'In Progress', 'Critical', 'David Park', 'Mike Chen', NOW() - INTERVAL '40 days', NOW() - INTERVAL '5 days', NULL, ARRAY['database', 'migration', 'infrastructure'], ARRAY['Database', 'Backend'], 'https://acmecorp.atlassian.net/browse/DB-201', '{}'),

(:org_id, 'DB-202', 'Optimize database queries for user profile page', 'User profile page is taking 3+ seconds to load. Need to optimize queries.

Investigation findings:
- Missing index on user_id in sessions table
- N+1 query problem in user_preferences
- Redundant JOIN on inactive_users table

PR #45 has the fixes', 'Bug', 'Done', 'High', 'David Park', 'Sarah Johnson', NOW() - INTERVAL '35 days', NOW() - INTERVAL '28 days', NOW() - INTERVAL '25 days', ARRAY['performance', 'database'], ARRAY['Database', 'Backend'], 'https://acmecorp.atlassian.net/browse/DB-202', '{}'),

(:org_id, 'UI-301', 'Redesign dashboard with new component library', 'Replace legacy dashboard components with Material-UI v5.

Scope:
- Update all chart components
- Implement responsive grid layout
- Add dark mode support
- Improve accessibility (WCAG 2.1 AA)

Design: See Figma mockups in Confluence', 'Story', 'In Progress', 'Medium', 'Emma Wilson', 'Mike Chen', NOW() - INTERVAL '30 days', NOW() - INTERVAL '10 days', NULL, ARRAY['frontend', 'ui', 'dashboard'], ARRAY['Frontend'], 'https://acmecorp.atlassian.net/browse/UI-301', '{}'),

(:org_id, 'UI-302', 'Fix broken table sorting on mobile devices', 'Table sorting doesn''t work on mobile screens < 768px.

Steps to reproduce:
1. Open dashboard on mobile
2. Try to sort any table column
3. Nothing happens

Expected: Table should sort
Actual: Click doesn''t register

Commit: ghi789jkl012', 'Bug', 'Done', 'Medium', 'Emma Wilson', 'Sarah Johnson', NOW() - INTERVAL '25 days', NOW() - INTERVAL '20 days', NOW() - INTERVAL '18 days', ARRAY['frontend', 'mobile', 'bug'], ARRAY['Frontend'], 'https://acmecorp.atlassian.net/browse/UI-302', '{}'),

(:org_id, 'API-401', 'Add rate limiting to public API endpoints', 'Implement rate limiting to prevent API abuse.

Requirements:
- 100 requests per minute for authenticated users
- 10 requests per minute for anonymous users
- Return proper HTTP 429 status
- Add X-RateLimit headers

See: Related to AUTH-101', 'Task', 'To Do', 'High', 'Sarah Johnson', 'Mike Chen', NOW() - INTERVAL '20 days', NOW() - INTERVAL '15 days', NULL, ARRAY['api', 'security', 'infrastructure'], ARRAY['Backend', 'API'], 'https://acmecorp.atlassian.net/browse/API-401', '{}'),

(:org_id, 'API-402', 'GraphQL API endpoint for complex queries', 'Add GraphQL endpoint alongside REST API for complex data fetching needs.

Benefits:
- Reduce over-fetching
- Better mobile performance
- Type safety with schema

PR #52 has initial implementation', 'Story', 'In Review', 'Medium', 'David Park', 'Emma Wilson', NOW() - INTERVAL '15 days', NOW() - INTERVAL '8 days', NULL, ARRAY['api', 'graphql', 'enhancement'], ARRAY['Backend', 'API'], 'https://acmecorp.atlassian.net/browse/API-402', '{}');

-- Insert Repository
INSERT INTO repositories (organization_id, repo_name, repo_url, provider, branch, file_count, last_synced, created_at) VALUES
(:org_id, 'acme-backend', 'https://github.com/acmecorp/backend', 'github', 'main', 3, NOW(), NOW());

-- Get repository ID
\set repo_id (SELECT id FROM repositories WHERE organization_id = :org_id LIMIT 1)

-- Insert Commits
INSERT INTO commits (organization_id, repository_id, sha, message, author_name, author_email, commit_date, files_changed, url, metadata) VALUES
(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 'abc123def456', 'feat(auth): implement JWT token validation middleware

Added middleware to validate JWT tokens:
- Verify token signature using RS256
- Check expiration timestamp
- Extract user claims (id, email, role)
- Handle token refresh logic

Closes AUTH-102', 'Sarah Johnson', 'sarah.johnson@acmecorp.com', NOW() - INTERVAL '38 days', ARRAY['src/middleware/auth.ts', 'src/utils/jwt.ts', 'tests/auth.test.ts'], 'https://github.com/acmecorp/backend/commit/abc123def456', '{}'),

(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 'def456ghi789', 'refactor(db): add database indexes for performance

Added indexes:
- user_id on sessions table
- email on users table (unique)
- created_at on audit_logs table

Query performance improved by 80%

Resolves DB-202', 'David Park', 'david.park@acmecorp.com', NOW() - INTERVAL '25 days', ARRAY['migrations/008_add_indexes.sql', 'docs/database_schema.md'], 'https://github.com/acmecorp/backend/commit/def456ghi789', '{}'),

(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 'ghi789jkl012', 'fix(ui): fix table sorting on mobile devices

Issue: Click events weren''t registering on mobile

Solution:
- Increased touch target size to 44x44px
- Added proper event listeners for touch events
- Tested on iOS Safari and Chrome Mobile

Fixes UI-302', 'Emma Wilson', 'emma.wilson@acmecorp.com', NOW() - INTERVAL '18 days', ARRAY['src/components/Table/SortableHeader.tsx', 'src/components/Table/Table.css'], 'https://github.com/acmecorp/backend/commit/ghi789jkl012', '{}'),

(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 'jkl012mno345', 'feat(api): add OAuth2 authorization endpoints

Implemented OAuth2 endpoints:
- POST /oauth/authorize
- POST /oauth/token
- POST /oauth/refresh
- GET /oauth/userinfo

Supports authorization code flow

Part of AUTH-101', 'Sarah Johnson', 'sarah.johnson@acmecorp.com', NOW() - INTERVAL '42 days', ARRAY['src/routes/oauth.ts', 'src/controllers/oauth_controller.ts', 'src/services/oauth_service.ts'], 'https://github.com/acmecorp/backend/commit/jkl012mno345', '{}');

-- Insert Pull Requests
INSERT INTO pull_requests (organization_id, repository_id, pr_number, title, description, author_name, state, created_at, merged_at, commit_shas, url, metadata) VALUES
(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 45, 'Optimize database queries for user profile', '## Problem
User profile page loading was taking 3+ seconds due to inefficient queries.

## Solution
- Added index on `user_id` in sessions table
- Fixed N+1 query in user_preferences loading
- Removed redundant JOIN on inactive_users

## Performance Impact
- Page load time: 3.2s → 0.4s (87.5% improvement)
- Database query count: 47 → 5 queries

Closes DB-202', 'David Park', 'merged', NOW() - INTERVAL '26 days', NOW() - INTERVAL '25 days', ARRAY['def456ghi789'], 'https://github.com/acmecorp/backend/pull/45', '{}'),

(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 52, 'Add GraphQL API endpoint', '## Summary
Adds GraphQL endpoint at `/graphql` alongside existing REST API.

## Features
- Type-safe schema with TypeScript
- Resolvers for User, Post, Comment entities
- DataLoader for N+1 prevention
- Query complexity limiting

Related to API-402', 'David Park', 'open', NOW() - INTERVAL '8 days', NULL, ARRAY[], 'https://github.com/acmecorp/backend/pull/52', '{}');

-- Insert Code Files
INSERT INTO code_files (organization_id, repository_id, file_path, file_name, file_type, language, content, functions, classes, line_count, url, metadata) VALUES
(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 'src/middleware/auth.ts', 'auth.ts', 'ts', 'typescript',
'import { Request, Response, NextFunction } from ''express'';
import jwt from ''jsonwebtoken'';
import { User } from ''../models/User'';

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
  const authHeader = req.headers[''authorization''];
  const token = authHeader && authHeader.split('' '')[1];

  if (!token) {
    return res.status(401).json({ error: ''No token provided'' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload;
    const user = await User.findById(decoded.userId);

    if (!user) {
      return res.status(403).json({ error: ''Invalid token'' });
    }

    req.user = user;
    next();
  } catch (error) {
    return res.status(403).json({ error: ''Invalid or expired token'' });
  }
};',
ARRAY['authenticateToken'], ARRAY[], 35, 'https://github.com/acmecorp/backend/blob/main/src/middleware/auth.ts', '{}'),

(:org_id, (SELECT id FROM repositories WHERE repo_name = 'acme-backend'), 'src/components/Table/SortableHeader.tsx', 'SortableHeader.tsx', 'tsx', 'typescript',
'import React from ''react'';
import { TableCell, TableSortLabel } from ''@mui/material'';

interface SortableHeaderProps {
  column: string;
  label: string;
  sortBy: string;
  sortOrder: ''asc'' | ''desc'';
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
        minWidth: ''44px'',
        minHeight: ''44px'',
        cursor: ''pointer'',
      }}
      onClick={handleSort}
      onTouchEnd={(e) => {
        e.preventDefault();
        handleSort();
      }}
    >
      <TableSortLabel
        active={sortBy === column}
        direction={sortBy === column ? sortOrder : ''asc''}
      >
        {label}
      </TableSortLabel>
    </TableCell>
  );
};',
ARRAY['SortableHeader', 'handleSort'], ARRAY[], 43, 'https://github.com/acmecorp/backend/blob/main/src/components/Table/SortableHeader.tsx', '{}');

SELECT '✅ Database seeded with realistic dummy data!' AS status;
SELECT COUNT(*) || ' Jira tickets' AS jira FROM jira_tickets WHERE organization_id = :org_id;
SELECT COUNT(*) || ' commits' AS commits FROM commits WHERE organization_id = :org_id;
SELECT COUNT(*) || ' pull requests' AS prs FROM pull_requests WHERE organization_id = :org_id;
SELECT COUNT(*) || ' code files' AS files FROM code_files WHERE organization_id = :org_id;
