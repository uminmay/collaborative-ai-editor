import pytest
from fastapi.testclient import TestClient
from app.main import app
import shutil
import os
from pathlib import Path

def test_websocket_connection(editor_client):
    """Test WebSocket connection and basic operations"""
    if not os.path.exists("editor_files"):
        Path("editor_files").mkdir(exist_ok=True)
    
    # Set the session cookie
    editor_client.cookies.set("session", "test-session")
    
    with editor_client.websocket_connect("/ws") as websocket:
        # Test sending a message
        websocket.send_json({
            "type": "load",
            "path": "test.txt"
        })
        
        # Test receiving a message
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "File not found" in response["message"]

def test_websocket_file_operations(editor_client, test_file):
    """Test file operations through WebSocket"""
    editor_client.cookies.set("session", "test-session")
    
    with editor_client.websocket_connect("/ws") as websocket:
        # Test saving a file
        websocket.send_json({
            "type": "save",
            "path": test_file,
            "content": "test content"
        })
        response = websocket.receive_json()
        assert response["type"] == "save"
        assert response["status"] == "success"

        # Test loading the file
        websocket.send_json({
            "type": "load",
            "path": test_file
        })
        response = websocket.receive_json()
        assert response["type"] == "load"
        assert response["content"] == "test content"

def test_websocket_invalid_path(editor_client):
    """Test WebSocket security for invalid paths"""
    editor_client.cookies.set("session", "test-session")
    
    with editor_client.websocket_connect("/ws") as websocket:
        invalid_paths = ["../outside", "/../../etc/passwd"]
        
        for path in invalid_paths:
            websocket.send_json({
                "type": "load",
                "path": path
            })
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Invalid path" in response["message"]

def test_websocket_auth(test_client):
    """Test WebSocket authentication"""
    # Try connecting without authentication
    with pytest.raises(Exception):
        with test_client.websocket_connect("/ws") as websocket:
            pass