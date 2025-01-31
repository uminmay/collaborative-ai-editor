from fastapi import FastAPI, WebSocket, Request, HTTPException
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
from fastapi.responses import JSONResponse
import logging
from logging.config import dictConfig

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
        }
    },
    "root": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "handlers": ["console"]
    }
}

dictConfig(logging_config)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add after creating the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create projects directory if it doesn't exist
PROJECTS_DIR = Path("editor_files")
PROJECTS_DIR.mkdir(exist_ok=True)

class CreateItem(BaseModel):
    name: str
    type: str
    path: str

class DeleteItem(BaseModel):
    path: str

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

@app.get("/api/structure")
async def get_structure():
    """Get the entire project structure"""
    return get_directory_structure(PROJECTS_DIR)

@app.post("/api/create")
async def create_item(item: CreateItem):
    """Create a new file or folder"""
    full_path = PROJECTS_DIR / item.path.lstrip('/')
    new_path = full_path / item.name if item.path != '/' else PROJECTS_DIR / item.name
    
    try:
        if item.type == 'folder':
            new_path.mkdir(parents=True, exist_ok=True)
        else:
            new_path.touch()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/delete")
async def delete_item(item: DeleteItem):
    """Delete a file or folder"""
    full_path = PROJECTS_DIR / item.path.lstrip('/')
    
    try:
        if full_path.is_dir():
            shutil.rmtree(full_path)
        else:
            full_path.unlink()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render home page with folder structure"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/editor", response_class=HTMLResponse)
async def get_editor(request: Request):
    """Render editor page"""
    return templates.TemplateResponse("editor.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
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
                    await websocket.send_json({"type": "load", "content": content})
                except FileNotFoundError:
                    await websocket.send_json({"type": "error", "message": "File not found"})
    
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()