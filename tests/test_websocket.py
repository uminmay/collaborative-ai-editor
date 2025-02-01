import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_connection(editor_client):
    """Test WebSocket connection and basic operations"""
    with editor_client.websocket_connect("/ws") as websocket:
        # Test connection is established
        assert websocket.accepted
        
        # Test sending a message
        websocket.send_json({
            "type": "ping",
            "content": "test"
        })
        
        # Test receiving a message
        response = websocket.receive_json()
        assert response["type"] == "error"  # Since "ping" is not a valid type
        assert "Invalid operation type" in response["message"]

def test_websocket_file_operations(editor_client, test_file):
    """Test file operations through WebSocket"""
    with editor_client.websocket_connect("/ws") as websocket:
        # Test loading a file
        websocket.send_json({
            "type": "load",
            "path": test_file
        })
        response = websocket.receive_json()
        assert response["type"] == "load"
        assert "content" in response

        # Test saving a file
        websocket.send_json({
            "type": "save",
            "path": test_file,
            "content": "test content"
        })
        response = websocket.receive_json()
        assert response["type"] == "save"
        assert response["status"] == "success"

def test_websocket_invalid_path(editor_client):
    """Test WebSocket security for invalid paths"""
    with editor_client.websocket_connect("/ws") as websocket:
        invalid_paths = [
            "../outside",
            "/../../etc/passwd",
            "\\windows\\path",
            "//double/slash"
        ]
        
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
            pass  # Should not reach here as connection should be rejected