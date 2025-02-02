from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, Dict, Union
from pathlib import Path
import shutil
import logging

from ..db import crud, models, database
from ..core.security import get_current_user
from ..core.settings import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

def get_directory_structure(path: Path) -> Dict[str, Union[Dict, str]]:
    """Recursively build directory structure"""
    if path.is_file():
        return path.name
    
    result = {}
    for item in path.iterdir():
        if item.name.startswith('.'):
            continue
        if item.is_dir():
            result[item.name] = get_directory_structure(item)
        else:
            result[item.name] = str(item)
    return result

def validate_path(path: str) -> bool:
    """Validate path is safe and within project directory"""
    try:
        normalized_path = path.replace('\\', '/').lstrip('/')
        if '..' in normalized_path or '//' in normalized_path or '\\' in path:
            return False
        full_path = settings.PROJECTS_DIR / normalized_path
        return full_path.resolve().is_relative_to(settings.PROJECTS_DIR.resolve())
    except (ValueError, RuntimeError):
        return False

def get_project_root(path: str) -> str:
    """Get the root project name from a path"""
    parts = Path(path.lstrip('/')).parts
    return parts[0] if parts else None

@router.get("/", response_class=HTMLResponse)
async def get_home(
    request: Request,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Get projects based on user role
    if user.is_admin:
        projects = crud.get_projects(db)
    else:
        projects = crud.get_user_accessible_projects(db, user.id)
    
    # Get available users for collaborator selection
    available_users = []
    if user.is_admin or any(project.owner_id == user.id for project in projects):
        available_users = crud.get_users(db)
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": user,
            "projects": projects,
            "available_users": available_users
        }
    )

@router.get("/editor")
async def get_editor(
    request: Request,
    path: str,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        # Validate path
        if not validate_path(path):
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Check file exists
        full_path = settings.PROJECTS_DIR / path.lstrip('/')
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get project root and verify access
        project_name = get_project_root(path)
        if not project_name:
            raise HTTPException(status_code=400, detail="Invalid project path")
        
        project = crud.get_project(db, project_name)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if user has access to project
        if not user.is_admin and project.owner_id != user.id and user not in project.collaborators:
            raise HTTPException(status_code=403, detail="Not authorized to access this file")
        
        return templates.TemplateResponse(
            "editor.html",
            {"request": request, "path": path, "user": user}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Editor error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error accessing file")

@router.post("/api/create")
async def create_item(
    item: dict,
    db: Session = Depends(database.get_db),
    user: Optional[models.User] = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        name = item["name"].strip()
        path = item["path"].strip()
        item_type = item.get("type", "folder")  # Default to folder for new projects
        
        if not name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        
        if not validate_path(path):
            raise HTTPException(status_code=400, detail="Invalid path")

        # For root level projects
        if path == '/':
            full_path = settings.PROJECTS_DIR / name
            if full_path.exists():
                raise HTTPException(status_code=400, detail="Project already exists")

            # Create project in database first
            project = crud.create_project(
                db,
                name=name,
                path=name,
                owner_id=user.id
            )
            
            # Create directory after successful database entry
            full_path.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "project": project.name}
        
        # For items within projects
        else:
            project_name = get_project_root(path)
            if not project_name:
                raise HTTPException(status_code=400, detail="Invalid project path")

            # Verify project exists and check permissions
            project = crud.get_project(db, project_name)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Check if user has access
            if not user.is_admin and project.owner_id != user.id and user not in project.collaborators:
                raise HTTPException(status_code=403, detail="Not authorized to modify this project")

            # Create the new item
            new_path = settings.PROJECTS_DIR / path.lstrip('/') / name
            if new_path.exists():
                raise HTTPException(status_code=400, detail="Item already exists")

            if item_type == "folder":
                new_path.mkdir(parents=True, exist_ok=True)
            else:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.touch()

            return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create item error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/api/delete")
async def delete_item(
    item: dict,
    db: Session = Depends(database.get_db),
    user: Optional[models.User] = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        if not item["path"]:
            raise HTTPException(status_code=400, detail="Path cannot be empty")
        
        path = item["path"].replace('\\', '/')
        if not validate_path(path):
            raise HTTPException(status_code=400, detail="Invalid path")

        full_path = settings.PROJECTS_DIR / path.lstrip('/')
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")

        project_name = get_project_root(path)
        if not project_name:
            raise HTTPException(status_code=400, detail="Invalid project path")

        # Get the project and verify permissions
        project = crud.get_project(db, project_name)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if user has permission
        if not user.is_admin and project.owner_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this item")

        # Handle deletion based on item type
        if full_path.is_dir() and full_path.parent == settings.PROJECTS_DIR:
            # This is a project root - delete from database first
            if crud.delete_project(db, path=full_path.name):
                shutil.rmtree(full_path)
            else:
                raise HTTPException(status_code=500, detail="Failed to delete project from database")
        else:
            # This is a file or subfolder
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()

        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete item error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

# API endpoint to get project structure
@router.get("/api/structure")
async def get_structure(
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # If admin, show all projects
        if user.is_admin:
            return get_directory_structure(settings.PROJECTS_DIR)
        
        # For regular users, filter only accessible projects
        projects = crud.get_user_accessible_projects(db, user.id)
        structure = {}
        
        # Build structure only for accessible projects
        for project in projects:
            project_path = settings.PROJECTS_DIR / project.path
            if project_path.exists():
                structure[project.path] = get_directory_structure(project_path)
        
        return structure
    
    except Exception as e:
        logger.error(f"Error getting structure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get directory structure")