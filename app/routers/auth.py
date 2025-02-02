from fastapi import APIRouter, Depends, Request, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta

from ..db import crud, database
from ..core.security import create_access_token
from ..core.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(database.get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    user = crud.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )
    
    # Create session
    request.session["user"] = user.username
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Redirect based on user role
    redirect_url = "/admin" if user.is_admin else "/"
    response = RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_302_FOUND
    )
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite='lax',
        max_age=1800
    )
    return response

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response