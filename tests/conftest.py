import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.models import Base
from app.main import app, get_current_user
from datetime import datetime, timedelta
import jwt
from app.db import crud, models
from typing import Generator

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "test_secret_key"
ALGORITHM = "HS256"

# Override the get_current_user dependency for testing
async def override_get_current_user():
    """Override get_current_user for testing"""
    return models.User(
        id=1,
        username="testuser",
        password_hash="",
        is_admin=True
    )

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

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
def test_client(test_db):
    """Create test client"""
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    return client

@pytest.fixture
def authenticated_client(test_client, test_db):
    """Create authenticated test client"""
    # Create test user in database
    test_user = crud.create_user(
        test_db,
        models.User(
            username="testuser",
            password_hash=models.User.hash_password("testpass"),
            is_admin=True
        )
    )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = jwt.encode(
        {
            "sub": test_user.username,
            "exp": datetime.utcnow() + access_token_expires
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    # Set auth header
    test_client.headers["Authorization"] = f"Bearer {access_token}"
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