from fastapi import APIRouter, Depends, Request, status, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import secrets
import string

from ..db import crud, models, database
from ..db.schemas import UserCreate
from ..core.security import get_current_user

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@router.get("")
@router.get("/")
async def admin_dashboard(
    request: Request,
    user: Optional[models.User] = Depends(get_current_user)
):
    if not user or not user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

@router.get("/project-management")
async def project_management(
    request: Request,
    user: Optional[models.User] = Depends(get_current_user)
):
    if not user or not user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/user-management")
async def user_management(
    request: Request,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user or not user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    users = crud.get_users(db)
    return templates.TemplateResponse(
        "user-management.html",
        {
            "request": request,
            "users": users,
            "message": request.session.pop("message", None),
            "error": request.session.pop("error", None)
        }
    )

@router.post("/create-user")
async def create_user(
    request: Request,
    username: str = Form(...),
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user or not user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    try:
        # Check if username already exists
        if crud.get_user_by_username(db, username):
            request.session["error"] = f"Username {username} already exists"
            return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)
        
        # Generate random password
        password = generate_password()
        
        # Create user
        new_user = UserCreate(
            username=username,
            password=password
        )
        crud.create_user(db, new_user)
        
        # Store success message with password
        request.session["message"] = f"User created successfully. Username: {username}, Password: {password}"
        
    except Exception as e:
        request.session["error"] = f"Error creating user: {str(e)}"
    
    return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)

@router.post("/delete-user/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user or not user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    try:
        delete_user = crud.get_user_by_id(db, user_id)
        if not delete_user:
            request.session["error"] = "User not found"
            return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)
        
        if delete_user.username == "admin":
            request.session["error"] = "Cannot delete admin user"
            return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)
            
        crud.delete_user(db, user_id)
        request.session["message"] = "User deleted successfully"
    except Exception as e:
        request.session["error"] = f"Error deleting user: {str(e)}"
    
    return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)

@router.post("/update-role/{user_id}")
async def update_role(
    request: Request,
    user_id: int,
    role: str = Form(...),
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user or not user.is_admin:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    try:
        update_user = crud.get_user_by_id(db, user_id)
        if not update_user:
            request.session["error"] = "User not found"
            return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)
        
        if update_user.username == "admin":
            request.session["error"] = "Cannot change admin role"
            return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)
            
        crud.update_user_role(db, user_id, role == "admin")
        request.session["message"] = "User role updated successfully"
    except Exception as e:
        request.session["error"] = f"Error updating role: {str(e)}"
    
    return RedirectResponse(url="/admin/user-management", status_code=status.HTTP_302_FOUND)