"""
pytest fixtures — sets up a fresh in-memory SQLite DB for each test session.
The CI pipeline overrides DATABASE_URL with a real PostgreSQL service container.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.main import get_db

import os

# Use SQLite for local test runs; CI overrides with PostgreSQL
TEST_DB_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

connect_args = {"check_same_thread": False} if TEST_DB_URL.startswith("sqlite") else {}
engine = create_engine(TEST_DB_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
