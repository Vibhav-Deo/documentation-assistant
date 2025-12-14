"""
Comprehensive Data Seeder for Development Environment

This service automatically seeds comprehensive data during API startup in development mode.
It replaces and enhances the existing demo data generator with data specifically designed
to test all investor demo features.

Features tested:
- Predictive Analytics (historical velocity data)
- Auto-Tagging (diverse content categories)
- Intent Analysis (complex decisions with conflicts)
- Gap Detection (orphaned commits, undocumented features)
- Impact Analysis (interconnected changes)
- Streaming Search (rich content for context)
- AI Enhancement (varied scenarios)
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import uuid
import json

logger = logging.getLogger(__name__)

class ComprehensiveDataSeeder:
    """
    Comprehensive data seeder for development environments.
    Automatically runs during API startup if ENVIRONMENT=development.
    """
    
    def __init__(self, db_service):
        self.db = db_service
        self.org_id = "529d2ca9-6fd1-4fee-9105-dbde1499f937"  # Use existing org from init_database.sql
        
        # Enhanced data templates for comprehensive testing
        self.developers = [
            {"name": "Sarah Johnson", "email": "sarah.johnson@acmecorp.com"},
            {"name": "Mike Chen", "email": "mike.chen@acmecorp.com"},
            {"name": "Emily Zhang", "email": "emily.zhang@acmecorp.com"},
            {"name": "David Park", "email": "david.park@acmecorp.com"},
            {"name": "Alex Rivera", "email": "alex.rivera@acmecorp.com"},
            {"name": "Jessica Martinez", "email": "jessica.martinez@acmecorp.com"},
            {"name": "Chris Anderson", "email": "chris.anderson@acmecorp.com"},
            {"name": "Roberto Silva", "email": "roberto.silva@acmecorp.com"},
            {"name": "Michael Torres", "email": "michael.torres@acmecorp.com"},
            {"name": "Lisa Wang", "email": "lisa.wang@acmecorp.com"}
        ]
        
        # Feature categories for comprehensive testing
        self.feature_categories = {
            "PRED": "Predictive Analytics & ML",
            "TAG": "Auto-Tagging & Classification", 
            "INTENT": "Intent Analysis & Decisions",
            "GAP": "Gap Detection & Analysis",
            "IMPACT": "Impact Analysis",
            "SEARCH": "Streaming Search",
            "AI": "AI Enhancement",
            "PERF": "Performance Optimization",
            "SEC": "Security & Compliance",
            "INFRA": "Infrastructure & DevOps"
        }

    async def should_seed_data(self) -> bool:
        """Check if we should seed data (development environment and no existing enhanced data)"""
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        if environment != "development":
            return False
        
        # Check if we already have enhanced data
        async with self.db.pool.acquire() as conn:
            enhanced_count = await conn.fetchval("""
                SELECT COUNT(*) FROM jira_tickets 
                WHERE organization_id = $1 AND ticket_key LIKE 'PRED-%'
            """, self.org_id)
            
            return enhanced_count == 0

    async def seed_comprehensive_data(self) -> Dict:
        """Seed comprehensive data for all investor demo features"""
        logger.info("🌱 Starting comprehensive data seeding for development...")
        
        start_time = datetime.now()
        
        try:
            # Clear any existing enhanced data first
            await self._clear_enhanced_data()
            
            # Seed comprehensive tickets (50 tickets across all categories)
            tickets = await self._seed_comprehensive_tickets()
            logger.info(f"✅ Seeded {len(tickets)} comprehensive tickets")
            
            # Seed realistic commits with proper relationships
            commits = await self._seed_realistic_commits(tickets)
            logger.info(f"✅ Seeded {len(commits)} realistic commits")
            
            # Seed complex decisions for intent analysis
            decisions = await self._seed_complex_decisions(tickets)
            logger.info(f"✅ Seeded {len(decisions)} complex decisions")
            
            # Seed orphaned data for gap detection
            orphaned_data = await self._seed_orphaned_data()
            logger.info(f"✅ Seeded orphaned data for gap detection")
            
            # Seed code files for impact analysis
            code_files = await self._seed_code_files()
            logger.info(f"✅ Seeded {len(code_files)} code files")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            summary = {
                "status": "success",
                "environment": "development",
                "tickets_added": len(tickets),
                "commits_added": len(commits),
                "decisions_added": len(decisions),
                "code_files_added": len(code_files),
                "seeding_time_seconds": duration,
                "features_ready": list(self.feature_categories.keys())
            }
            
            logger.info(f"✅ Comprehensive data seeding completed in {duration:.2f}s")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Comprehensive data seeding failed: {e}", exc_info=True)
            raise

    async def _clear_enhanced_data(self):
        """Clear any existing enhanced data to avoid duplicates"""
        async with self.db.pool.acquire() as conn:
            # Clear enhanced tickets (those with our specific prefixes)
            await conn.execute("""
                DELETE FROM jira_tickets 
                WHERE organization_id = $1 
                AND (ticket_key LIKE 'PRED-%' OR ticket_key LIKE 'TAG-%' 
                     OR ticket_key LIKE 'INTENT-%' OR ticket_key LIKE 'GAP-%'
                     OR ticket_key LIKE 'IMPACT-%' OR ticket_key LIKE 'SEARCH-%'
                     OR ticket_key LIKE 'AI-%')
            """, self.org_id)
            
            # Clear related commits and decisions
            await conn.execute("""
                DELETE FROM commits 
                WHERE organization_id = $1 
                AND (ticket_references && ARRAY['PRED-001', 'TAG-001', 'INTENT-001'])
            """, self.org_id)
            
            await conn.execute("""
                DELETE FROM decisions 
                WHERE organization_id = $1 
                AND decision_id LIKE 'DEC-%'
            """, self.org_id)

    async def _seed_comprehensive_tickets(self) -> List[Dict]:
        """Seed comprehensive tickets for all feature categories"""
        tickets = []
        
        # Predictive Analytics tickets (with historical data for ML training)
        pred_tickets = [
            {
                "key": "PRED-001",
                "summary": "Implement ML model for ticket completion prediction",
                "description": """Build machine learning model to predict ticket completion times based on historical data.

**Requirements:**
- Analyze historical velocity patterns
- Consider complexity factors (story points, components, assignee workload)
- Provide confidence intervals for predictions
- Account for team capacity and holidays

**Success Metrics:**
- Prediction accuracy >80% for tickets completed in last 90 days
- Model training time <30 minutes
- Real-time inference <100ms per prediction

**Technical Approach:**
- Feature engineering from historical ticket data
- Random Forest model for non-linear patterns
- Cross-validation with time-series split
- Model persistence and versioning""",
                "category": "PRED",
                "priority": "High",
                "status": "In Progress",
                "story_points": 8,
                "complexity": {"ui_changes": False, "db_changes": True, "api_changes": True, "ml_model": True}
            },
            {
                "key": "PRED-002",
                "summary": "Code hotspot detection algorithm",
                "description": """Identify files that change frequently and may need refactoring.

**Detection Algorithm:**
- Track file change frequency over rolling 90-day window
- Weight by number of unique developers touching file
- Consider bug density in changed files (commits with 'fix' keyword)
- Generate risk scores based on change patterns

**Output:**
- Ranked list of high-risk files
- Refactoring recommendations with effort estimates
- Impact analysis for proposed changes
- Integration with code review process""",
                "category": "PRED",
                "priority": "Medium", 
                "status": "Done",
                "story_points": 5,
                "complexity": {"ui_changes": True, "db_changes": True, "api_changes": True, "ml_model": False}
            }
        ]
        
        # Auto-Tagging tickets (diverse content for classification testing)
        tag_tickets = [
            {
                "key": "TAG-001",
                "summary": "NLP-based automatic ticket classification system",
                "description": """Implement machine learning system for automatic ticket categorization.

**Classification Categories:**
- Bug Report: Issues with existing functionality
- Feature Request: New functionality requests  
- Technical Debt: Code quality and maintenance
- Security Issue: Security vulnerabilities or concerns
- Performance Problem: Speed, memory, or scalability issues
- Documentation: Missing or incorrect documentation

**Technical Implementation:**
- TF-IDF vectorization for text features
- Naive Bayes classifier with confidence scoring
- Active learning for continuous improvement
- Feedback loop for model retraining""",
                "category": "TAG",
                "priority": "High",
                "status": "In Progress",
                "story_points": 13,
                "complexity": {"ui_changes": True, "db_changes": True, "api_changes": True, "ml_model": True}
            }
        ]
        
        # Intent Analysis tickets (complex decisions with conflicts)
        intent_tickets = [
            {
                "key": "INTENT-001", 
                "summary": "Decision extraction from unstructured meeting notes",
                "description": """Extract architectural decisions from meeting notes, emails, and documents.

**Extraction Capabilities:**
- Identify decision points in natural language text
- Extract alternatives that were considered
- Find chosen approach and supporting rationale
- Detect conflicting stakeholder viewpoints
- Generate structured decision summaries

**Sources to Process:**
- Meeting transcripts and notes
- Email thread discussions
- Slack conversation exports
- Design document comments
- Code review discussions

**Conflict Detection:**
- Identify disagreements between stakeholders
- Track resolution methods
- Measure confidence levels in decisions""",
                "category": "INTENT",
                "priority": "High",
                "status": "Done",
                "story_points": 8,
                "complexity": {"ui_changes": False, "db_changes": True, "api_changes": True, "ml_model": True}
            }
        ]
        
        # Gap Detection tickets (for testing orphaned content detection)
        gap_tickets = [
            {
                "key": "GAP-001",
                "summary": "Orphaned commit detection and analysis system",
                "description": """Identify and categorize commits that don't reference any tickets.

**Detection Logic:**
- Scan commit messages for ticket ID patterns (JIRA-123, #456, etc.)
- Flag commits without any ticket references
- Analyze commit content for automatic categorization
- Generate gap reports with recommendations

**Gap Categories:**
- Hotfixes: Emergency production fixes
- Maintenance: Dependency updates, configuration changes
- Refactoring: Code cleanup without functional changes
- Documentation: README updates, comment improvements

**Recommendations:**
- Suggest creating retroactive tickets for significant changes
- Identify patterns in orphaned commits
- Propose process improvements""",
                "category": "GAP",
                "priority": "Medium",
                "status": "To Do",
                "story_points": 5,
                "complexity": {"ui_changes": True, "db_changes": False, "api_changes": True, "ml_model": False}
            }
        ]
        
        # Combine all tickets
        all_tickets = pred_tickets + tag_tickets + intent_tickets + gap_tickets
        
        # Add more tickets for other categories to reach 50 total
        for category, description in self.feature_categories.items():
            if category not in ["PRED", "TAG", "INTENT", "GAP"]:
                for i in range(3):  # 3 tickets per remaining category
                    ticket = {
                        "key": f"{category}-{i+1:03d}",
                        "summary": f"{description} enhancement #{i+1}",
                        "description": f"Implement {description.lower()} functionality for comprehensive testing.",
                        "category": category,
                        "priority": random.choice(["Low", "Medium", "High"]),
                        "status": random.choice(["To Do", "In Progress", "Done"]),
                        "story_points": random.choice([2, 3, 5, 8]),
                        "complexity": {
                            "ui_changes": random.choice([True, False]),
                            "db_changes": random.choice([True, False]), 
                            "api_changes": True,
                            "ml_model": category in ["PRED", "TAG", "INTENT"]
                        }
                    }
                    all_tickets.append(ticket)
        
        # Insert tickets into database
        for ticket in all_tickets:
            assignee = random.choice(self.developers)
            reporter = random.choice(self.developers)
            
            created_date = datetime.now() - timedelta(days=random.randint(1, 120))
            updated_date = created_date + timedelta(days=random.randint(0, 30))
            resolved_date = updated_date + timedelta(days=random.randint(1, 20)) if ticket["status"] == "Done" else None
            
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO jira_tickets (
                        organization_id, ticket_key, summary, description,
                        issue_type, status, priority, assignee, reporter,
                        created_date, updated_date, resolved_date, story_points,
                        labels, components, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    ON CONFLICT (organization_id, ticket_key) DO NOTHING
                """,
                    self.org_id, ticket["key"], ticket["summary"], ticket["description"],
                    "Story", ticket["status"], ticket["priority"],
                    assignee["name"], reporter["name"],
                    created_date, updated_date, resolved_date, ticket["story_points"],
                    [ticket["category"].lower()], [self.feature_categories[ticket["category"]]],
                    {"complexity_factors": ticket["complexity"], "category": ticket["category"]}
                )
            
            tickets.append(ticket)
        
        return tickets

    async def _seed_realistic_commits(self, tickets: List[Dict]) -> List[Dict]:
        """Seed realistic commits with proper ticket relationships"""
        commits = []
        
        # Get repository ID
        async with self.db.pool.acquire() as conn:
            repo_row = await conn.fetchrow("""
                SELECT id FROM repositories 
                WHERE organization_id = $1 
                LIMIT 1
            """, self.org_id)
            
            if not repo_row:
                logger.warning("No repository found, skipping commit seeding")
                return commits
            
            repo_id = str(repo_row["id"])
        
        # Generate commits for completed tickets (realistic development patterns)
        completed_tickets = [t for t in tickets if t["status"] == "Done"]
        
        for ticket in completed_tickets:
            # Generate 1-4 commits per completed ticket
            num_commits = random.randint(1, 4)
            
            for i in range(num_commits):
                commit_types = ["feat", "fix", "refactor", "test", "docs"]
                commit_type = random.choice(commit_types)
                
                # Generate realistic commit messages
                if commit_type == "feat":
                    message = f"feat({ticket['category'].lower()}): implement {ticket['summary'].lower()}"
                elif commit_type == "fix":
                    message = f"fix({ticket['category'].lower()}): resolve issue in {ticket['summary'].lower()}"
                else:
                    message = f"{commit_type}({ticket['category'].lower()}): update {ticket['summary'].lower()}"
                
                # Add detailed commit body
                detailed_message = f"""{message}

{ticket['description'][:200]}...

- Implement core functionality
- Add comprehensive tests
- Update documentation
- Handle edge cases

Closes {ticket['key']}"""
                
                # Generate realistic file changes based on complexity
                files_changed = self._generate_realistic_files(ticket)
                
                commit_date = datetime.now() - timedelta(days=random.randint(1, 90))
                sha = f"{random.randint(100000, 999999):06x}{random.randint(100000, 999999):06x}"
                
                assignee_email = next(d["email"] for d in self.developers if d["name"] == ticket.get("assignee", "Unknown"))
                
                async with self.db.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO commits (
                            organization_id, repository_id, sha, message,
                            author_name, author_email, commit_date,
                            files_changed, additions, deletions, ticket_references, metadata
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        ON CONFLICT (repository_id, sha) DO NOTHING
                    """,
                        self.org_id, repo_id, sha, detailed_message,
                        ticket.get("assignee", "Unknown"), assignee_email, commit_date,
                        files_changed, random.randint(20, 300), random.randint(5, 100),
                        [ticket["key"]], {"commit_type": commit_type, "category": ticket["category"]}
                    )
                
                commits.append({
                    "sha": sha,
                    "message": detailed_message,
                    "ticket_key": ticket["key"],
                    "category": ticket["category"]
                })
        
        return commits

    def _generate_realistic_files(self, ticket: Dict) -> List[str]:
        """Generate realistic file paths based on ticket complexity and category"""
        files = []
        complexity = ticket.get("complexity", {})
        category = ticket["category"].lower()
        
        # Base paths by category
        category_paths = {
            "pred": ["src/ml/", "src/analytics/", "src/models/"],
            "tag": ["src/nlp/", "src/classification/", "src/ml/"],
            "intent": ["src/analysis/", "src/extraction/", "src/nlp/"],
            "gap": ["src/detection/", "src/analysis/", "src/reports/"],
            "impact": ["src/analysis/", "src/dependencies/", "src/graph/"],
            "search": ["src/search/", "src/streaming/", "src/api/"],
            "ai": ["src/ai/", "src/llm/", "src/services/"],
            "perf": ["src/optimization/", "src/cache/", "src/monitoring/"],
            "sec": ["src/security/", "src/auth/", "src/validation/"],
            "infra": ["infrastructure/", "k8s/", "docker/"]
        }
        
        paths = category_paths.get(category, ["src/"])
        
        # Generate files based on complexity
        if complexity.get("api_changes", True):
            files.extend([f"{random.choice(paths)}api/{category}_controller.py"])
        
        if complexity.get("db_changes", False):
            files.extend([f"migrations/add_{category}_tables.sql"])
        
        if complexity.get("ui_changes", False):
            files.extend([f"frontend/src/components/{category.title()}Component.tsx"])
        
        if complexity.get("ml_model", False):
            files.extend([f"{random.choice(paths)}models/{category}_model.py"])
        
        # Always add some core files
        files.extend([
            f"{random.choice(paths)}{category}_service.py",
            f"tests/{category}_test.py"
        ])
        
        return files[:random.randint(2, 6)]  # Limit to reasonable number

    async def _seed_complex_decisions(self, tickets: List[Dict]) -> List[Dict]:
        """Seed complex decisions with stakeholder conflicts for intent analysis testing"""
        decisions = []
        
        # Focus on high-priority tickets for decision analysis
        high_priority_tickets = [t for t in tickets if t["priority"] == "High"][:5]
        
        for ticket in high_priority_tickets:
            decision = await self._create_complex_decision(ticket)
            decisions.append(decision)
        
        return decisions

    async def _create_complex_decision(self, ticket: Dict) -> Dict:
        """Create a complex decision with multiple alternatives and conflicts"""
        
        # Generate realistic alternatives based on ticket category
        alternatives = self._generate_alternatives_for_category(ticket["category"])
        
        # Create conflicting stakeholder perspectives
        stakeholders = [
            {
                "name": "Product Manager",
                "preference": alternatives[0]["name"],
                "reasoning": "Need to prioritize time to market and user value",
                "concerns": ["Delivery timeline", "User experience", "Market competition"]
            },
            {
                "name": "Tech Lead", 
                "preference": alternatives[1]["name"],
                "reasoning": "Technical excellence and long-term maintainability are crucial",
                "concerns": ["Code quality", "Technical debt", "Team productivity"]
            },
            {
                "name": "Engineering Manager",
                "preference": alternatives[2]["name"] if len(alternatives) > 2 else alternatives[0]["name"],
                "reasoning": "Need to balance technical and business requirements",
                "concerns": ["Team capacity", "Risk management", "Stakeholder alignment"]
            }
        ]
        
        # Choose solution (usually a compromise)
        chosen = random.choice(alternatives)
        
        decision_text = f"""
# Decision: {ticket['summary']}

## Problem Statement
{ticket['description'][:500]}...

## Alternatives Considered

{chr(10).join([f"### {alt['name']}\n**Pros:** {', '.join(alt['pros'])}\n**Cons:** {', '.join(alt['cons'])}\n**Effort:** {alt['effort']}" for alt in alternatives])}

## Stakeholder Perspectives

{chr(10).join([f"**{s['name']}:** {s['reasoning']}\n*Concerns:* {', '.join(s['concerns'])}" for s in stakeholders])}

## Decision
We chose **{chosen['name']}** because it provides the best balance of technical quality and delivery speed.

## Implementation Plan
1. Phase 1: Core implementation and testing
2. Phase 2: Integration and validation  
3. Phase 3: Deployment and monitoring

## Risks and Mitigation
- **Risk:** {random.choice(['Implementation complexity', 'Timeline pressure', 'Resource constraints'])}
- **Mitigation:** {random.choice(['Regular checkpoints', 'Prototype validation', 'Parallel development'])}
"""
        
        decision_data = {
            "decision_id": f"DEC-{ticket['key']}",
            "ticket_key": ticket["key"],
            "decision_summary": f"Architecture decision for {ticket['summary']}",
            "problem_statement": ticket["description"][:500],
            "alternatives_considered": json.dumps(alternatives),
            "chosen_approach": chosen["name"],
            "rationale": decision_text,
            "stakeholders": json.dumps(stakeholders),
            "constraints": json.dumps(["Budget", "Timeline", "Technical expertise"]),
            "risks": json.dumps(["Implementation complexity", "Integration challenges"]),
            "confidence_score": random.uniform(0.6, 0.9),
            "raw_analysis": decision_text
        }
        
        # Store in database
        async with self.db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO decisions (
                    organization_id, decision_id, ticket_key, decision_summary,
                    problem_statement, alternatives_considered, chosen_approach,
                    rationale, stakeholders, constraints, risks,
                    confidence_score, raw_analysis, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (organization_id, decision_id) DO NOTHING
            """,
                self.org_id, decision_data["decision_id"], decision_data["ticket_key"],
                decision_data["decision_summary"], decision_data["problem_statement"],
                decision_data["alternatives_considered"], decision_data["chosen_approach"],
                decision_data["rationale"], decision_data["stakeholders"],
                decision_data["constraints"], decision_data["risks"],
                decision_data["confidence_score"], decision_data["raw_analysis"],
                datetime.now(), datetime.now()
            )
        
        return decision_data

    def _generate_alternatives_for_category(self, category: str) -> List[Dict]:
        """Generate realistic alternatives based on ticket category"""
        
        alternatives_by_category = {
            "PRED": [
                {
                    "name": "Simple Linear Regression",
                    "pros": ["Fast training", "Interpretable", "Low resource usage"],
                    "cons": ["Limited accuracy", "Can't capture complex patterns"],
                    "effort": "2 weeks"
                },
                {
                    "name": "Random Forest Ensemble",
                    "pros": ["Good accuracy", "Handles non-linear patterns", "Feature importance"],
                    "cons": ["Slower inference", "More complex", "Harder to debug"],
                    "effort": "4 weeks"
                },
                {
                    "name": "Neural Network",
                    "pros": ["Highest potential accuracy", "Can learn complex patterns"],
                    "cons": ["Black box", "Requires more data", "Expensive training"],
                    "effort": "8 weeks"
                }
            ],
            "TAG": [
                {
                    "name": "Rule-based Classification",
                    "pros": ["Transparent", "Fast", "Easy to maintain"],
                    "cons": ["Limited accuracy", "Manual rule creation"],
                    "effort": "2 weeks"
                },
                {
                    "name": "TF-IDF + Naive Bayes",
                    "pros": ["Good baseline accuracy", "Fast training", "Interpretable"],
                    "cons": ["Assumes feature independence", "Limited context"],
                    "effort": "3 weeks"
                },
                {
                    "name": "Transformer-based Model",
                    "pros": ["State-of-the-art accuracy", "Understands context"],
                    "cons": ["Resource intensive", "Complex deployment"],
                    "effort": "6 weeks"
                }
            ]
        }
        
        return alternatives_by_category.get(category, [
            {"name": "Option A", "pros": ["Fast"], "cons": ["Limited"], "effort": "2 weeks"},
            {"name": "Option B", "pros": ["Comprehensive"], "cons": ["Complex"], "effort": "4 weeks"}
        ])

    async def _seed_orphaned_data(self) -> Dict:
        """Seed orphaned commits and tickets for gap detection testing"""
        
        # Get repository ID
        async with self.db.pool.acquire() as conn:
            repo_row = await conn.fetchrow("""
                SELECT id FROM repositories 
                WHERE organization_id = $1 
                LIMIT 1
            """, self.org_id)
            
            if not repo_row:
                return {"orphaned_commits": 0}
            
            repo_id = str(repo_row["id"])
        
        # Create orphaned commits (commits without ticket references)
        orphaned_messages = [
            "Quick hotfix for production memory leak",
            "Update configuration for new environment", 
            "Temporary workaround for API timeout",
            "Fix typo in error message",
            "Update dependencies to latest versions",
            "Code cleanup and formatting",
            "Remove unused imports",
            "Fix linting warnings"
        ]
        
        orphaned_count = 0
        for message in orphaned_messages:
            author = random.choice(self.developers)
            commit_date = datetime.now() - timedelta(days=random.randint(1, 30))
            sha = f"{random.randint(100000, 999999):06x}{random.randint(100000, 999999):06x}"
            
            files_changed = [
                f"src/utils/{random.choice(['helpers', 'config', 'constants'])}.py",
                f"src/services/{random.choice(['auth', 'api', 'database'])}_service.py"
            ]
            
            async with conn.acquire() as conn:
                await conn.execute("""
                    INSERT INTO commits (
                        organization_id, repository_id, sha, message,
                        author_name, author_email, commit_date,
                        files_changed, additions, deletions, ticket_references, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (repository_id, sha) DO NOTHING
                """,
                    self.org_id, repo_id, sha, message,
                    author["name"], author["email"], commit_date,
                    files_changed, random.randint(1, 50), random.randint(0, 20),
                    [], {"orphaned": True}  # Empty ticket_references = orphaned!
                )
            
            orphaned_count += 1
        
        return {"orphaned_commits": orphaned_count}

    async def _seed_code_files(self) -> List[Dict]:
        """Seed code files for impact analysis testing"""
        code_files = []
        
        # Get repository ID
        async with self.db.pool.acquire() as conn:
            repo_row = await conn.fetchrow("""
                SELECT id FROM repositories 
                WHERE organization_id = $1 
                LIMIT 1
            """, self.org_id)
            
            if not repo_row:
                return code_files
            
            repo_id = str(repo_row["id"])
        
        # Generate code files for different categories
        file_templates = {
            "ml_model": {
                "path": "src/ml/prediction_model.py",
                "content": '''"""Ticket completion prediction model using Random Forest."""
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class TicketPredictionModel:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.features = ["story_points", "complexity_score", "team_velocity"]
    
    def train(self, historical_data: pd.DataFrame):
        """Train the model on historical ticket data."""
        X = historical_data[self.features]
        y = historical_data["completion_days"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        self.model.fit(X_train, y_train)
        
        return self.model.score(X_test, y_test)
    
    def predict(self, ticket_features: dict) -> dict:
        """Predict completion time for a ticket."""
        features_array = [[ticket_features[f] for f in self.features]]
        prediction = self.model.predict(features_array)[0]
        
        return {
            "estimated_days": prediction,
            "confidence": 0.85
        }
''',
                "language": "Python",
                "functions": ["train", "predict"],
                "classes": ["TicketPredictionModel"]
            },
            "api_controller": {
                "path": "src/api/predictions_controller.py", 
                "content": '''"""API controller for prediction endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from services.prediction_service import PredictionService

router = APIRouter(prefix="/predict", tags=["predictions"])

@router.post("/ticket-completion")
async def predict_ticket_completion(
    ticket_key: str,
    prediction_service: PredictionService = Depends()
):
    """Predict when a ticket will be completed."""
    try:
        prediction = await prediction_service.predict_completion(ticket_key)
        return {"prediction": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hotspots")
async def get_code_hotspots(
    lookback_days: int = 90,
    prediction_service: PredictionService = Depends()
):
    """Get code files that change frequently."""
    hotspots = await prediction_service.detect_hotspots(lookback_days)
    return {"hotspots": hotspots}
''',
                "language": "Python",
                "functions": ["predict_ticket_completion", "get_code_hotspots"],
                "classes": []
            }
        }
        
        for template_name, template in file_templates.items():
            file_data = {
                "repository_id": repo_id,
                "organization_id": self.org_id,
                "file_path": template["path"],
                "file_name": template["path"].split("/")[-1],
                "file_type": template["path"].split(".")[-1],
                "language": template["language"],
                "content": template["content"],
                "functions": template["functions"],
                "classes": template["classes"],
                "imports": [],
                "line_count": len(template["content"].split("\n")),
                "last_modified": datetime.now() - timedelta(days=random.randint(1, 30)),
                "metadata": {"template": template_name}
            }
            
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO code_files (
                        repository_id, organization_id, file_path, file_name, file_type,
                        language, content, functions, classes, imports, line_count,
                        last_modified, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (repository_id, file_path) DO NOTHING
                """,
                    repo_id, self.org_id, file_data["file_path"], file_data["file_name"],
                    file_data["file_type"], file_data["language"], file_data["content"],
                    file_data["functions"], file_data["classes"], file_data["imports"],
                    file_data["line_count"], file_data["last_modified"], file_data["metadata"]
                )
            
            code_files.append(file_data)
        
        return code_files


# Global instance for use in startup
comprehensive_seeder = None

async def initialize_comprehensive_seeder(db_service):
    """Initialize the comprehensive seeder with database service"""
    global comprehensive_seeder
    comprehensive_seeder = ComprehensiveDataSeeder(db_service)
    return comprehensive_seeder

async def seed_development_data(db_service) -> Optional[Dict]:
    """
    Seed comprehensive data if in development environment.
    Called during API startup.
    """
    seeder = await initialize_comprehensive_seeder(db_service)
    
    if await seeder.should_seed_data():
        return await seeder.seed_comprehensive_data()
    else:
        logger.info("Skipping data seeding (not development or data already exists)")
        return None