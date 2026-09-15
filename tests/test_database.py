import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
from mongomock_motor import AsyncMongoMockClient
from fastapi.testclient import TestClient

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database.client import set_motor_client, get_database, close_motor_client
from app.database.connection import connect_to_mongo
from app.database.indexes import create_database_indexes
from app.repositories.review_repository import ReviewRepository
from app.repositories.finding_repository import FindingRepository
from app.repositories.agent_run_repository import AgentRunRepository
from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_mongo():
    """Fixture initializing in-memory AsyncMongoMockClient via mongomock_motor."""
    client = AsyncMongoMockClient()
    set_motor_client(client)
    yield client
    close_motor_client()


async def test_review_repository_crud(mock_mongo):
    """Test CRUD round-trips on ReviewRepository."""
    db = get_database()
    repo = ReviewRepository(db=db)

    # 1. Create
    review = await repo.create({
        "user_id": "user_123",
        "code": "def hello(): pass",
        "language": "python",
        "mode": "quick",
        "status": "pending"
    })
    assert review is not None
    assert "id" in review
    review_id = review["id"]

    # 2. Get by ID
    fetched = await repo.get_by_id(review_id)
    assert fetched is not None
    assert fetched["id"] == review_id
    assert fetched["language"] == "python"

    # 3. List
    reviews = await repo.list(filter_query={"user_id": "user_123"})
    assert len(reviews) == 1
    assert reviews[0]["id"] == review_id

    # 4. Update
    updated = await repo.update(review_id, {"status": "completed", "summary": "Looks good"})
    assert updated is not None
    assert updated["status"] == "completed"
    assert updated["summary"] == "Looks good"

    # 5. Delete
    deleted = await repo.delete(review_id)
    assert deleted is True
    assert await repo.get_by_id(review_id) is None


async def test_finding_repository_crud(mock_mongo):
    """Test CRUD round-trips on FindingRepository."""
    db = get_database()
    repo = FindingRepository(db=db)

    # 1. Create single finding
    finding = await repo.create({
        "review_id": "rev_999",
        "line": 10,
        "severity": "HIGH",
        "category": "BUG",
        "description": "Null pointer access",
        "suggestion": "Add null check"
    })
    assert finding is not None
    assert "id" in finding
    finding_id = finding["id"]

    # 2. Bulk create
    findings = await repo.create_many([
        {
            "review_id": "rev_999",
            "line": 15,
            "severity": "CRITICAL",
            "category": "SECURITY",
            "description": "SQL Injection",
            "suggestion": "Use parameterized query"
        },
        {
            "review_id": "rev_999",
            "line": 20,
            "severity": "LOW",
            "category": "STYLE",
            "description": "Unused variable",
            "suggestion": "Remove unused var"
        }
    ])
    assert len(findings) == 2

    # 3. List by review_id
    by_review = await repo.list_by_review_id("rev_999")
    assert len(by_review) == 3

    # 4. Get by ID
    single = await repo.get_by_id(finding_id)
    assert single["severity"] == "HIGH"

    # 5. Update
    updated = await repo.update(finding_id, {"severity": "CRITICAL"})
    assert updated["severity"] == "CRITICAL"

    # 6. Delete
    assert await repo.delete(finding_id) is True
    assert await repo.get_by_id(finding_id) is None


async def test_agent_run_repository_crud(mock_mongo):
    """Test CRUD round-trips on AgentRunRepository."""
    db = get_database()
    repo = AgentRunRepository(db=db)

    # 1. Create
    run_log = await repo.create({
        "review_id": "rev_100",
        "agent_name": "bug_agent",
        "status": "running",
        "tokens_used": 150
    })
    assert run_log is not None
    assert "id" in run_log
    run_id = run_log["id"]

    # 2. Get by ID & List
    fetched = await repo.get_by_id(run_id)
    assert fetched["agent_name"] == "bug_agent"

    runs_by_review = await repo.list_by_review_id("rev_100")
    assert len(runs_by_review) == 1

    # 3. Update & Delete
    updated = await repo.update(run_id, {"status": "success", "tokens_used": 200})
    assert updated["status"] == "success"

    assert await repo.delete(run_id) is True
    assert await repo.get_by_id(run_id) is None


async def test_index_creation(mock_mongo):
    """Test that index creation logic runs cleanly across collections."""
    db = get_database()
    created_indexes = await create_database_indexes(db=db)
    assert "users" in created_indexes
    assert "code_reviews" in created_indexes
    assert "review_findings" in created_indexes
    assert "agent_runs" in created_indexes


async def test_connection_failure_handling():
    """Test that connection failures do not crash application startup and return False cleanly."""
    with patch("app.database.connection.get_motor_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.admin.command.side_effect = Exception("Server selection timeout")
        mock_get_client.return_value = mock_client

        success = await connect_to_mongo(max_retries=2, initial_delay=0.01)
        assert success is False


async def test_health_check_endpoint_async(mock_mongo):
    """Test health check endpoint with mocked database."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "database" in json_data
