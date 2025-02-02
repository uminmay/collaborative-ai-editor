from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectCollaborator(BaseModel):
    user_id: int
    username: str
    added_at: datetime

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    path: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int
    owner: UserBase
    collaborators: List[UserBase]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CollaboratorUpdate(BaseModel):
    user_id: int
    action: str  # "add" or "remove"