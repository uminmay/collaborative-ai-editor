from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import bcrypt
import uuid
from datetime import datetime, timedelta
from .database import Base

# Project collaborators association table
project_collaborators = Table(
    'project_collaborators',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now())
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with owned projects
    owned_projects = relationship("Project", back_populates="owner")
    
    # Relationship with collaborative projects
    collaborative_projects = relationship(
        "Project",
        secondary=project_collaborators,
        back_populates="collaborators"
    )

    # Relationship with sessions and active editors
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    active_editors = relationship("ActiveEditor", back_populates="user", cascade="all, delete-orphan")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship with user
    user = relationship("User", back_populates="sessions")

    @classmethod
    def create_session_id(cls):
        return str(uuid.uuid4())

    @property
    def is_expired(self):
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

class ActiveEditor(Base):
    __tablename__ = "active_editors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship with user
    user = relationship("User", back_populates="active_editors")

    # Create index for faster lookups
    __table_args__ = (
        Index('idx_user_file', user_id, file_path, unique=True),
    )

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    path = Column(String, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with owner
    owner = relationship("User", back_populates="owned_projects")
    
    # Relationship with collaborators
    collaborators = relationship(
        "User",
        secondary=project_collaborators,
        back_populates="collaborative_projects"
    )