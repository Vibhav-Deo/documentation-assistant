"""
Pytest configuration and shared fixtures for all tests.

This module provides:
- Database fixtures for testing
- Mock services and clients
- Test data generators
- Async test support
"""

import pytest
import asyncio
import asyncpg
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock
import os

# Test database configuration
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
TEST_DB_PORT = int(os.getenv("TEST_DB_PORT", "5432"))
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "test_rag_db")
TEST_DB_USER = os.getenv("TEST_DB_USER", "postgres")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "postgres")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Create a test database connection pool.
    
    This fixture:
    1. Creates a connection pool to the test database
    2. Yields the pool for tests to use
    3. Closes the pool after all tests complete
    """
    pool = await asyncpg.create_pool(
        host=TEST_DB_HOST,
        port=TEST_DB_PORT,
        database=TEST_DB_NAME,
        user=TEST_DB_USER,
        password=TEST_DB_PASSWORD,
        min_size=2,
        max_size=10
    )
    
    yield pool
    
    await pool.close()


@pytest.fixture
async def db_connection(test_db_pool: asyncpg.Pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Provide a database connection with transaction rollback.
    
    Each test gets a fresh connection with a transaction that is
    rolled back after the test completes, ensuring test isolation.
    """
    async with test_db_pool.acquire() as conn:
        async with conn.transaction():
            yield conn
            # Transaction is automatically rolled back


@pytest.fixture
async def test_organization(db_connection: asyncpg.Connection) -> Dict[str, Any]:
    """Create a test organization."""
    org = await db_connection.fetchrow("""
        INSERT INTO organizations (name, plan, monthly_quota, quota_used)
        VALUES ($1, $2, $3, $4)
        RETURNING id, name, plan, monthly_quota, quota_used, created_at
    """, "Test Organization", "enterprise", 100000, 0)
    
    return dict(org)


@pytest.fixture
async def test_user(db_connection: asyncpg.Connection, test_organization: Dict) -> Dict[str, Any]:
    """Create a test user."""
    import bcrypt
    
    password_hash = bcrypt.hashpw("testpass123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = await db_connection.fetchrow("""
        INSERT INTO users (email, password_hash, name, organization_id, role)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, email, name, organization_id, role, created_at
    """, "test@example.com", password_hash, "Test User", test_organization['id'], "admin")
    
    return dict(user)


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing without actual LLM calls."""
    mock = Mock()
    mock.generate_response = Mock(return_value="This is a test AI response.")
    mock.build_prompt = Mock(return_value="Test prompt")
    mock.build_multi_source_prompt = Mock(return_value="Test multi-source prompt")
    return mock


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing without actual vector database."""
    mock = Mock()
    mock.search = Mock(return_value=[])
    mock.upsert = Mock(return_value=None)
    mock.create_collection = Mock(return_value=None)
    return mock


@pytest.fixture
def mock_embedder():
    """Mock sentence transformer for testing without actual embeddings."""
    mock = Mock()
    mock.encode = Mock(return_value=[0.1] * 384)  # 384-dimensional vector
    return mock


@pytest.fixture
async def sample_jira_ticket(db_connection: asyncpg.Connection, test_organization: Dict) -> Dict[str, Any]:
    """Create a sample Jira ticket for testing."""
    # First create a repository
    repo = await db_connection.fetchrow("""
        INSERT INTO repositories (repo_name, repo_url, organization_id)
        VALUES ($1, $2, $3)
        RETURNING id
    """, "test-repo", "https://github.com/test/repo", test_organization['id'])
    
    ticket = await db_connection.fetchrow("""
        INSERT INTO jira_tickets (
            ticket_key, summary, description, issue_type, status,
            priority, assignee, reporter, organization_id
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id, ticket_key, summary, description, issue_type, status,
                  priority, assignee, reporter, organization_id, created_date
    """, 
        "TEST-001",
        "Implement user authentication",
        "Add JWT-based authentication to the API",
        "Story",
        "In Progress",
        "High",
        "test@example.com",
        "manager@example.com",
        test_organization['id']
    )
    
    return dict(ticket)


@pytest.fixture
async def sample_commit(db_connection: asyncpg.Connection, test_organization: Dict, sample_jira_ticket: Dict) -> Dict[str, Any]:
    """Create a sample commit for testing."""
    # Get repository
    repo = await db_connection.fetchrow("""
        SELECT id FROM repositories WHERE organization_id = $1 LIMIT 1
    """, test_organization['id'])
    
    commit = await db_connection.fetchrow("""
        INSERT INTO commits (
            sha, message, author_name, author_email, commit_date,
            repository_id, organization_id, ticket_references, files_changed,
            additions, deletions
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id, sha, message, author_name, author_email, commit_date,
                  ticket_references, files_changed, additions, deletions
    """,
        "abc123def456",
        "feat: Add JWT authentication [TEST-001]",
        "Test Developer",
        "dev@example.com",
        "2024-01-15 10:00:00",
        repo['id'],
        test_organization['id'],
        [sample_jira_ticket['ticket_key']],
        ["api/auth.py", "api/models.py"],
        150,
        20
    )
    
    return dict(commit)


@pytest.fixture
def sample_decision_data() -> Dict[str, Any]:
    """Sample decision data for testing."""
    return {
        "ticket_key": "TEST-001",
        "decision_summary": "Use JWT for authentication",
        "problem_statement": "Need secure authentication mechanism",
        "alternatives_considered": [
            "Session-based authentication",
            "OAuth2 only",
            "JWT tokens"
        ],
        "chosen_approach": "JWT tokens with refresh mechanism",
        "constraints": ["Must work with mobile apps", "Need offline capability"],
        "risks": [
            {"risk": "Token theft", "mitigation": "Short expiry times"},
            {"risk": "Token bloat", "mitigation": "Minimal claims"}
        ],
        "stakeholders": ["Security Team", "Mobile Team", "Backend Team"]
    }


# Hypothesis strategies for property-based testing
from hypothesis import strategies as st

@pytest.fixture
def ticket_key_strategy():
    """Strategy for generating valid ticket keys."""
    return st.builds(
        lambda prefix, num: f"{prefix}-{num}",
        prefix=st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=2, max_size=5),
        num=st.integers(min_value=1, max_value=9999)
    )


@pytest.fixture
def file_path_strategy():
    """Strategy for generating valid file paths."""
    return st.builds(
        lambda parts: "/".join(parts),
        parts=st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
            min_size=1,
            max_size=5
        )
    )


@pytest.fixture
def confidence_score_strategy():
    """Strategy for generating valid confidence scores (0.0 to 1.0)."""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
