from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from typing import Optional

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = models.User.hash_password(user.password)
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        is_admin=True  # Since we're only creating admin users
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if user and user.verify_password(password):
        return user
    return None

# Existing project operations
def create_project(db: Session, name: str, path: str):
    db_project = models.Project(name=name, path=path)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, path: str):
    project = db.query(models.Project).filter(models.Project.path == path).first()
    if project:
        db.delete(project)
        db.commit()
    return project

def get_project(db: Session, path: str):
    return db.query(models.Project).filter(models.Project.path == path).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()