from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from ..db import crud, models, database, schemas
from ..core.security import get_current_user

router = APIRouter(prefix="/api/projects")

@router.get("/{project_id}/collaborators")
async def get_collaborators(
    project_id: int,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get project collaborators"""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to view collaborators
    if not user.is_admin and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "collaborators": [
            {
                "user_id": collaborator.id,
                "username": collaborator.username
            }
            for collaborator in project.collaborators
        ]
    }

@router.post("/{project_id}/collaborators")
async def update_collaborators(
    project_id: int,
    update: schemas.CollaboratorUpdate,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Add or remove project collaborator"""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has permission to modify collaborators
    if not user.is_admin and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get target user
    target_user = crud.get_user_by_id(db, update.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Can't modify project owner's access
    if target_user.id == project.owner_id:
        raise HTTPException(status_code=400, detail="Cannot modify owner's access")
    
    if update.action == "add":
        if crud.add_project_collaborator(db, project_id, update.user_id):
            return {"status": "success", "message": "Collaborator added"}
    elif update.action == "remove":
        if crud.remove_project_collaborator(db, project_id, update.user_id):
            return {"status": "success", "message": "Collaborator removed"}
    
    raise HTTPException(status_code=400, detail="Failed to update collaborators")

@router.post("/{project_id}/transfer")
async def transfer_ownership(
    project_id: int,
    transfer: dict,
    user: Optional[models.User] = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Transfer project ownership"""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Only admin can transfer ownership
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_owner_id = transfer.get("new_owner_id")
    if not new_owner_id:
        raise HTTPException(status_code=400, detail="New owner ID is required")
    
    # Get new owner
    new_owner = crud.get_user_by_id(db, new_owner_id)
    if not new_owner:
        raise HTTPException(status_code=404, detail="New owner not found")
    
    if crud.transfer_project_ownership(db, project_id, new_owner_id):
        return {"status": "success", "message": "Ownership transferred"}
    
    raise HTTPException(status_code=400, detail="Failed to transfer ownership")