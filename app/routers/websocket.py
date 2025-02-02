from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
import json
import logging
from typing import Optional
from pathlib import Path

from ..core.settings import settings
from ..db import crud, models, database

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_websocket_user(
    websocket: WebSocket,
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    """Get user from WebSocket session"""
    try:
        session = websocket.session
        if not session:
            return None
        
        username = session.get("user")
        if not username:
            return None
            
        return crud.get_user_by_username(db, username)
    except Exception as e:
        logger.error(f"Error getting websocket user: {e}")
        return None

def check_if_project_exists(db: Session, path: str) -> bool:
    """Check if the project or file's parent project exists"""
    parts = Path(path).parts
    if len(parts) >= 1:
        project_path = str(Path(parts[0]))
        project = crud.get_project(db, path=project_path)
        return project is not None
    return False

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(database.get_db)
):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "load":
                path = message.get("path")
                if not path:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Path is required"
                    })
                    continue
                    
                try:
                    # First check if project exists
                    if not check_if_project_exists(db, path):
                        await websocket.send_json({
                            "type": "error",
                            "message": "Project has been deleted"
                        })
                        continue

                    full_path = settings.PROJECTS_DIR / path.lstrip("/")
                    if not full_path.exists():
                        await websocket.send_json({
                            "type": "error",
                            "message": "File has been deleted"
                        })
                        continue
                    else:
                        content = full_path.read_text()
                        await websocket.send_json({
                            "type": "load",
                            "content": content
                        })
                except Exception as e:
                    logger.error(f"Error loading file: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
            elif message["type"] == "save":
                path = message.get("path")
                content = message.get("content")
                
                if not path or content is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Path and content are required"
                    })
                    continue
                
                try:
                    # Check if project exists before saving
                    if not check_if_project_exists(db, path):
                        await websocket.send_json({
                            "type": "error",
                            "message": "Project has been deleted"
                        })
                        continue

                    full_path = settings.PROJECTS_DIR / path.lstrip("/")
                    if not full_path.parent.exists():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Parent directory has been deleted"
                        })
                        continue

                    full_path.write_text(content)
                    await websocket.send_json({
                        "type": "save",
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Error saving file: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
    
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)