"""
Auto-Tagging Service

Automatically classifies and tags:
1. Jira tickets (by category/type)
2. Commits (feature/bugfix/refactor/docs)
3. Documents (by topic)

Uses simple NLP techniques for demo purposes:
- TF-IDF + keyword matching for tickets
- Regex patterns for commits
- Keyword extraction for documents
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import Counter
import re
from enum import Enum


class CommitType(Enum):
    """Types of commits."""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TEST = "test"
    CHORE = "chore"


@dataclass
class Tag:
    """A tag with confidence score."""
    name: str
    category: str
    confidence: float
    source: str  # "auto" or "manual"


@dataclass
class Topic:
    """A document topic."""
    name: str
    keywords: List[str]
    confidence: float


class AutoTaggingService:
    """
    Automatic tagging and classification service.
    
    Uses simple NLP techniques suitable for demo:
    - Keyword matching for tickets
    - Pattern matching for commits
    - Frequency analysis for documents
    """
    
    def __init__(self, db_service):
        self.db = db_service
        
        # Predefined tag categories and keywords
        self.ticket_categories = {
            "authentication": ["auth", "login", "password", "jwt", "token", "oauth", "sso"],
            "database": ["database", "sql", "query", "schema", "migration", "postgres", "mysql"],
            "api": ["api", "endpoint", "rest", "graphql", "request", "response"],
            "frontend": ["ui", "frontend", "react", "vue", "angular", "component", "css"],
            "backend": ["backend", "server", "service", "microservice", "lambda"],
            "security": ["security", "vulnerability", "xss", "csrf", "encryption", "secure"],
            "performance": ["performance", "slow", "optimize", "cache", "latency", "speed"],
            "bug": ["bug", "error", "crash", "fail", "broken", "issue", "problem"],
            "feature": ["feature", "enhancement", "new", "add", "implement"],
            "documentation": ["docs", "documentation", "readme", "guide", "tutorial"],
            "testing": ["test", "testing", "unit test", "integration", "qa"],
            "devops": ["deploy", "ci/cd", "docker", "kubernetes", "pipeline", "build"]
        }
        
        # Commit type patterns
        self.commit_patterns = {
            CommitType.FEATURE: [
                r"^feat(\(.*\))?:",
                r"^feature:",
                r"add\s+new",
                r"implement",
                r"introduce"
            ],
            CommitType.BUGFIX: [
                r"^fix(\(.*\))?:",
                r"^bug:",
                r"resolve",
                r"patch",
                r"hotfix"
            ],
            CommitType.REFACTOR: [
                r"^refactor(\(.*\))?:",
                r"^refact:",
                r"restructure",
                r"reorganize",
                r"clean\s+up"
            ],
            CommitType.DOCUMENTATION: [
                r"^docs(\(.*\))?:",
                r"^doc:",
                r"update.*readme",
                r"add.*documentation"
            ],
            CommitType.TEST: [
                r"^test(\(.*\))?:",
                r"add.*test",
                r"update.*test",
                r"fix.*test"
            ],
            CommitType.CHORE: [
                r"^chore(\(.*\))?:",
                r"^build:",
                r"^ci:",
                r"update.*dependencies",
                r"bump.*version"
            ]
        }
    
    async def tag_ticket(
        self,
        ticket: Dict,
        org_id: str
    ) -> List[Tag]:
        """
        Auto-tag Jira ticket based on content analysis.
        
        Uses keyword matching against predefined categories.
        
        Args:
            ticket: Ticket data dict
            org_id: Organization ID
            
        Returns:
            List of Tag objects with confidence scores
            
        Validates: Requirements 3.1
        """
        text = f"{ticket.get('summary', '')} {ticket.get('description', '')}".lower()
        
        tags = []
        for category, keywords in self.ticket_categories.items():
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in text)
            
            if matches > 0:
                # Calculate confidence based on match count
                confidence = min(0.95, 0.5 + (matches * 0.15))
                
                tags.append(Tag(
                    name=category,
                    category="ticket_category",
                    confidence=confidence,
                    source="auto"
                ))
        
        # Sort by confidence
        tags.sort(key=lambda t: t.confidence, reverse=True)
        
        # Return top 5 tags
        return tags[:5]
    
    async def classify_commit(
        self,
        commit: Dict
    ) -> CommitType:
        """
        Classify commit by type using pattern recognition.
        
        Uses conventional commit patterns and message analysis.
        
        Args:
            commit: Commit data dict
            
        Returns:
            CommitType enum value
            
        Validates: Requirements 3.2
        """
        message = commit.get('message', '').lower()
        
        # Try each pattern type
        for commit_type, patterns in self.commit_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return commit_type
        
        # Default classification based on keywords
        if any(word in message for word in ['fix', 'bug', 'error', 'issue']):
            return CommitType.BUGFIX
        elif any(word in message for word in ['add', 'new', 'feature', 'implement']):
            return CommitType.FEATURE
        elif any(word in message for word in ['refactor', 'clean', 'restructure']):
            return CommitType.REFACTOR
        elif any(word in message for word in ['test', 'spec']):
            return CommitType.TEST
        elif any(word in message for word in ['doc', 'readme', 'comment']):
            return CommitType.DOCUMENTATION
        else:
            return CommitType.CHORE
    
    async def extract_document_topics(
        self,
        document: Dict
    ) -> List[Topic]:
        """
        Extract key topics from documentation.
        
        Uses keyword frequency analysis and predefined categories.
        
        Args:
            document: Document data dict
            
        Returns:
            List of Topic objects
            
        Validates: Requirements 3.3
        """
        text = f"{document.get('title', '')} {document.get('text', '')}".lower()
        
        # Extract words (simple tokenization)
        words = re.findall(r'\b[a-z]{4,}\b', text)
        
        # Count word frequency
        word_freq = Counter(words)
        
        # Remove common stop words
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'will', 'your', 'they',
            'been', 'were', 'their', 'what', 'which', 'when', 'where', 'about'
        }
        word_freq = {word: count for word, count in word_freq.items() 
                     if word not in stop_words}
        
        # Match against categories
        topics = []
        for category, keywords in self.ticket_categories.items():
            # Count how many category keywords appear
            category_score = sum(word_freq.get(keyword, 0) for keyword in keywords)
            
            if category_score > 0:
                # Get top keywords for this category
                category_keywords = [
                    word for word in keywords 
                    if word in word_freq and word_freq[word] > 0
                ][:5]
                
                # Calculate confidence
                confidence = min(0.9, 0.4 + (category_score * 0.1))
                
                topics.append(Topic(
                    name=category,
                    keywords=category_keywords,
                    confidence=confidence
                ))
        
        # Sort by confidence
        topics.sort(key=lambda t: t.confidence, reverse=True)
        
        # Return top 3 topics
        return topics[:3]
    
    async def record_feedback(
        self,
        item_id: str,
        item_type: str,
        suggested_tags: List[str],
        accepted_tags: List[str],
        user_id: str,
        org_id: str
    ):
        """
        Record user feedback on auto-tagging suggestions.
        
        Stores feedback for future model improvement.
        
        Args:
            item_id: ID of the item (ticket, commit, doc)
            item_type: Type of item
            suggested_tags: Tags suggested by auto-tagger
            accepted_tags: Tags accepted by user
            user_id: User who provided feedback
            org_id: Organization ID
            
        Validates: Requirements 3.5
        """
        async with self.db.pool.acquire() as conn:
            # Store feedback
            await conn.execute("""
                INSERT INTO tagging_feedback (
                    item_id, item_type, suggested_tags, accepted_tags,
                    user_id, organization_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """, item_id, item_type, suggested_tags, accepted_tags, user_id, org_id)
    
    async def get_tagging_accuracy(
        self,
        org_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate auto-tagging accuracy based on user feedback.
        
        Args:
            org_id: Organization ID
            days: Days to look back
            
        Returns:
            Dict with accuracy metrics
        """
        async with self.db.pool.acquire() as conn:
            # Check if feedback table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'tagging_feedback'
                )
            """)
            
            if not table_exists:
                return {
                    "accuracy": 0.0,
                    "total_feedback": 0,
                    "message": "No feedback data available yet"
                }
            
            # Get feedback
            feedback = await conn.fetch("""
                SELECT suggested_tags, accepted_tags
                FROM tagging_feedback
                WHERE organization_id = $1
                AND created_at >= NOW() - INTERVAL '%s days'
            """, org_id, days)
            
            if not feedback:
                return {
                    "accuracy": 0.0,
                    "total_feedback": 0,
                    "message": "No feedback in the specified period"
                }
            
            # Calculate accuracy
            total_suggestions = 0
            correct_suggestions = 0
            
            for record in feedback:
                suggested = set(record['suggested_tags'] or [])
                accepted = set(record['accepted_tags'] or [])
                
                total_suggestions += len(suggested)
                correct_suggestions += len(suggested & accepted)
            
            accuracy = correct_suggestions / total_suggestions if total_suggestions > 0 else 0.0
            
            return {
                "accuracy": accuracy,
                "total_feedback": len(feedback),
                "total_suggestions": total_suggestions,
                "correct_suggestions": correct_suggestions,
                "period_days": days
            }
    
    async def bulk_tag_tickets(
        self,
        org_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk tag untagged tickets.
        
        Args:
            org_id: Organization ID
            limit: Maximum tickets to process
            
        Returns:
            Summary of tagging operation
        """
        async with self.db.pool.acquire() as conn:
            # Get untagged tickets
            tickets = await conn.fetch("""
                SELECT id, ticket_key, summary, description
                FROM jira_tickets
                WHERE organization_id = $1
                AND (labels IS NULL OR cardinality(labels) = 0)
                LIMIT $2
            """, org_id, limit)
            
            tagged_count = 0
            for ticket in tickets:
                tags = await self.tag_ticket(dict(ticket), org_id)
                
                if tags:
                    # Update ticket with tags
                    tag_names = [tag.name for tag in tags]
                    await conn.execute("""
                        UPDATE jira_tickets
                        SET labels = array_cat(COALESCE(labels, '{}'), $1::text[])
                        WHERE id = $2
                    """, tag_names, ticket['id'])
                    tagged_count += 1
            
            return {
                "tickets_processed": len(tickets),
                "tickets_tagged": tagged_count,
                "organization_id": org_id
            }
