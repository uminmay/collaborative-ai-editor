from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Create editor_files directory if it doesn't exist
os.makedirs("editor_files", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def get_editor(request: Request):
    return templates.TemplateResponse("editor.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "save":
                filename = message["filename"]
                content = message["content"]
                with open(f"editor_files/{filename}", "w") as f:
                    f.write(content)
                await websocket.send_json({"type": "save", "status": "success"})
            
            elif message["type"] == "load":
                filename = message["filename"]
                try:
                    with open(f"editor_files/{filename}", "r") as f:
                        content = f.read()
                    await websocket.send_json({"type": "load", "content": content})
                except FileNotFoundError:
                    await websocket.send_json({"type": "error", "message": "File not found"})
    
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

# Add editor_files directory to .gitignore
with open(".gitignore", "w") as f:
    f.write("editor_files/\n")
