from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
from ipaddress import IPv4Address, IPv6Address

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

class UserSessionBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UserSessionCreate(UserSessionBase):
    user_id: int

class UserSession(UserSessionBase):
    id: int
    session_id: str
    user_id: int
    expires_at: datetime
    created_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True

class ActiveEditorBase(BaseModel):
    file_path: str

class ActiveEditorCreate(ActiveEditorBase):
    user_id: int

class ActiveEditor(ActiveEditorBase):
    id: int
    user_id: int
    opened_at: datetime
    last_activity: datetime

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

class SessionInfo(BaseModel):
    session_id: str
    active_editors: Optional[List[str]] = None
    last_activity: datetime