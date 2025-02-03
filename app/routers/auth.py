from fastapi import APIRouter, Depends, Request, status, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..db import crud, database
from ..core.security import create_access_token
from ..core.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": request.session.pop("error", None)
        }
    )

@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(database.get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        # Authenticate user
        user = crud.authenticate_user(db, username, password)
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Invalid username or password"
                }
            )

        # Create database session
        session = crud.create_user_session(
            db=db,
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "session": session.session_id},
            expires_delta=access_token_expires
        )

        # Create response
        redirect_url = "/admin" if user.is_admin else "/"
        response = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND
        )

        # Set session cookie and token
        request.session["user"] = user.username
        request.session["session_id"] = session.session_id
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            samesite='lax',
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        return response

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "An error occurred during login"
            }
        )

@router.get("/logout")
async def logout(
    request: Request,
    db: Session = Depends(database.get_db)
):
    try:
        # Delete database session if exists
        session_id = request.session.get("session_id")
        if session_id:
            crud.delete_session(db, session_id)

        # Clear session and cookies
        request.session.clear()
        response = RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND
        )
        response.delete_cookie("access_token")
        
        return response

    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        request.session["error"] = "An error occurred during logout"
        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_302_FOUND
        )

@router.get("/api/session")
async def get_session_info(
    request: Request,
    db: Session = Depends(database.get_db)
):
    """Get current session information"""
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active session"
            )

        session = crud.get_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        # Update session activity
        crud.update_session_activity(db, session_id)

        # Get user's active editors
        active_editors = crud.get_active_editors_for_user(db, session.user_id)
        
        return {
            "session_id": session_id,
            "user": {
                "id": session.user.id,
                "username": session.user.username,
                "is_admin": session.user.is_admin
            },
            "active_editors": [editor.file_path for editor in active_editors],
            "expires_at": session.expires_at,
            "last_activity": session.last_activity
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session info error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )