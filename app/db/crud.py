from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.sql import expression
from datetime import datetime, timedelta
from typing import Optional, List
from . import models, schemas
import logging

logger = logging.getLogger(__name__)

# User Management Functions
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

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get all users"""
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if user and user.verify_password(password):
        return user
    return None

def get_user_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get projects owned by a specific user"""
    return db.query(models.Project).filter(
        models.Project.owner_id == user_id
    ).offset(skip).limit(limit).all()

def transfer_project_ownership(db: Session, project_id: int, new_owner_id: int) -> bool:
    """Transfer project ownership to another user"""
    project = get_project_by_id(db, project_id)
    new_owner = get_user_by_id(db, new_owner_id)
    
    if not project or not new_owner:
        return False
        
    project.owner_id = new_owner_id
    db.commit()
    return True

# Session Management Functions
def create_user_session(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    expires_in: int = 30
) -> models.UserSession:
    """Create a new user session"""
    session = models.UserSession(
        session_id=models.UserSession.create_session_id(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now() + timedelta(minutes=expires_in)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_session(db: Session, session_id: str) -> Optional[models.UserSession]:
    """Get session by session ID"""
    return db.query(models.UserSession).filter(
        models.UserSession.session_id == session_id,
        models.UserSession.expires_at > datetime.now()
    ).first()

def update_session_activity(db: Session, session_id: str) -> bool:
    """Update session last activity timestamp"""
    session = get_session(db, session_id)
    if session:
        session.last_activity = datetime.now()
        db.commit()
        return True
    return False

def delete_session(db: Session, session_id: str) -> bool:
    """Delete a session"""
    session = get_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False

def cleanup_expired_sessions(db: Session) -> int:
    """Remove expired sessions"""
    result = db.query(models.UserSession).filter(
        models.UserSession.expires_at <= datetime.now()
    ).delete()
    db.commit()
    return result

# Active Editor Functions
def track_editor_activity(db: Session, user_id: int, file_path: str) -> models.ActiveEditor:
    """Create or update active editor entry"""
    try:
        # Check for existing entry
        editor = db.query(models.ActiveEditor).filter(
            and_(
                models.ActiveEditor.user_id == user_id,
                models.ActiveEditor.file_path == file_path
            )
        ).first()
        
        current_time = datetime.now()
        
        if editor:
            # Update existing entry
            editor.last_activity = current_time
        else:
            # Create new entry
            editor = models.ActiveEditor(
                user_id=user_id,
                file_path=file_path,
                opened_at=current_time,
                last_activity=current_time
            )
            db.add(editor)
        
        db.commit()
        db.refresh(editor)
        return editor
        
    except Exception as e:
        logger.error(f"Error tracking editor activity: {e}")
        db.rollback()
        raise

def get_active_editors(db: Session, file_path: str) -> list[models.ActiveEditor]:
    """Get all active editors for a file"""
    try:
        # Consider editors inactive after 5 minutes of no activity
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        return db.query(models.ActiveEditor).filter(
            and_(
                models.ActiveEditor.file_path == file_path,
                models.ActiveEditor.last_activity >= cutoff_time
            )
        ).all()
        
    except Exception as e:
        logger.error(f"Error getting active editors: {e}")
        return []

def get_active_editors_for_user(db: Session, user_id: int) -> list[models.ActiveEditor]:
    """Get all active editing sessions for a user"""
    try:
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        return db.query(models.ActiveEditor).filter(
            and_(
                models.ActiveEditor.user_id == user_id,
                models.ActiveEditor.last_activity >= cutoff_time
            )
        ).all()
        
    except Exception as e:
        logger.error(f"Error getting user's active editors: {e}")
        return []

def remove_editor_activity(db: Session, user_id: int, file_path: str) -> bool:
    """Remove active editor entry"""
    try:
        result = db.query(models.ActiveEditor).filter(
            and_(
                models.ActiveEditor.user_id == user_id,
                models.ActiveEditor.file_path == file_path
            )
        ).delete()
        
        db.commit()
        return result > 0
        
    except Exception as e:
        logger.error(f"Error removing editor activity: {e}")
        db.rollback()
        return False

def cleanup_inactive_editors(db: Session) -> int:
    """Remove all inactive editor entries"""
    try:
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        result = db.query(models.ActiveEditor).filter(
            models.ActiveEditor.last_activity < cutoff_time
        ).delete()
        
        db.commit()
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up inactive editors: {e}")
        db.rollback()
        return 0

def get_editor_stats(db: Session, file_path: str) -> dict:
    """Get statistics about editor activity for a file"""
    try:
        # Get current active editors
        active_editors = get_active_editors(db, file_path)
        
        # Get total edit time and session count
        stats = db.query(
            func.count(models.ActiveEditor.id).label('total_sessions'),
            func.sum(
                func.extract('epoch', models.ActiveEditor.last_activity) - 
                func.extract('epoch', models.ActiveEditor.opened_at)
            ).label('total_edit_time')
        ).filter(
            models.ActiveEditor.file_path == file_path
        ).first()
        
        return {
            'current_active_users': len(active_editors),
            'total_sessions': stats.total_sessions if stats else 0,
            'total_edit_time': int(stats.total_edit_time or 0),
            'active_users': [
                {
                    'username': editor.user.username,
                    'opened_at': editor.opened_at,
                    'last_activity': editor.last_activity
                }
                for editor in active_editors
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting editor stats: {e}")
        return {
            'current_active_users': 0,
            'total_sessions': 0,
            'total_edit_time': 0,
            'active_users': []
        }

# Project Management Functions
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

def get_project(db: Session, path: str) -> Optional[models.Project]:
    """Get project by path"""
    return db.query(models.Project).filter(models.Project.path == path).first()

def get_project_by_id(db: Session, project_id: int) -> Optional[models.Project]:
    """Get project by ID"""
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    """Get all projects"""
    return db.query(models.Project).order_by(models.Project.created_at.desc()).offset(skip).limit(limit).all()

def get_user_accessible_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all projects accessible by user (owned or collaborative)"""
    return db.query(models.Project).filter(
        or_(
            models.Project.owner_id == user_id,
            models.Project.collaborators.any(id=user_id)
        )
    ).order_by(models.Project.created_at.desc()).offset(skip).limit(limit).all()

def delete_project(db: Session, path: str) -> bool:
    """Delete a project"""
    project = db.query(models.Project).filter(models.Project.path == path).first()
    if project:
        db.delete(project)
        db.commit()
        return True
    return False

# Collaborator Management
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

def check_project_access(db: Session, project_id: int, user_id: int) -> bool:
    """Check if user has access to project"""
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