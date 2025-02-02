import pytest
from fastapi.testclient import TestClient
from app.main import app
import shutil
import os
from pathlib import Path

@pytest.fixture
def websocket_client(editor_client, test_db):
    """Create an authenticated WebSocket client"""
    # Create and login a user
    username = f"wsuser_{uuid.uuid4().hex[:8]}"
    password = "testpass"
    user_create = schemas.UserCreate(username=username, password=password)
    user = crud.create_user(test_db, user_create)
    
    # Get authentication tokens
    response = editor_client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False
    )
    assert response.status_code == 302
    return editor_client, response.cookies

def test_websocket_connection(websocket_client):
    """Test WebSocket connection and basic operations"""
    client, cookies = websocket_client
    
    with client.websocket_connect("/ws", cookies=cookies) as websocket:
        # Test sending a message
        websocket.send_json({
            "type": "load",
            "path": "test.txt"
        })
        
        # Test receiving a message
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "File not found" in response["message"]

def test_websocket_file_operations(websocket_client, test_file):
    """Test file operations through WebSocket"""
    client, cookies = websocket_client
    
    with client.websocket_connect("/ws", cookies=cookies) as websocket:
        # Test saving a file
        websocket.send_json({
            "type": "save",
            "path": test_file,
            "content": "test content"
        })
        response = websocket.receive_json()
        assert response["type"] == "save"
        assert response["status"] == "success"

def test_websocket_invalid_path(websocket_client):
    """Test WebSocket security for invalid paths"""
    client, cookies = websocket_client
    
    with client.websocket_connect("/ws", cookies=cookies) as websocket:
        invalid_paths = ["../outside", "/../../etc/passwd"]
        
        for path in invalid_paths:
            websocket.send_json({
                "type": "load",
                "path": path
            })
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Invalid path" in response["message"]