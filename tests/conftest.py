import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db import models, crud, schemas
from app.main import app

sys.path.append(os.path.abspath('./app'))

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create database tables
    models.Base.metadata.create_all(bind=engine)
    
    # Create test database session
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
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
            
    # Create test admin user
    admin_user = crud.create_user(
        test_db,
        schemas.UserCreate(username="admin", password="admin")
    )
    
    # Override the database dependency
    app.dependency_overrides = {
        "get_db": override_get_db
    }
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def authenticated_client(test_client):
    """Create an authenticated test client"""
    response = test_client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        allow_redirects=False
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