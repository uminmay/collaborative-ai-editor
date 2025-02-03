from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import logging
from typing import Optional, Dict
from pathlib import Path
import asyncio
from datetime import datetime
import random

from ..core.settings import settings
from ..db import crud, models, database, schemas

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active WebSocket connections and user info
# Format: {file_path: {user_id: {"ws": WebSocket, "cursor": position, "color": color, etc}}}
active_connections: Dict[str, Dict[int, dict]] = {}

# Professional, dark color palette
USER_COLORS = [
    '#E63946', '#1D3557', '#2A9D8F', '#6A4C93', '#F4A261',
    '#264653', '#023047', '#8338EC', '#06D6A0', '#073B4C'
]

def get_random_color() -> str:
    """Get a random color from the palette"""
    return random.choice(USER_COLORS)

async def get_session_user(websocket: WebSocket, db: Session) -> Optional[tuple[models.User, str]]:
    """Get user and session ID from WebSocket session"""
    try:
        session = websocket.session
        if not session:
            return None
        
        session_id = session.get("session_id")
        if not session_id:
            return None
            
        db_session = crud.get_session(db, session_id)
        if not db_session or db_session.is_expired:
            return None
            
        return db_session.user, session_id
    except Exception as e:
        logger.error(f"Error getting websocket session: {e}")
        return None

async def broadcast_to_file(file_path: str, message: dict, exclude_user: Optional[int] = None):
    """Broadcast message to all users editing a file"""
    if file_path not in active_connections:
        return
        
    message_str = json.dumps(message)
    
    for user_id, connection in active_connections[file_path].items():
        if user_id != exclude_user:
            try:
                await connection["ws"].send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")

async def get_active_editors_info(file_path: str, current_user_id: int) -> list:
    """Get information about active editors for a file"""
    if file_path not in active_connections:
        return []
    
    current_time = datetime.now().timestamp()
    editors = []
    
    for user_id, connection in active_connections[file_path].items():
        # Skip current user from the list
        if user_id == current_user_id:
            continue
            
        # Extend timeout to 60 seconds to be more lenient
        last_update = connection.get("last_cursor_update", current_time)
        if current_time - last_update > 60:
            continue
            
        editors.append({
            "id": user_id,
            "username": connection.get("username", "Unknown"),
            "color": connection.get("color", "#000000"),
            "cursor": connection.get("cursor", 0),
            "last_active": last_update
        })
    
    # Sort by most recently active
    editors.sort(key=lambda x: x["last_active"], reverse=True)
    return editors

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(database.get_db)):
    session_info = await get_session_user(websocket, db)
    if not session_info:
        await websocket.close(code=1008)  # Policy violation
        return
        
    user, session_id = session_info
    current_file = None
    user_color = get_random_color()
    
    try:
        await websocket.accept()
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Update session activity
            crud.update_session_activity(db, session_id)
            
            if message["type"] == "load":
                path = message.get("path")
                if not path:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Path is required"
                    })
                    continue
                    
                try:
                    # Verify project exists and user has access
                    project_path = path.split('/')[0]
                    project = crud.get_project(db, project_path)
                    if not project:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Project not found"
                        })
                        continue
                        
                    if not crud.check_project_access(db, project.id, user.id):
                        await websocket.send_json({
                            "type": "error",
                            "message": "Access denied"
                        })
                        continue

                    full_path = settings.PROJECTS_DIR / path.lstrip("/")
                    if not full_path.exists():
                        await websocket.send_json({
                            "type": "error",
                            "message": "File not found"
                        })
                        continue

                    # Initialize file connections if needed
                    if path not in active_connections:
                        active_connections[path] = {}
                    
                    # Add user to active connections
                    active_connections[path][user.id] = {
                        "ws": websocket,
                        "username": user.username,
                        "color": user_color,
                        "cursor": 0,
                        "last_cursor_update": datetime.now().timestamp()
                    }
                    current_file = path

                    # Track editor activity and get stats
                    editor_activity = crud.track_editor_activity(db, user.id, path)
                    editor_stats = crud.get_editor_stats(db, path)
                    
                    # Get file content
                    content = full_path.read_text()
                    
                    # Get active editors
                    active_editors = await get_active_editors_info(path, user.id)
                    
                    # Send initial data to the user
                    await websocket.send_json({
                        "type": "load",
                        "content": content,
                        "current_user_id": user.id,
                        "username": user.username,
                        "color": user_color,
                        "active_editors": active_editors
                    })
                    
                    # Notify other editors
                    await broadcast_to_file(
                        path,
                        {
                            "type": "editor_joined",
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "color": user_color
                            }
                        },
                        exclude_user=user.id
                    )
                    
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
                    # Verify project exists and user has access
                    project_path = path.split('/')[0]
                    project = crud.get_project(db, project_path)
                    if not project:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Project not found"
                        })
                        continue
                        
                    if not crud.check_project_access(db, project.id, user.id):
                        await websocket.send_json({
                            "type": "error",
                            "message": "Access denied"
                        })
                        continue

                    full_path = settings.PROJECTS_DIR / path.lstrip("/")
                    if not full_path.parent.exists():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Parent directory not found"
                        })
                        continue

                    # Save file
                    full_path.write_text(content)
                    
                    # Update activity timestamp
                    crud.track_editor_activity(db, user.id, path)
                    
                    # Notify client of successful save
                    await websocket.send_json({
                        "type": "save",
                        "status": "success"
                    })
                    
                    # Notify other editors
                    await broadcast_to_file(
                        path,
                        {
                            "type": "content_update",
                            "content": content,
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "color": user_color
                            }
                        },
                        exclude_user=user.id
                    )
                    
                    # Broadcast active editors after save
                    active_editors = await get_active_editors_info(path, user.id)
                    await broadcast_to_file(
                        path,
                        {
                            "type": "active_editors",
                            "users": active_editors
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Error saving file: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })

            elif message["type"] == "cursor_update":
                if not current_file:
                    continue
                    
                position = message.get("position", 0)
                timestamp = datetime.now().timestamp()
                
                if current_file in active_connections:
                    user_connection = active_connections[current_file].get(user.id)
                    if user_connection:
                        # Only broadcast if significant time has passed or position changed significantly
                        last_update = user_connection.get("last_cursor_update", 0)
                        last_position = user_connection.get("cursor", 0)
                        
                        if (timestamp - last_update > 0.05 or  # 50ms throttle
                            abs(position - last_position) > 10):  # Position changed significantly
                            
                            user_connection["cursor"] = position
                            user_connection["last_cursor_update"] = timestamp
                            
                            # Broadcast cursor position to other users
                            await broadcast_to_file(
                                current_file,
                                {
                                    "type": "cursor_update",
                                    "user": {
                                        "id": user.id,
                                        "username": user.username,
                                        "color": user_color
                                    },
                                    "position": position,
                                    "timestamp": timestamp
                                },
                                exclude_user=user.id
                            )

            elif message["type"] == "check_active":
                if not current_file:
                    continue
                    
                try:
                    # Get file content
                    full_path = settings.PROJECTS_DIR / current_file.lstrip("/")
                    content = full_path.read_text() if full_path.exists() else None
                    
                    # Get active editors
                    active_editors = await get_active_editors_info(current_file, user.id)
                    
                    await websocket.send_json({
                        "type": "active_editors",
                        "users": active_editors,
                        "content": content
                    })
                except Exception as e:
                    logger.error(f"Error checking active editors: {e}")
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user.username}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cleanup when connection closes
        if current_file and current_file in active_connections:
            if user.id in active_connections[current_file]:
                del active_connections[current_file][user.id]
                if not active_connections[current_file]:
                    del active_connections[current_file]
                
            # Remove editor activity
            crud.remove_editor_activity(db, user.id, current_file)
            
            # Notify other editors
            await broadcast_to_file(
                current_file,
                {
                    "type": "editor_left",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "color": user_color
                    }
                }
            )
            
            # Broadcast updated active editors list
            if current_file in active_connections:
                active_editors = await get_active_editors_info(current_file, user.id)
                await broadcast_to_file(
                    current_file,
                    {
                        "type": "active_editors",
                        "users": active_editors
                    }
                )