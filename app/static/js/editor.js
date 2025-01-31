let ws = new WebSocket(`ws://${window.location.host}/ws`);
let lastSaveTimeout;
let currentPath = new URLSearchParams(window.location.search).get('path');
let saveStatus = document.getElementById('save-status');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'load') {
        document.getElementById('editor').value = data.content;
    } else if (data.type === 'error') {
        alert(data.message);
    } else if (data.type === 'save') {
        saveStatus.textContent = 'All changes saved';
        setTimeout(() => {
            saveStatus.textContent = '';
        }, 2000);
    }
};

// Load file content when page loads
if (currentPath) {
    document.getElementById('filepath').textContent = currentPath;
    ws.addEventListener('open', function() {
        ws.send(JSON.stringify({
            type: 'load',
            path: currentPath
        }));
    });
}

function autoSave() {
    if (!currentPath) return;
    
    const content = document.getElementById('editor').value;
    saveStatus.textContent = 'Saving...';
    
    // Clear any pending save
    if (lastSaveTimeout) {
        clearTimeout(lastSaveTimeout);
    }
    
    // Set new save timeout
    lastSaveTimeout = setTimeout(() => {
        ws.send(JSON.stringify({
            type: 'save',
            path: currentPath,
            content: content
        }));
    }, 1000); // Save after 1 second of no typing
}

// Add event listener for editor changes
document.getElementById('editor').addEventListener('input', autoSave);

// Handle WebSocket reconnection
ws.onclose = function() {
    saveStatus.textContent = 'Connection lost. Reconnecting...';
    setTimeout(function() {
        ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        // Reload the content once reconnected
        ws.addEventListener('open', function() {
            saveStatus.textContent = 'Connection restored';
            if (currentPath) {
                ws.send(JSON.stringify({
                    type: 'load',
                    path: currentPath
                }));
            }
            setTimeout(() => {
                saveStatus.textContent = '';
            }, 2000);
        });
    }, 1000);
};