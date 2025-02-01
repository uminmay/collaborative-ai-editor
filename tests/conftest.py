import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator
from app.main import app
from app.db import models, crud, schemas, database

# Add app directory to Python path
sys.path.append(os.path.abspath('./app'))

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test database engine
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create test SessionLocal class
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db() -> Generator:
    """Override the database dependency"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    # Create tables
    models.Base.metadata.create_all(bind=engine)
    
    # Get test database session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up
        models.Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test.db"):
            os.remove("./test.db")

@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client with a fresh database"""
    try:
        # Override the database dependency
        app.dependency_overrides[database.get_db] = lambda: test_db
        
        # Create test admin user
        admin_user = crud.create_user(
            test_db,
            schemas.UserCreate(username="admin", password="admin")
        )
        
        with TestClient(app) as client:
            yield client
    finally:
        # Clean up
        app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def authenticated_client(test_client):
    """Create an authenticated test client"""
    response = test_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False
    )
    assert response.status_code == 302
    return test_client

@pytest.fixture(scope="function")
def test_project(authenticated_client, test_db):
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

@pytest.fixture(scope="function")
def test_file(authenticated_client, test_project):
    """Create a test file within the test project"""
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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Create editor_files directory if it doesn't exist
    os.makedirs("editor_files", exist_ok=True)
    
    yield
    
    # Cleanup after test
    if os.path.exists("editor_files"):
        import shutil
        shutil.rmtree("editor_files")