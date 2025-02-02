from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from typing import Optional
from pathlib import Path

def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False) -> models.User:
    """Create a new user"""
    hashed_password = models.User.hash_password(user.password)
    db_user = models.User(
        username=user.username,
        password_hash=hashed_password,
        is_admin=is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    """Get all users"""
    return db.query(models.User).offset(skip).limit(limit).all()

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if user and user.verify_password(password):
        return user
    return None

def create_project(db: Session, name: str, path: str, creator_id: int) -> models.Project:
    """Create a new project in database"""
    db_project = models.Project(
        name=name,
        path=path,
        creator_id=creator_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, path: str) -> bool:
    """Delete a project"""
    project = db.query(models.Project).filter(models.Project.path == path).first()
    if project:
        db.delete(project)
        db.commit()
        return True
    return False

def get_project(db: Session, path: str) -> Optional[models.Project]:
    """Get project by path"""
    return db.query(models.Project).filter(models.Project.path == path).first()

def get_project_by_id(db: Session, project_id: int) -> Optional[models.Project]:
    """Get project by ID"""
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    """Get all projects"""
    return db.query(models.Project).offset(skip).limit(limit).all()

def get_user_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get projects created by a specific user"""
    return db.query(models.Project).filter(
        models.Project.creator_id == user_id
    ).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user"""
    user = get_user_by_id(db, user_id)
    if user and user.username != "admin":
        db.delete(user)
        db.commit()
        return True
    return False

def update_user_role(db: Session, user_id: int, is_admin: bool) -> Optional[models.User]:
    """Update user role"""
    user = get_user_by_id(db, user_id)
    if user and user.username != "admin":
        user.is_admin = is_admin
        db.commit()
        db.refresh(user)
    return user