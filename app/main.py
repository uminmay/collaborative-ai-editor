from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging

from .core.settings import settings
from .db import models, database, crud, schemas
from .routers import (
    auth_router, 
    admin_router, 
    projects_router, 
    websocket_router,
    collaborations_router
)

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# FastAPI app initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# Middlewares
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=1800  # 30 minutes
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(websocket_router)
app.include_router(collaborations_router)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.error(f"HTTP exception {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

# Initialize database
models.Base.metadata.create_all(bind=database.engine)

# Startup event
@app.on_event("startup")
async def startup_event():
    try:
        db = next(database.get_db())
        admin = crud.get_user_by_username(db, "admin")
        if not admin:
            logging.info("Creating admin user...")
            crud.create_user(
                db=db,
                user=schemas.UserCreate(username="admin", password="admin"),
                is_admin=True
            )
            logging.info("Admin user created successfully")
        else:
            logging.info("Admin user already exists")
    except Exception as e:
        logging.error(f"Error in startup: {e}", exc_info=True)
        raise

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)