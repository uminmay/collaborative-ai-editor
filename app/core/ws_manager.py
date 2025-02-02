from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Structure: {file_path: {client_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Structure: {client_id: file_path}
        self.client_files: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, file_path: str):
        """Connect a client to a file"""
        await websocket.accept()
        
        # Initialize file_path dict if it doesn't exist
        if file_path not in self.active_connections:
            self.active_connections[file_path] = {}
        
        # Add connection
        self.active_connections[file_path][client_id] = websocket
        self.client_files[client_id] = file_path
        
        # Log connection
        logger.info(f"Client {client_id} connected to {file_path}")
        
        # Notify other clients
        await self.broadcast(
            file_path,
            {
                "type": "user_joined",
                "client_id": client_id
            },
            exclude_client=client_id
        )
    
    def disconnect(self, client_id: str):
        """Disconnect a client"""
        try:
            # Get file_path for client
            file_path = self.client_files.get(client_id)
            if not file_path:
                return
            
            # Remove from active connections
            if file_path in self.active_connections:
                self.active_connections[file_path].pop(client_id, None)
                if not self.active_connections[file_path]:
                    del self.active_connections[file_path]
            
            # Remove from client_files
            self.client_files.pop(client_id, None)
            
            logger.info(f"Client {client_id} disconnected from {file_path}")
        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")
    
    async def broadcast(
        self,
        file_path: str,
        message: dict,
        exclude_client: Optional[str] = None
    ):
        """Broadcast message to all clients connected to a file"""
        if file_path not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        
        for client_id, websocket in self.active_connections[file_path].items():
            if client_id != exclude_client:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")
                    # Handle disconnection
                    self.disconnect(client_id)
    
    def get_connected_clients(self, file_path: str) -> List[str]:
        """Get list of clients connected to a file"""
        if file_path not in self.active_connections:
            return []
        return list(self.active_connections[file_path].keys())

# Global connection manager instance
manager = ConnectionManager()