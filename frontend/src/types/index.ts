// User and Authentication Types
export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'user'
  created_at: string
}

export interface Organization {
  id: string
  name: string
  plan: 'free' | 'pro' | 'enterprise'
  monthly_quota: number
  used_quota: number
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
  organization: Organization
}

// Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  source_metadata?: SourceMetadata
}

export interface SourceMetadata {
  confluence_count: number
  jira_count: number
  git_count: number
  code_count: number
}

export interface ChatRequest {
  question: string
  session_id?: string | null
  model?: string
  max_results?: number
  search_type?: 'semantic' | 'hybrid' | 'keyword'
  include_confluence?: boolean
  include_jira?: boolean
  include_git?: boolean
  include_code?: boolean
}

export interface ChatResponse {
  answer: string
  sources: string[]
  session_id: string
}

// Knowledge Graph Types
export interface TicketRelationship {
  ticket_key: string
  commits: Commit[]
  pull_requests: PullRequest[]
  code_files: CodeFile[]
  developers: Developer[]
}

export interface Commit {
  commit_hash: string
  message: string
  author: string
  date: string
  files_changed?: string[]
}

export interface PullRequest {
  pr_number: number
  title: string
  state: string
  author: string
  created_at: string
  merged_at?: string
}

export interface CodeFile {
  file_path: string
  language: string
  size: number
  last_modified: string
}

export interface Developer {
  name: string
  email: string
  commits_count: number
  tickets_count: number
}

// Decision Analysis Types
export interface Decision {
  id: string
  ticket_key: string
  decision_summary: string
  rationale: string
  alternatives_considered: string[]
  technical_context: string
  business_impact: string
  created_at: string
}

// Admin Types
export interface OrganizationMetrics {
  organization: Organization
  users: User[]
  usage_stats: UsageStats
}

export interface UsageStats {
  total_requests: number
  avg_response_time: number
  error_rate: number
  user_requests: UserRequest[]
  recent_activity: ActivityData[]
}

export interface UserRequest {
  name: string
  request_count: number
}

export interface ActivityData {
  date: string
  requests: number
}

// Sync Configuration Types
export interface SyncConfig {
  source_type: 'confluence' | 'jira' | 'repository'
  [key: string]: any
}

export interface JiraSyncConfig {
  server: string
  email: string
  api_token: string
  project_key: string
}

export interface RepositorySyncConfig {
  provider: 'github' | 'gitlab' | 'bitbucket'
  repo_url: string
  access_token: string
  branch: string
}
