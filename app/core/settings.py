from pydantic_settings import BaseSettings
from typing import Optional, List
import uuid
from pathlib import Path

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Collaborative AI Editor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment settings
    ENV: str = "development"
    DEBUG: bool = True
    
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
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Groq API settings
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama2-70b-3.3"  # or other available model
    GROQ_MAX_TOKENS: int = 500
    GROQ_TEMPERATURE: float = 0.1
    GROQ_REQUEST_TIMEOUT: float = 10.0
    
    # WebSocket settings
    WS_PING_INTERVAL: float = 30.0
    WS_PING_TIMEOUT: float = 10.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def validate_settings(self) -> None:
        """Validate critical settings"""
        if self.ENV == "production":
            assert len(self.SECRET_KEY) >= 32, "SECRET_KEY must be at least 32 characters in production"
            assert len(self.SESSION_SECRET) >= 32, "SESSION_SECRET must be at least 32 characters in production"
            assert self.GROQ_API_KEY, "GROQ_API_KEY must be set in production"
            assert "*" not in self.CORS_ORIGINS, "CORS_ORIGINS should be explicitly set in production"

# Create global settings object
settings = Settings()

# Ensure projects directory exists
settings.PROJECTS_DIR.mkdir(exist_ok=True)