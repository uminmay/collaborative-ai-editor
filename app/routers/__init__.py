from .auth import router as auth_router
from .admin import router as admin_router
from .projects import router as projects_router
from .websocket import router as websocket_router

__all__ = [
    'auth_router',
    'admin_router',
    'projects_router',
    'websocket_router',
]