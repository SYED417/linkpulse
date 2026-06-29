import os
import uuid

# Point at a test database BEFORE importing the app (database.py reads this
# at import time). Falls back to a local test DB if not set by CI.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/linkpulse_test",
)

import pytest
from fastapi.testclient import TestClient

from app.db.database import Base, engine
from app import models  # noqa: F401  (registers all models)
from main import app


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    """Unauthenticated client (for public endpoints)."""
    return TestClient(app)


@pytest.fixture
def auth_client():
    """Client authenticated as a freshly-registered user (Bearer token set)."""
    c = TestClient(app)
    email = f"test-{uuid.uuid4().hex[:10]}@example.com"
    password = "Sup3rSecret!"
    reg = c.post("/api/register", json={"email": email, "password": password})
    assert reg.status_code == 201, reg.text
    tok = c.post("/api/token", data={"username": email, "password": password})
    assert tok.status_code == 200, tok.text
    c.headers.update({"Authorization": f"Bearer {tok.json()['access_token']}"})
    return c
