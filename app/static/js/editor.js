let ws = null;
let lastSaveTimeout;
let currentPath = new URLSearchParams(window.location.search).get('path');
let saveStatus = document.getElementById('save-status');
let editor = document.getElementById('editor');
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function updateStatus(message, duration = 2000, isError = false) {
    saveStatus.textContent = message;
    saveStatus.className = `text-sm ${isError ? 'text-red-500' : 'text-gray-500'}`;
    if (duration > 0) {
        setTimeout(() => {
            saveStatus.textContent = '';
        }, duration);
    }
}

function redirectToProjects() {
    window.location.href = '/';
}

function handleFileError(message) {
    editor.value = '';
    editor.disabled = true;
    editor.placeholder = message;
    updateStatus(message, 0, true);
    
    // Show a modal or alert to inform the user
    if (confirm(`${message}. Return to projects list?`)) {
        redirectToProjects();
    }
}

function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        updateStatus('Connected');
        reconnectAttempts = 0;

        // Load initial file content
        if (currentPath) {
            ws.send(JSON.stringify({
                type: 'load',
                path: currentPath
            }));
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'load':
                editor.value = data.content;
                editor.disabled = false;
                updateStatus('File loaded');
                break;
            case 'error':
                if (data.message.includes('deleted')) {
                    handleFileError(data.message);
                } else {
                    updateStatus(`Error: ${data.message}`, 3000, true);
                }
                break;
            case 'save':
                updateStatus('All changes saved');
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    };

    ws.onclose = () => {
        if (reconnectAttempts < maxReconnectAttempts) {
            updateStatus('Connection lost. Reconnecting...', 0);
            reconnectAttempts++;
            setTimeout(connectWebSocket, 1000 * Math.pow(2, reconnectAttempts));
        } else {
            updateStatus('Connection lost. Please refresh the page.', 0, true);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('Connection error', 0, true);
    };
}

function saveContent() {
    if (!currentPath || !ws || ws.readyState !== WebSocket.OPEN || editor.disabled) {
        return;
    }
    
    updateStatus('Saving...');
    
    ws.send(JSON.stringify({
        type: 'save',
        path: currentPath,
        content: editor.value
    }));
}

function autoSave() {
    if (lastSaveTimeout) {
        clearTimeout(lastSaveTimeout);
    }
    lastSaveTimeout = setTimeout(saveContent, 1000);
}

// Initialize
if (currentPath) {
    document.getElementById('filepath').textContent = currentPath;
    connectWebSocket();
    editor.addEventListener('input', autoSave);
}