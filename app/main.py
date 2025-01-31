from fastapi import FastAPI, WebSocket, Request, HTTPException, Depends
from starlette.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import json
from pathlib import Path
import shutil
from typing import Optional, Dict, Union
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.config import dictConfig
from sqlalchemy.orm import Session
from app.db import models, crud, database

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

dictConfig(logging_config)
logger = logging.getLogger(__name__)

app = FastAPI(title="Collaborative AI Editor")

# Database setup
models.Base.metadata.create_all(bind=database.engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Error handling request: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": str(exc), "detail": str(exc.__class__.__name__)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create projects directory
PROJECTS_DIR = Path("editor_files")
PROJECTS_DIR.mkdir(exist_ok=True)

# Pydantic models
class CreateItem(BaseModel):
    name: str
    type: str
    path: str

class DeleteItem(BaseModel):
    path: str

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
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
        full_path = PROJECTS_DIR / path.lstrip('/')
        return full_path.resolve().is_relative_to(PROJECTS_DIR.resolve())
    except (ValueError, RuntimeError):
        return False

# API endpoints
@app.get("/api/structure")
async def get_structure():
    """Get the entire project structure"""
    try:
        return get_directory_structure(PROJECTS_DIR)
    except Exception as e:
        logger.error(f"Error getting structure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get directory structure")

@app.post("/api/create")
async def create_item(item: CreateItem, db: Session = Depends(get_db)):
    """Create a new file or folder"""
    try:
        if not validate_path(item.path):
            raise HTTPException(status_code=400, detail="Invalid path")
        
        if item.type not in ['file', 'folder']:
            raise HTTPException(status_code=400, detail="Invalid item type")
            
        full_path = PROJECTS_DIR / item.path.lstrip('/')
        new_path = full_path / item.name if item.path != '/' else PROJECTS_DIR / item.name
        
        if item.type == 'folder':
            new_path.mkdir(parents=True, exist_ok=True)
            if item.path == '/':
                crud.create_project(db, name=item.name, path=str(new_path))
        else:
            new_path.touch()
        return {"status": "success"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Create item error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/delete")
async def delete_item(item: DeleteItem, db: Session = Depends(get_db)):
    """Delete a file or folder"""
    try:
        if not item.path:
            raise HTTPException(status_code=400, detail="Path cannot be empty")
            
        if not validate_path(item.path):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        full_path = PROJECTS_DIR / item.path.lstrip('/')
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
            
        if full_path.is_dir():
            shutil.rmtree(full_path)
            if '/' not in item.path:
                crud.delete_project(db, path=str(full_path))
        else:
            full_path.unlink()
        return {"status": "success"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Delete item error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/projects")
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all projects"""
    try:
        return crud.get_projects(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get projects")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Page routes
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render home page with folder structure"""
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request}
    )

@app.get("/editor", response_class=HTMLResponse)
async def get_editor(request: Request):
    """Render editor page"""
    return templates.TemplateResponse(
        request=request,
        name="editor.html",
        context={"request": request}
    )

@app.get("/api/db/projects")
def view_all_projects(db: Session = Depends(get_db)):
    """View all projects in database"""
    projects = crud.get_projects(db)
    return [{
        "id": project.id,
        "project_id": project.project_id,
        "name": project.name,
        "path": project.path,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    } for project in projects]

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if not validate_path(message.get("path", "")):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid path"
                })
                continue
            
            if message["type"] == "save":
                path = message["path"]
                content = message["content"]
                full_path = PROJECTS_DIR / path.lstrip('/')
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                await websocket.send_json({"type": "save", "status": "success"})
            
            elif message["type"] == "load":
                path = message["path"]
                try:
                    full_path = PROJECTS_DIR / path.lstrip('/')
                    content = full_path.read_text()
                    await websocket.send_json({
                        "type": "load",
                        "content": content
                    })
                except FileNotFoundError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "File not found"
                    })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid operation type"
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error"
            })
        except Exception:
            pass