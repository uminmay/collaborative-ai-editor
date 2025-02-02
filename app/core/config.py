import os
from pathlib import Path
from typing import List
import logging
from logging.config import dictConfig
import uuid

# Project settings
PROJECTS_DIR = Path("editor_files")
PROJECTS_DIR.mkdir(exist_ok=True)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", str(uuid.uuid4()))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Session settings
SESSION_SECRET = str(uuid.uuid4())

# Logging configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "app.log"
        }
    },
    "root": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "handlers": ["console", "file"]
    }
}

# Initialize logging
dictConfig(logging_config)
logger = logging.getLogger(__name__)