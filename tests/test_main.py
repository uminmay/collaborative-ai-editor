import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
import shutil

def setup_module(module):
    """Setup test environment before tests"""
    # Create test directory
    Path("editor_files").mkdir(exist_ok=True)

def teardown_module(module):
    """Cleanup after tests"""
    # Remove test directory and all contents
    shutil.rmtree("editor_files", ignore_errors=True)

def test_get_home(test_client):
    """Test home page loads"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Projects List" in response.text  # Updated to match the actual title

def test_get_editor(test_client):
    """Test editor page loads"""
    response = test_client.get("/editor")
    assert response.status_code == 200
    assert "Code Editor" in response.text

def test_api_structure(test_client):
    """Test API returns folder structure"""
    response = test_client.get("/api/structure")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_create_folder(test_client):
    """Test folder creation"""
    response = test_client.post(
        "/api/create", 
        json={"name": "test_folder", "type": "folder", "path": "/"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert Path("editor_files/test_folder").is_dir()

def test_create_file(test_client):
    """Test file creation"""
    response = test_client.post(
        "/api/create", 
        json={"name": "test.txt", "type": "file", "path": "/"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert Path("editor_files/test.txt").is_file()

def test_delete_file(test_client):
    """Test file deletion"""
    # Create a file first
    test_file = Path("editor_files/to_delete.txt")
    test_file.touch()
    
    response = test_client.request(
        "DELETE",
        "/api/delete",
        json={"path": "to_delete.txt"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert not test_file.exists()

def test_delete_folder(test_client):
    """Test folder deletion"""
    # Create a folder first
    test_folder = Path("editor_files/to_delete_folder")
    test_folder.mkdir(exist_ok=True)
    
    response = test_client.request(
        "DELETE",
        "/api/delete",
        json={"path": "to_delete_folder"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert not test_folder.exists()

@pytest.mark.asyncio
async def test_websocket(test_client):
    """Test WebSocket connection and file operations"""
    with test_client.websocket_connect("/ws") as websocket:
        # Test save operation
        data = {
            "type": "save",
            "path": "test_ws.txt",
            "content": "Hello WebSocket!"
        }
        websocket.send_json(data)
        response = websocket.receive_json()
        assert response["type"] == "save"
        assert response["status"] == "success"
        
        # Verify file was created with correct content
        assert Path("editor_files/test_ws.txt").read_text() == "Hello WebSocket!"
        
        # Test load operation
        data = {
            "type": "load",
            "path": "test_ws.txt"
        }
        websocket.send_json(data)
        response = websocket.receive_json()
        assert response["type"] == "load"
        assert response["content"] == "Hello WebSocket!"
        
        # Test loading non-existent file
        data = {
            "type": "load",
            "path": "nonexistent.txt"
        }
        websocket.send_json(data)
        response = websocket.receive_json()
        assert response["type"] == "error"