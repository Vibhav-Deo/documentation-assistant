"""
Demo Data Generator Service

Generates realistic demo data for investor presentations including:
- Jira tickets with realistic content
- Git commits with proper relationships
- Pull requests linked to tickets
- Documentation samples
- Gap examples (orphaned tickets, undocumented features)
- Decision scenarios with conflicts

Optimized for <60 second load time with progress indicators.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from faker import Faker
import asyncio


class DemoDataGenerator:
    """
    Generates comprehensive demo data for the Enterprise RAG platform.
    
    Features:
    - Relationship-aware data generation
    - Realistic development patterns
    - Gap examples for demonstration
    - Diverse decision scenarios
    - Progress tracking and parallel processing
    """

    def __init__(self, db_service):
        self.db = db_service
        self.fake = Faker()
        
        # Demo organization and users
        self.demo_org_id = None
        self.demo_users = []
        
        # Data templates
        self.project_names = [
            "AuthFlow", "PaymentGateway", "UserDashboard", "APIGateway", 
            "DataPipeline", "NotificationService", "SearchEngine", "Analytics"
        ]
        
        self.tech_stack = [
            "React", "Node.js", "Python", "PostgreSQL", "Redis", "Docker",
            "Kubernetes", "AWS", "TypeScript", "FastAPI", "MongoDB", "GraphQL"
        ]
        
        self.feature_types = [
            "authentication", "payment", "notification", "search", "analytics",
            "security", "performance", "ui", "api", "database", "deployment"
        ]

    async def generate_complete_demo_data(
        self, 
        org_name: str = "Demo Corporation",
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Generate additional demo dataset for presentations (separate from development data).
        
        This generates presentation-specific data that doesn't conflict with the 
        comprehensive development data that's automatically seeded.
        
        Returns summary of generated data.
        """
        start_time = datetime.now()
        
        if progress_callback:
            progress_callback("Starting presentation demo data generation...", 0)

        # Check if we should create a separate demo org or use existing
        existing_org = await self._check_existing_demo_org(org_name)
        if existing_org:
            self.demo_org_id = str(existing_org["id"])
            if progress_callback:
                progress_callback("Using existing demo organization", 10)
        else:
            # Step 1: Create organization and users (10%)
            await self._create_demo_organization(org_name)
            if progress_callback:
                progress_callback("Created demo organization and users", 10)

        # Step 2: Generate presentation-specific tickets (30%)
        tickets = await self._generate_presentation_tickets(20)
        if progress_callback:
            progress_callback(f"Generated {len(tickets)} presentation tickets", 30)

        # Step 3: Generate commits (50%)
        commits = await self._generate_commits_for_tickets(tickets, 50)
        if progress_callback:
            progress_callback(f"Generated {len(commits)} commits", 50)

        # Step 4: Generate PRs (70%)
        prs = await self._generate_pull_requests(tickets, commits, 15)
        if progress_callback:
            progress_callback(f"Generated {len(prs)} pull requests", 70)

        # Step 5: Generate documentation (90%)
        docs = await self._generate_documentation_samples(10)
        if progress_callback:
            progress_callback(f"Generated {len(docs)} documents", 90)

        # Step 6: Complete (100%)
        if progress_callback:
            progress_callback("Presentation demo data generation complete!", 100)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            "status": "success",
            "type": "presentation_demo",
            "organization_id": self.demo_org_id,
            "summary": {
                "tickets": len(tickets),
                "commits": len(commits),
                "pull_requests": len(prs),
                "documents": len(docs),
                "users": len(self.demo_users)
            },
            "generation_time_seconds": duration,
            "created_at": end_time.isoformat()
        }

    async def _check_existing_demo_org(self, org_name: str) -> Optional[Dict]:
        """Check if demo organization already exists"""
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, name FROM organizations 
                WHERE name = $1
            """, org_name)
            return dict(row) if row else None
    async def _create_demo_organization(self, org_name: str) -> None:
        """Create demo organization and users."""
        # Create organization
        org_data = await self.db.create_organization(org_name, "enterprise")
        self.demo_org_id = str(org_data["id"])
        
        # Create demo users
        demo_users_data = [
            ("alice.johnson@democorp.com", "Alice Johnson", "admin"),
            ("bob.smith@democorp.com", "Bob Smith", "user"),
            ("carol.davis@democorp.com", "Carol Davis", "user"),
            ("david.wilson@democorp.com", "David Wilson", "user"),
            ("eve.brown@democorp.com", "Eve Brown", "user"),
        ]
        
        for email, name, role in demo_users_data:
            # Simple password hash for demo
            password_hash = "$2b$12$demo.hash.for.presentation.only"
            user_data = await self.db.create_user(
                email, password_hash, name, self.demo_org_id, role
            )
            self.demo_users.append(user_data)

    async def _generate_presentation_tickets(self, count: int) -> List[Dict]:
        """Generate presentation-specific tickets (different from development data)"""
        tickets = []
        
        for i in range(count):
            project = random.choice(self.project_names)
            feature_type = random.choice(self.feature_types)
            tech = random.choice(self.tech_stack)
            
            # Generate presentation-focused ticket content
            ticket_key = f"DEMO-PRES-{i+1:03d}"
            
            summaries = [
                f"Showcase {feature_type} capabilities with {tech}",
                f"Demo {feature_type} integration in {project}",
                f"Present {feature_type} performance improvements",
                f"Demonstrate {tech} benefits in {project}",
                f"Exhibit {project} {feature_type} features"
            ]
            
            summary = random.choice(summaries)
            
            # Generate description focused on demo value
            description = f"This ticket demonstrates our {feature_type} capabilities using {tech}. " \
                         f"It showcases the integration with {project} and highlights the business value " \
                         f"of our technical approach. Perfect for investor presentations."
            
            # Realistic ticket metadata for presentations
            ticket_data = {
                "organization_id": self.demo_org_id,
                "ticket_key": ticket_key,
                "summary": summary,
                "description": description,
                "issue_type": random.choice(["Story", "Epic", "Task"]),
                "status": random.choice(["Done", "In Progress", "Done", "Done"]),  # Bias toward completed
                "priority": random.choice(["Medium", "High", "High"]),  # Bias toward important
                "assignee": random.choice(self.demo_users)["email"] if self.demo_users else "demo@example.com",
                "reporter": random.choice(self.demo_users)["email"] if self.demo_users else "demo@example.com",
                "created_date": self.fake.date_time_between(start_date="-60d", end_date="-30d"),
                "updated_date": self.fake.date_time_between(start_date="-30d", end_date="now"),
                "story_points": random.choice([3, 5, 8, 13]),  # Meaningful sizes
                "labels": [feature_type, tech, "demo"],
                "components": [project, "presentation"],
                "metadata": {
                    "demo_purpose": "investor_presentation",
                    "business_value": "high"
                }
            }
            
            # Store in database
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO jira_tickets (
                        organization_id, ticket_key, summary, description, issue_type,
                        status, priority, assignee, reporter, created_date, updated_date,
                        story_points, labels, components, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (organization_id, ticket_key) DO NOTHING
                """, 
                    self.demo_org_id, ticket_key, summary, description, ticket_data["issue_type"],
                    ticket_data["status"], ticket_data["priority"], ticket_data["assignee"],
                    ticket_data["reporter"], ticket_data["created_date"], ticket_data["updated_date"],
                    ticket_data["story_points"], ticket_data["labels"], ticket_data["components"],
                    ticket_data["metadata"]
                )
            
            tickets.append(ticket_data)
        
        return tickets

    async def _generate_realistic_tickets(self, count: int) -> List[Dict]:
        """Generate realistic Jira tickets with proper relationships."""
        tickets = []
        
        for i in range(count):
            project = random.choice(self.project_names)
            feature_type = random.choice(self.feature_types)
            tech = random.choice(self.tech_stack)
            
            # Generate realistic ticket content
            ticket_key = f"DEMO-{i+1:03d}"
            
            summaries = [
                f"Implement {feature_type} using {tech}",
                f"Fix {feature_type} bug in {project}",
                f"Optimize {feature_type} performance",
                f"Add {tech} integration to {project}",
                f"Refactor {project} {feature_type} module",
                f"Update {feature_type} documentation",
                f"Add unit tests for {feature_type}",
                f"Security review for {project} {feature_type}"
            ]
            
            summary = random.choice(summaries)
            
            # Generate description with decision context
            descriptions = [
                f"We need to implement {feature_type} functionality in {project}. "
                f"After evaluating multiple options including {random.choice(self.tech_stack)} "
                f"and {random.choice(self.tech_stack)}, we decided to go with {tech} "
                f"because of its performance characteristics and team familiarity.",
                
                f"Users are experiencing issues with {feature_type}. "
                f"The current implementation using {random.choice(self.tech_stack)} "
                f"is not scaling well. We should migrate to {tech} to resolve this.",
                
                f"As part of our {project} modernization effort, we need to "
                f"update the {feature_type} component. This will improve "
                f"maintainability and performance.",
            ]
            
            description = random.choice(descriptions)
            
            # Realistic ticket metadata
            ticket_data = {
                "organization_id": self.demo_org_id,
                "ticket_key": ticket_key,
                "summary": summary,
                "description": description,
                "issue_type": random.choice(["Story", "Bug", "Task", "Epic"]),
                "status": random.choice(["To Do", "In Progress", "Done", "Closed"]),
                "priority": random.choice(["Low", "Medium", "High", "Critical"]),
                "assignee": random.choice(self.demo_users)["email"],
                "reporter": random.choice(self.demo_users)["email"],
                "created_date": self.fake.date_time_between(start_date="-90d", end_date="now"),
                "updated_date": self.fake.date_time_between(start_date="-30d", end_date="now"),
                "story_points": random.choice([1, 2, 3, 5, 8, 13]) if random.random() > 0.3 else None,
                "labels": [feature_type, tech] if random.random() > 0.5 else [],
                "components": [project] if random.random() > 0.4 else [],
                "metadata": {
                    "comments": self._generate_ticket_comments(),
                    "attachments": random.randint(0, 3)
                }
            }
            
            # Store in database
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO jira_tickets (
                        organization_id, ticket_key, summary, description, issue_type,
                        status, priority, assignee, reporter, created_date, updated_date,
                        story_points, labels, components, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (organization_id, ticket_key) DO NOTHING
                """, 
                    self.demo_org_id, ticket_key, summary, description, ticket_data["issue_type"],
                    ticket_data["status"], ticket_data["priority"], ticket_data["assignee"],
                    ticket_data["reporter"], ticket_data["created_date"], ticket_data["updated_date"],
                    ticket_data["story_points"], ticket_data["labels"], ticket_data["components"],
                    ticket_data["metadata"]
                )
            
            tickets.append(ticket_data)
        
        return tickets

    def _generate_ticket_comments(self) -> List[Dict]:
        """Generate realistic ticket comments."""
        comments = []
        comment_count = random.randint(0, 5)
        
        comment_templates = [
            "I think we should consider {tech} for this implementation.",
            "The current approach has some limitations. What about using {tech}?",
            "After discussion with the team, we decided to go with {tech}.",
            "This is blocked by DEMO-{num}. We need to resolve that first.",
            "Updated the implementation based on code review feedback.",
            "Testing shows this approach works well. Ready for review.",
            "Documentation has been updated to reflect the changes."
        ]
        
        for i in range(comment_count):
            comment = random.choice(comment_templates).format(
                tech=random.choice(self.tech_stack),
                num=random.randint(1, 50)
            )
            
            comments.append({
                "author": random.choice(self.demo_users)["name"],
                "body": comment,
                "created": self.fake.date_time_between(start_date="-30d", end_date="now").isoformat()
            })
        
        return comments
    async def _generate_commits_for_tickets(self, tickets: List[Dict], count: int) -> List[Dict]:
        """Generate realistic commits linked to tickets."""
        commits = []
        
        # Create a repository first
        repo_data = {
            "organization_id": self.demo_org_id,
            "repo_url": "https://github.com/democorp/enterprise-platform",
            "repo_name": "enterprise-platform",
            "provider": "github",
            "branch": "main",
            "last_synced": datetime.now(),
            "file_count": 150,
            "metadata": {"language": "TypeScript", "framework": "React"}
        }
        
        async with self.db.pool.acquire() as conn:
            repo_row = await conn.fetchrow("""
                INSERT INTO repositories (
                    organization_id, repo_url, repo_name, provider, branch,
                    last_synced, file_count, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (organization_id, repo_url) 
                DO UPDATE SET last_synced = EXCLUDED.last_synced
                RETURNING id
            """, 
                self.demo_org_id, repo_data["repo_url"], repo_data["repo_name"],
                repo_data["provider"], repo_data["branch"], repo_data["last_synced"],
                repo_data["file_count"], repo_data["metadata"]
            )
            repo_id = str(repo_row["id"])
        
        # Generate commits
        for i in range(count):
            # 70% of commits should reference tickets
            if random.random() < 0.7 and tickets:
                ticket = random.choice(tickets)
                ticket_key = ticket["ticket_key"]
                ticket_references = [ticket_key]
                
                # Generate commit message that references the ticket
                commit_messages = [
                    f"feat({ticket_key}): implement {ticket['summary'].lower()}",
                    f"fix({ticket_key}): resolve {ticket['summary'].lower()}",
                    f"refactor({ticket_key}): improve {ticket['summary'].lower()}",
                    f"test({ticket_key}): add tests for {ticket['summary'].lower()}",
                    f"docs({ticket_key}): update documentation for {ticket['summary'].lower()}",
                    f"{ticket_key}: {ticket['summary']}"
                ]
                message = random.choice(commit_messages)
            else:
                # Commits without ticket references (will be "undocumented")
                ticket_references = []
                generic_messages = [
                    "fix: minor bug fixes",
                    "chore: update dependencies",
                    "style: code formatting",
                    "refactor: cleanup unused code",
                    "perf: optimize database queries",
                    "build: update build configuration"
                ]
                message = random.choice(generic_messages)
            
            # Generate realistic file changes
            file_extensions = [".ts", ".tsx", ".py", ".js", ".jsx", ".sql", ".md", ".json"]
            files_changed = []
            num_files = random.randint(1, 8)
            
            for _ in range(num_files):
                project = random.choice(self.project_names).lower()
                feature = random.choice(self.feature_types)
                ext = random.choice(file_extensions)
                
                file_paths = [
                    f"src/{project}/{feature}/index{ext}",
                    f"src/{project}/{feature}/service{ext}",
                    f"src/{project}/components/{feature}{ext}",
                    f"tests/{project}/{feature}.test{ext}",
                    f"docs/{project}/{feature}{ext}",
                    f"src/utils/{feature}{ext}"
                ]
                
                files_changed.append(random.choice(file_paths))
            
            commit_data = {
                "repository_id": repo_id,
                "organization_id": self.demo_org_id,
                "sha": self.fake.sha1(),
                "message": message,
                "author_name": random.choice(self.demo_users)["name"],
                "author_email": random.choice(self.demo_users)["email"],
                "commit_date": self.fake.date_time_between(start_date="-60d", end_date="now"),
                "files_changed": files_changed,
                "additions": random.randint(5, 200),
                "deletions": random.randint(0, 50),
                "ticket_references": ticket_references,
                "metadata": {"branch": "main", "merge_commit": random.random() < 0.2}
            }
            
            # Store in database
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO commits (
                        repository_id, organization_id, sha, message, author_name,
                        author_email, commit_date, files_changed, additions, deletions,
                        ticket_references, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (repository_id, sha) DO NOTHING
                """,
                    repo_id, self.demo_org_id, commit_data["sha"], commit_data["message"],
                    commit_data["author_name"], commit_data["author_email"], commit_data["commit_date"],
                    commit_data["files_changed"], commit_data["additions"], commit_data["deletions"],
                    commit_data["ticket_references"], commit_data["metadata"]
                )
            
            commits.append(commit_data)
        
        return commits

    async def _generate_pull_requests(self, tickets: List[Dict], commits: List[Dict], count: int) -> List[Dict]:
        """Generate realistic pull requests linked to tickets and commits."""
        prs = []
        
        # Get repository ID from commits
        if not commits:
            return prs
        
        repo_id = commits[0]["repository_id"]
        
        for i in range(count):
            # 80% of PRs should reference tickets
            if random.random() < 0.8 and tickets:
                ticket = random.choice(tickets)
                ticket_key = ticket["ticket_key"]
                
                title = f"{ticket_key}: {ticket['summary']}"
                description = f"Implements {ticket['summary']}.\n\nCloses {ticket_key}"
                ticket_references = [ticket_key]
            else:
                # PRs without ticket references
                title = random.choice([
                    "Hotfix: Critical bug resolution",
                    "Chore: Dependency updates",
                    "Refactor: Code cleanup",
                    "Performance: Query optimization"
                ])
                description = f"This PR addresses {title.lower()}."
                ticket_references = []
            
            # Link to some commits
            related_commits = random.sample(commits, min(random.randint(1, 5), len(commits)))
            commit_shas = [commit["sha"] for commit in related_commits]
            
            pr_data = {
                "repository_id": repo_id,
                "organization_id": self.demo_org_id,
                "pr_number": i + 1,
                "title": title,
                "description": description,
                "author_name": random.choice(self.demo_users)["name"],
                "state": random.choice(["open", "merged", "closed"]),
                "created_at_pr": self.fake.date_time_between(start_date="-45d", end_date="now"),
                "merged_at": self.fake.date_time_between(start_date="-30d", end_date="now") if random.random() < 0.7 else None,
                "closed_at": None,
                "commit_shas": commit_shas,
                "ticket_references": ticket_references,
                "metadata": {
                    "reviewers": random.sample([user["name"] for user in self.demo_users], random.randint(1, 3)),
                    "labels": ["enhancement", "bug", "feature"][random.randint(0, 2)] if random.random() > 0.5 else None
                }
            }
            
            # Store in database
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO pull_requests (
                        repository_id, organization_id, pr_number, title, description,
                        author_name, state, created_at_pr, merged_at, closed_at,
                        commit_shas, ticket_references, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (repository_id, pr_number) DO NOTHING
                """,
                    repo_id, self.demo_org_id, pr_data["pr_number"], pr_data["title"],
                    pr_data["description"], pr_data["author_name"], pr_data["state"],
                    pr_data["created_at_pr"], pr_data["merged_at"], pr_data["closed_at"],
                    pr_data["commit_shas"], pr_data["ticket_references"], pr_data["metadata"]
                )
            
            prs.append(pr_data)
        
        return prs
    async def _generate_code_files(self, count: int) -> List[Dict]:
        """Generate realistic code files."""
        code_files = []
        
        # Get repository ID
        async with self.db.pool.acquire() as conn:
            repo_row = await conn.fetchrow("""
                SELECT id FROM repositories 
                WHERE organization_id = $1 
                LIMIT 1
            """, self.demo_org_id)
            
            if not repo_row:
                return code_files
            
            repo_id = str(repo_row["id"])
        
        # File templates
        file_templates = {
            "component": {
                "path": "src/components/{name}/{name}.tsx",
                "content": """import React from 'react';
import {{ {name}Props }} from './{name}.types';

export const {name}: React.FC<{name}Props> = ({{ children, ...props }}) => {{
  return (
    <div className="{name.lower()}" {{...props}}>
      {{children}}
    </div>
  );
}};

export default {name};""",
                "functions": ["React.FC"],
                "classes": [],
                "imports": ["React"]
            },
            "service": {
                "path": "src/services/{name}Service.ts",
                "content": """export class {name}Service {{
  private baseUrl: string;

  constructor(baseUrl: string) {{
    this.baseUrl = baseUrl;
  }}

  async get{name}(id: string): Promise<{name}> {{
    const response = await fetch(`${{this.baseUrl}}/{name.lower()}/${{id}}`);
    return response.json();
  }}

  async create{name}(data: Partial<{name}>): Promise<{name}> {{
    const response = await fetch(`${{this.baseUrl}}/{name.lower()}`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(data)
    }});
    return response.json();
  }}
}}""",
                "functions": ["get{name}", "create{name}"],
                "classes": ["{name}Service"],
                "imports": []
            },
            "api": {
                "path": "src/api/{name}.py",
                "content": """from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models import {name}, {name}Create
from services import {name}Service

router = APIRouter()

@router.get("/{name.lower()}/", response_model=List[{name}])
async def get_{name.lower()}s():
    \"\"\"Get all {name.lower()}s\"\"\"
    return await {name}Service.get_all()

@router.post("/{name.lower()}/", response_model={name})
async def create_{name.lower()}(data: {name}Create):
    \"\"\"Create a new {name.lower()}\"\"\"
    return await {name}Service.create(data)

@router.get("/{name.lower()}/{{id}}", response_model={name})
async def get_{name.lower()}(id: str):
    \"\"\"Get {name.lower()} by ID\"\"\"
    result = await {name}Service.get_by_id(id)
    if not result:
        raise HTTPException(status_code=404, detail="{name} not found")
    return result""",
                "functions": ["get_{name.lower()}s", "create_{name.lower()}", "get_{name.lower()}"],
                "classes": [],
                "imports": ["APIRouter", "Depends", "HTTPException", "List"]
            }
        }
        
        for i in range(count):
            template_type = random.choice(list(file_templates.keys()))
            template = file_templates[template_type]
            
            # Generate name based on feature types
            name = random.choice([
                "Auth", "Payment", "User", "Dashboard", "Analytics", "Search",
                "Notification", "Profile", "Settings", "Report", "Export", "Import"
            ])
            
            file_path = template["path"].format(name=name)
            content = template["content"].format(name=name)
            
            # Determine file properties
            file_name = file_path.split("/")[-1]
            file_type = file_name.split(".")[-1] if "." in file_name else "unknown"
            
            language_map = {
                "tsx": "TypeScript",
                "ts": "TypeScript", 
                "py": "Python",
                "js": "JavaScript",
                "jsx": "JavaScript"
            }
            
            language = language_map.get(file_type, "Unknown")
            
            file_data = {
                "repository_id": repo_id,
                "organization_id": self.demo_org_id,
                "file_path": file_path,
                "file_name": file_name,
                "file_type": file_type,
                "language": language,
                "content": content,
                "functions": [f.format(name=name) for f in template["functions"]],
                "classes": [c.format(name=name) for c in template["classes"]],
                "imports": template["imports"],
                "line_count": len(content.split("\n")),
                "last_modified": self.fake.date_time_between(start_date="-30d", end_date="now"),
                "metadata": {"size_bytes": len(content), "encoding": "utf-8"}
            }
            
            # Store in database
            async with self.db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO code_files (
                        repository_id, organization_id, file_path, file_name, file_type,
                        language, content, functions, classes, imports, line_count,
                        last_modified, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (repository_id, file_path) DO NOTHING
                """,
                    repo_id, self.demo_org_id, file_data["file_path"], file_data["file_name"],
                    file_data["file_type"], file_data["language"], file_data["content"],
                    file_data["functions"], file_data["classes"], file_data["imports"],
                    file_data["line_count"], file_data["last_modified"], file_data["metadata"]
                )
            
            code_files.append(file_data)
        
        return code_files

    async def _generate_gap_examples(self, tickets: List[Dict], commits: List[Dict]) -> Dict:
        """Generate specific gap examples for demonstration."""
        gap_data = {
            "orphaned_tickets": [],
            "undocumented_commits": [],
            "stale_tickets": [],
            "missing_decisions": []
        }
        
        # Create some orphaned tickets (tickets with no commits)
        orphaned_count = min(5, len(tickets) // 4)
        for ticket in tickets[:orphaned_count]:
            # Remove ticket references from some commits to create orphans
            gap_data["orphaned_tickets"].append({
                "ticket_key": ticket["ticket_key"],
                "summary": ticket["summary"],
                "days_orphaned": (datetime.now() - ticket["created_date"]).days,
                "priority": ticket["priority"]
            })
        
        # Create undocumented commits (commits without ticket references)
        undocumented_commits = [c for c in commits if not c["ticket_references"]]
        gap_data["undocumented_commits"] = undocumented_commits[:10]
        
        # Create stale tickets (old tickets still in progress)
        stale_tickets = [
            t for t in tickets 
            if t["status"] in ["In Progress", "To Do"] and 
            (datetime.now() - t["updated_date"]).days > 30
        ]
        gap_data["stale_tickets"] = stale_tickets[:8]
        
        # Create tickets that need decision analysis
        gap_data["missing_decisions"] = [
            {
                "ticket_key": t["ticket_key"],
                "summary": t["summary"],
                "has_implementation": len([c for c in commits if t["ticket_key"] in c.get("ticket_references", [])]) > 0,
                "needs_analysis": True
            }
            for t in tickets[:6]
        ]
        
        return gap_data

    async def _generate_decision_scenarios(self, tickets: List[Dict]) -> List[Dict]:
        """Generate diverse decision scenarios with conflicts."""
        decisions = []
        
        decision_templates = [
            {
                "type": "simple",
                "problem": "Need to choose authentication method",
                "alternatives": ["JWT", "OAuth 2.0", "Session-based"],
                "chosen": "OAuth 2.0",
                "reasoning": "Better security and user experience",
                "confidence": 0.9
            },
            {
                "type": "complex",
                "problem": "Database selection for high-traffic application",
                "alternatives": ["PostgreSQL", "MongoDB", "Redis + PostgreSQL"],
                "chosen": "Redis + PostgreSQL",
                "reasoning": "Hybrid approach provides both performance and consistency",
                "confidence": 0.7,
                "conflicts": ["Team prefers MongoDB", "Budget constraints favor single DB"]
            },
            {
                "type": "conflicted",
                "problem": "Frontend framework choice",
                "alternatives": ["React", "Vue.js", "Angular"],
                "chosen": "React",
                "reasoning": "Team expertise and ecosystem",
                "confidence": 0.6,
                "conflicts": ["Performance concerns", "Learning curve for junior developers"]
            }
        ]
        
        for i, ticket in enumerate(tickets):
            template = decision_templates[i % len(decision_templates)]
            
            decision_data = {
                "decision_id": f"decision_{ticket['ticket_key']}_{int(datetime.now().timestamp())}",
                "ticket_key": ticket["ticket_key"],
                "decision_summary": f"Chose {template['chosen']} for {template['problem'].lower()}",
                "problem_statement": template["problem"],
                "alternatives_considered": template["alternatives"],
                "chosen_approach": template["chosen"],
                "rationale": template["reasoning"],
                "constraints": ["Budget limitations", "Timeline constraints", "Team expertise"],
                "risks": ["Technical debt", "Performance impact", "Maintenance overhead"],
                "tradeoffs": "Prioritized speed over flexibility",
                "stakeholders": [user["name"] for user in self.demo_users[:3]],
                "implementation_commits": [],
                "related_prs": [],
                "related_docs": [],
                "raw_analysis": f"Analysis for {ticket['ticket_key']}: {template['reasoning']}",
                "confidence_score": template["confidence"]
            }
            
            # Store decision
            await self.db.create_decision(decision_data, self.demo_org_id)
            decisions.append(decision_data)
        
        return decisions

    async def _generate_documentation_samples(self, count: int) -> List[Dict]:
        """Generate sample documentation."""
        docs = []
        
        doc_templates = [
            {
                "title": "API Authentication Guide",
                "content": "This guide explains how to authenticate with our API using OAuth 2.0..."
            },
            {
                "title": "Database Schema Documentation", 
                "content": "Our database uses PostgreSQL with the following schema..."
            },
            {
                "title": "Deployment Guide",
                "content": "Follow these steps to deploy the application to production..."
            }
        ]
        
        for i in range(count):
            template = doc_templates[i % len(doc_templates)]
            docs.append({
                "title": f"{template['title']} v{i+1}",
                "content": template["content"],
                "created_at": self.fake.date_time_between(start_date="-60d", end_date="now")
            })
        
        return docs