import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.models import Base
from app.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def authenticated_client(test_client):
    """Create authenticated test client"""
    # For now, we'll just return the regular client since auth isn't implemented yet
    return test_client

@pytest.fixture
def test_project(authenticated_client):
    """Create a test project"""
    response = authenticated_client.post(
        "/api/create",
        json={
            "name": "test_project",
            "type": "folder",
            "path": "/"
        }
    )
    assert response.status_code == 200
    return "test_project"

@pytest.fixture
def test_file(authenticated_client, test_project):
    """Create a test file"""
    response = authenticated_client.post(
        "/api/create",
        json={
            "name": "test_file.txt",
            "type": "file",
            "path": f"/{test_project}"
        }
    )
    assert response.status_code == 200
    return f"{test_project}/test_file.txt"

def setup_test_environment():
    """Setup test environment"""
    # Create test directory
    os.makedirs("editor_files", exist_ok=True)