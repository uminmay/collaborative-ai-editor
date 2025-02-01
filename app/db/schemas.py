from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class LoginForm(BaseModel):
    username: str
    password: str

class ProjectBase(BaseModel):
    name: str
    path: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True