-- Migration: Add decisions table for IntentAnalyzer
-- Purpose: Store extracted decision rationale from tickets, commits, PRs, docs

CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Core decision data
    decision_id VARCHAR(255) NOT NULL,  -- e.g., "decision_DEMO-001"
    ticket_key VARCHAR(50),             -- Link to Jira ticket
    decision_summary TEXT NOT NULL,      -- Brief summary of decision

    -- Decision analysis
    problem_statement TEXT,              -- What problem was being solved
    alternatives_considered JSONB,       -- Array of alternatives evaluated
    chosen_approach TEXT,                -- Which approach was chosen
    rationale TEXT,                      -- Why this approach was chosen
    constraints JSONB,                   -- Array of constraints
    risks JSONB,                         -- Array of {risk, mitigation}
    tradeoffs TEXT,                      -- What was gained vs sacrificed

    -- Context and relationships
    stakeholders JSONB,                  -- Array of people involved
    implementation_commits JSONB,        -- Array of commit SHAs
    related_prs JSONB,                   -- Array of PR numbers
    related_docs JSONB,                  -- Array of doc titles/IDs

    -- Metadata
    raw_analysis TEXT,                   -- Full AI analysis for reference
    confidence_score FLOAT,              -- How confident is the analysis (0-1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(organization_id, decision_id)
);

-- Indexes for performance
CREATE INDEX idx_decisions_org_id ON decisions(organization_id);
CREATE INDEX idx_decisions_ticket_key ON decisions(ticket_key);
CREATE INDEX idx_decisions_created_at ON decisions(created_at DESC);

-- Full-text search on decision content
CREATE INDEX idx_decisions_summary_fts ON decisions USING GIN(to_tsvector('english', decision_summary));
CREATE INDEX idx_decisions_problem_fts ON decisions USING GIN(to_tsvector('english', problem_statement));
CREATE INDEX idx_decisions_chosen_fts ON decisions USING GIN(to_tsvector('english', chosen_approach));

-- JSONB indexes for array searches
CREATE INDEX idx_decisions_stakeholders ON decisions USING GIN(stakeholders);
CREATE INDEX idx_decisions_commits ON decisions USING GIN(implementation_commits);

COMMENT ON TABLE decisions IS 'Stores extracted decision rationale from multi-source analysis (IntentAnalyzer)';
COMMENT ON COLUMN decisions.decision_id IS 'Unique identifier like decision_DEMO-001';
COMMENT ON COLUMN decisions.alternatives_considered IS 'JSON array of alternative approaches that were evaluated';
COMMENT ON COLUMN decisions.constraints IS 'JSON array of constraints that influenced the decision';
COMMENT ON COLUMN decisions.risks IS 'JSON array of {risk: string, mitigation: string} objects';
COMMENT ON COLUMN decisions.confidence_score IS 'AI confidence in the analysis (0.0-1.0)';
