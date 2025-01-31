import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.models import Base

sys.path.append(os.path.abspath('./app'))

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test.db"):
            os.remove("./test.db")

@pytest.fixture
def test_app():
    from app.main import app
    return app

@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)

@pytest.fixture
def async_client(test_app):
    from httpx import AsyncClient
    return AsyncClient(app=test_app, base_url="http://test")