from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import Request, Depends, HTTPException, status, WebSocket
from sqlalchemy.orm import Session
import logging

from ..db import crud, models, database
from .settings import settings

logger = logging.getLogger(__name__)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_session_user(
    request_or_websocket: Union[Request, WebSocket],
    db: Session,
    require_active: bool = True
) -> Optional[tuple[models.User, models.UserSession]]:
    """Get user and session from request or websocket"""
    try:
        # Get session ID from cookie session
        session_store = (
            request_or_websocket.session
            if isinstance(request_or_websocket, Request)
            else request_or_websocket.session
        )
        session_id = session_store.get("session_id")
        
        if session_id:
            db_session = crud.get_session(db, session_id)
            if db_session and (not require_active or not db_session.is_expired):
                if require_active:
                    crud.update_session_activity(db, session_id)
                return db_session.user, db_session
        
        # Try bearer token if no valid session found
        auth = None
        if isinstance(request_or_websocket, Request):
            auth = request_or_websocket.headers.get("Authorization")
        elif isinstance(request_or_websocket, WebSocket):
            # For WebSocket, check the token from query parameters
            token = request_or_websocket.query_params.get("token")
            if token:
                auth = f"Bearer {token}"
        
        if auth and auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM]
                )
                username = payload.get("sub")
                session_id = payload.get("session")
                
                if username and session_id:
                    db_session = crud.get_session(db, session_id)
                    if db_session and (not require_active or not db_session.is_expired):
                        if require_active:
                            crud.update_session_activity(db, session_id)
                        return db_session.user, db_session
            except JWTError as e:
                logger.warning(f"JWT validation failed: {e}")
                pass
        
        return None

    except Exception as e:
        logger.error(f"Error in get_session_user: {e}", exc_info=True)
        return None

async def get_current_user(
    request: Request,
    db: Session = Depends(database.get_db)
) -> models.User:
    """Dependency for getting current user from request"""
    result = await get_session_user(request, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result[0]

async def get_current_active_user(
    request: Request,
    db: Session = Depends(database.get_db)
) -> models.User:
    """Dependency for getting current user with active session check"""
    result = await get_session_user(request, db, require_active=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result[0]

async def get_optional_user(
    request: Request,
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    """Dependency for getting optional user from request"""
    result = await get_session_user(request, db, require_active=False)
    return result[0] if result else None

def validate_admin(user: models.User) -> bool:
    """Validate if user is admin"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return True

async def get_current_admin(
    user: models.User = Depends(get_current_active_user)
) -> models.User:
    """Dependency for getting current admin user"""
    validate_admin(user)
    return user

def create_session_token(
    user: models.User,
    session: models.UserSession,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new session token"""
    return create_access_token(
        data={
            "sub": user.username,
            "session": session.session_id
        },
        expires_delta=expires_delta
    )