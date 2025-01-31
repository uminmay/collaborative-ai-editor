import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_get_editor():
    response = client.get("/")
    assert response.status_code == 200
    assert "Simple Code Editor" in response.text

def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        data = {"type": "save", "filename": "test.txt", "content": "Hello, World!"}
        websocket.send_json(data)
        response = websocket.receive_json()
        assert response["type"] == "save"
        assert response["status"] == "success"

        data = {"type": "load", "filename": "test.txt"}
        websocket.send_json(data)
        response = websocket.receive_json()
        assert response["type"] == "load"
        assert response["content"] == "Hello, World!"
