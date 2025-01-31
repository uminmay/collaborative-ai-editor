# tests/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db import crud, models
from app.main import app
from fastapi.testclient import TestClient
import os

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    # Create test database
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create test session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test.db"):
            os.remove("./test.db")

def test_create_project(test_db):
    project = crud.create_project(test_db, name="test_project", path="/test_project")
    assert project.name == "test_project"
    assert project.path == "/test_project"

def test_get_project(test_db):
    project = crud.create_project(test_db, name="test_project", path="/test_project")
    fetched_project = crud.get_project(test_db, path="/test_project")
    assert fetched_project.name == project.name
    assert fetched_project.project_id == project.project_id

def test_delete_project(test_db):
    project = crud.create_project(test_db, name="test_project", path="/test_project")
    deleted_project = crud.delete_project(test_db, path="/test_project")
    assert deleted_project.id == project.id
    fetched_project = crud.get_project(test_db, path="/test_project")
    assert fetched_project is None