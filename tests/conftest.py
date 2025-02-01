import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.models import Base
from app.main import app
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
import jwt

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "test_secret_key"
ALGORITHM = "HS256"

def create_test_token():
    """Create a test JWT token"""
    access_token_expires = timedelta(minutes=30)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {"exp": expire, "sub": "testuser"}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    token = create_test_token()
    test_client.headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
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
    os.makedirs("editor_files", exist_ok=True)