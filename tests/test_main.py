def test_get_editor(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Simple Code Editor" in response.text

def test_websocket(test_client):
    with test_client.websocket_connect("/ws") as websocket:
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
