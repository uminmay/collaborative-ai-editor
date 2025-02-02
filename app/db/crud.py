from sqlalchemy.orm import Session
from sqlalchemy import or_
from . import models, schemas
from datetime import datetime
from typing import Optional, List
from pathlib import Path

def create_project(db: Session, name: str, path: str, owner_id: int) -> models.Project:
    """Create a new project in database"""
    db_project = models.Project(
        name=name,
        path=path,
        owner_id=owner_id
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

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    """Get all projects"""
    return db.query(models.Project).order_by(models.Project.created_at.desc()).offset(skip).limit(limit).all()


def get_project_by_id(db: Session, project_id: int) -> Optional[models.Project]:
    """Get project by ID"""
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_user_accessible_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all projects accessible by user (owned or collaborative)"""
    return db.query(models.Project).filter(
        or_(
            models.Project.owner_id == user_id,
            models.Project.collaborators.any(id=user_id)
        )
    ).order_by(models.Project.created_at.desc()).offset(skip).limit(limit).all()

def get_user_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get projects owned by a specific user"""
    return db.query(models.Project).filter(
        models.Project.owner_id == user_id
    ).offset(skip).limit(limit).all()

def add_project_collaborator(db: Session, project_id: int, user_id: int) -> bool:
    """Add a collaborator to a project"""
    project = get_project_by_id(db, project_id)
    user = get_user_by_id(db, user_id)
    
    if not project or not user:
        return False
        
    if user not in project.collaborators:
        project.collaborators.append(user)
        db.commit()
    return True

def remove_project_collaborator(db: Session, project_id: int, user_id: int) -> bool:
    """Remove a collaborator from a project"""
    project = get_project_by_id(db, project_id)
    user = get_user_by_id(db, user_id)
    
    if not project or not user:
        return False
        
    if user in project.collaborators:
        project.collaborators.remove(user)
        db.commit()
    return True

def transfer_project_ownership(db: Session, project_id: int, new_owner_id: int) -> bool:
    """Transfer project ownership to another user"""
    project = get_project_by_id(db, project_id)
    new_owner = get_user_by_id(db, new_owner_id)
    
    if not project or not new_owner:
        return False
        
    project.owner_id = new_owner_id
    db.commit()
    return True

def check_project_access(db: Session, project_id: int, user_id: int) -> bool:
    """Check if user has access to project (owner, collaborator, or admin)"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
        
    if user.is_admin:
        return True
        
    project = get_project_by_id(db, project_id)
    if not project:
        return False
        
    return (project.owner_id == user_id or 
            user_id in [c.id for c in project.collaborators])

# User management functions
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

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get all users"""
    return db.query(models.User).offset(skip).limit(limit).all()

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if user and user.verify_password(password):
        return user
    return None