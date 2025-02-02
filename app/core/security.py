from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Request, Depends
from sqlalchemy.orm import Session

from ..db import crud, models, database
from .settings import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    request: Request,
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    """Get current user from session or JWT token"""
    # First check session
    session = request.session
    username = session.get("user")
    if username:
        return crud.get_user_by_username(db, username)
    
    # Then check bearer token
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            if username:
                return crud.get_user_by_username(db, username)
        except JWTError:
            return None
    
    return None