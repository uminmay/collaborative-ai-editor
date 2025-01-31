import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import models
import os

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    models.Base.metadata.create_all(bind=engine)
    yield engine
    models.Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def test_db(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_create_project(test_db):
    project = models.Project(name="test_project", path="/test_project")
    test_db.add(project)
    test_db.commit()
    assert project.id is not None
    assert project.name == "test_project"

def test_get_project(test_db):
    project = models.Project(name="test_project", path="/test_project")
    test_db.add(project)
    test_db.commit()
    
    saved_project = test_db.query(models.Project).filter_by(path="/test_project").first()
    assert saved_project is not None
    assert saved_project.name == project.name

def test_delete_project(test_db):
    project = models.Project(name="test_project", path="/test_project")
    test_db.add(project)
    test_db.flush()
    test_db.commit()
    
    # Get fresh instance
    project_id = project.id
    test_db.expunge_all()
    
    # Delete
    project_to_delete = test_db.query(models.Project).get(project_id)
    test_db.delete(project_to_delete)
    test_db.commit()
    test_db.expire_all()
    
    # Verify deletion
    saved_project = test_db.query(models.Project).filter_by(id=project_id).first()
    assert saved_project is None