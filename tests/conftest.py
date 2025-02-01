import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.models import Base
from app.main import app, get_current_user
from datetime import datetime, timedelta
import jwt
from app.db import crud, models, schemas
from typing import Generator
import os

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "test_secret_key"
ALGORITHM = "HS256"

def create_test_user(db: sessionmaker, username: str, password: str) -> models.User:
    """Helper function to create a test user"""
    user_create = schemas.UserCreate(
        username=username,
        password=password
    )
    return crud.create_user(db, user_create)

def get_authenticated_client(client: TestClient, username: str) -> TestClient:
    """Helper function to create authenticated client"""
    access_token = jwt.encode(
        {
            "sub": username,
            "exp": datetime.utcnow() + timedelta(minutes=30)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator:
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
def creator_client(test_client, test_db):
    """Client for creating projects and files"""
    user = create_test_user(test_db, "creator", "creator_pass")
    return get_authenticated_client(test_client, user.username)

@pytest.fixture
def editor_client(test_client, test_db):
    """Client for editing files"""
    user = create_test_user(test_db, "editor", "editor_pass")
    return get_authenticated_client(test_client, user.username)

@pytest.fixture
def deleter_client(test_client, test_db):
    """Client for deleting projects and files"""
    user = create_test_user(test_db, "deleter", "deleter_pass")
    return get_authenticated_client(test_client, user.username)

@pytest.fixture
def validator_client(test_client, test_db):
    """Client for path validation tests"""
    user = create_test_user(test_db, "validator", "validator_pass")
    return get_authenticated_client(test_client, user.username)

@pytest.fixture
def test_project(creator_client):
    """Create a test project"""
    response = creator_client.post(
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
def test_file(creator_client, test_project):
    """Create a test file"""
    response = creator_client.post(
        "/api/create",
        json={
            "name": "test_file.txt",
            "type": "file",
            "path": f"/{test_project}"
        }
    )
    assert response.status_code == 200
    return f"{test_project}/test_file.txt"