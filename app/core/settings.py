from pydantic_settings import BaseSettings
from typing import List
import uuid
from pathlib import Path

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Collaborative AI Editor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Path settings
    PROJECTS_DIR: Path = Path("editor_files")
    
    # Security settings
    SECRET_KEY: str = str(uuid.uuid4())
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SESSION_SECRET: str = str(uuid.uuid4())
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Environment settings
    ENV: str = "development"  # development, test, production
    DEBUG: bool = True
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings object
settings = Settings()

# Ensure projects directory exists
settings.PROJECTS_DIR.mkdir(exist_ok=True)