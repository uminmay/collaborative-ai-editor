from fastapi import FastAPI, WebSocket, Request, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import json
from pathlib import Path
import shutil
from typing import Optional, Dict, Union, Annotated
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.config import dictConfig
from sqlalchemy.orm import Session
from app.db import models, crud, database, schemas
from jose import JWTError, jwt
from datetime import datetime, timedelta
import uuid
from starlette.middleware.sessions import SessionMiddleware

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

dictConfig(logging_config)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(title="Collaborative AI Editor")

# Session middleware with a secure random key
SESSION_SECRET = str(uuid.uuid4())
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

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

# Static files and templates setup
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create projects directory
PROJECTS_DIR = Path("editor_files")
PROJECTS_DIR.mkdir(exist_ok=True)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Pydantic models for request validation
class CreateItem(BaseModel):
    name: str
    type: str
    path: str

class DeleteItem(BaseModel):
    path: str

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    request: Request,
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    # First check session
    session = request.session
    username = session.get("user")
    if username:
        return crud.get_user_by_username(db, username)
    
    # Then check bearer token
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username:
                return crud.get_user_by_username(db, username)
        except JWTError:
            return None
    
    return None

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

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    db: Session = Depends(database.get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    logger.info(f"Login attempt for username: {username}")
    user = crud.authenticate_user(db, username, password)
    if not user:
        logger.warning(f"Failed login attempt for username: {username}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )
    
    logger.info(f"Successful login for username: {username}")
    # Create session
    request.session["user"] = user.username
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite='lax',
        max_age=1800
    )
    return response

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# Initialize admin user on startup
@app.on_event("startup")
async def startup_event():
    try:
        # Ensure database tables are created
        models.Base.metadata.create_all(bind=database.engine)
        
        # Create admin user
        db = next(database.get_db())
        admin = crud.get_user_by_username(db, "admin")
        if not admin:
            logger.info("Creating admin user...")
            crud.create_user(
                db,
                schemas.UserCreate(username="admin", password="admin")
            )
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error in startup: {e}", exc_info=True)

# Main application routes
@app.get("/", response_class=HTMLResponse)
async def get_home(
    request: Request,
    user: Optional[models.User] = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request}
    )

@app.get("/editor", response_class=HTMLResponse)
async def get_editor(
    request: Request,
    user: Optional[models.User] = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        request=request,
        name="editor.html",
        context={"request": request}
    )

# API endpoints
@app.get("/api/structure")
async def get_structure(user: Optional[models.User] = Depends(get_current_user)):
    """Get the entire project structure"""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        return get_directory_structure(PROJECTS_DIR)
    except Exception as e:
        logger.error(f"Error getting structure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get directory structure")

@app.post("/api/create")
async def create_item(
    item: CreateItem,
    db: Session = Depends(database.get_db),
    user: Optional[models.User] = Depends(get_current_user)
):
    """Create a new file or folder"""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
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
async def delete_item(
    item: DeleteItem,
    db: Session = Depends(database.get_db),
    user: Optional[models.User] = Depends(get_current_user)
):
    """Delete a file or folder"""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        if not item.path:
            raise HTTPException(status_code=400, detail="Path cannot be empty")
            
        # Validate path before checking existence
        if not validate_path(item.path):
            raise HTTPException(status_code=400, detail="Invalid path")

        # Check if path points outside project directory
        full_path = PROJECTS_DIR / item.path.lstrip('/')
        try:
            if not full_path.resolve().is_relative_to(PROJECTS_DIR.resolve()):
                raise HTTPException(status_code=400, detail="Invalid path")
        except (ValueError, RuntimeError):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        # Only check existence after path validation
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")
            
        if full_path.is_dir():
            shutil.rmtree(full_path)
            if '/' not in item.path:
                crud.delete_project(db, path=str(full_path))
        else:
            full_path.unlink()
        return {"status": "success"}

@app.get("/api/projects")
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    user: Optional[models.User] = Depends(get_current_user)
):
    """Get all projects"""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        return crud.get_projects(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error getting projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get projects")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# WebSocket auth
async def get_websocket_user(
    websocket: WebSocket,
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    session = websocket.session
    if not session:
        return None
    
    username = session.get("user")
    if not username:
        return None
        
    return crud.get_user_by_username(db, username)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(database.get_db)
):
    user = await get_websocket_user(websocket, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
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

# Exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error handling request: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": str(exc), "detail": str(exc.__class__.__name__)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)