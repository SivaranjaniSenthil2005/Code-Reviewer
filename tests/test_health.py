import sys
import os
from fastapi.testclient import TestClient

# Ensure backend package is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

client = TestClient(app)


def test_health_check_root():
    """Smoke test for the root /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "database" in json_data


def test_health_check_v1():
    """Smoke test for the /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "database" in json_data
