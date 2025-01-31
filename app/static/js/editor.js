let ws = new WebSocket(`ws://${window.location.host}/ws`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'load') {
        document.getElementById('editor').value = data.content;
    } else if (data.type === 'error') {
        alert(data.message);
    }
};

function saveFile() {
    const filename = document.getElementById('filename').value;
    const content = document.getElementById('editor').value;
    
    if (!filename) {
        alert('Please enter a filename');
        return;
    }
    
    ws.send(JSON.stringify({
        type: 'save',
        filename: filename,
        content: content
    }));
}

function loadFile() {
    const filename = document.getElementById('filename').value;
    
    if (!filename) {
        alert('Please enter a filename');
        return;
    }
    
    ws.send(JSON.stringify({
        type: 'load',
        filename: filename
    }));
}

// Reconnect WebSocket if connection is lost
ws.onclose = function() {
    setTimeout(function() {
        ws = new WebSocket(`ws://${window.location.host}/ws`);
    }, 1000);
};
