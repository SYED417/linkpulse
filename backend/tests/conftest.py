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

from app.db.database import Base, engine, SessionLocal
from app import models  # noqa: F401  (registers all models)
from main import app


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_id():
    """Insert a fresh user and return its id (unique email per test)."""
    db = SessionLocal()
    try:
        user = models.User(
            email=f"test-{uuid.uuid4()}@example.com",
            password_hash="not-a-real-hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return str(user.id)
    finally:
        db.close()
