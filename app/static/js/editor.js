// Global variables
let ws = null;
let lastSaveTimeout;
let currentPath = new URLSearchParams(window.location.search).get('path');
let saveStatus = document.getElementById('save-status');
let editor = document.getElementById('editor');
let lineNumbers = document.getElementById('line-numbers');
let activeUsers = document.getElementById('active-users');
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// Keep track of current user
let currentUserId = null;
let currentUsername = null;
let currentUserColor = null;

// Function to update the status message
function updateStatus(message, duration = 2000, isError = false) {
    if (!saveStatus) return;
    saveStatus.textContent = message;
    saveStatus.className = `text-sm ${isError ? 'text-red-500' : 'text-gray-500'}`;
    if (duration > 0) {
        setTimeout(() => {
            saveStatus.textContent = '';
        }, duration);
    }
}

// Function to update line numbers
function updateLineNumbers() {
    if (!lineNumbers || !editor) return;
    
    const lines = editor.value.split('\n');
    const numbers = Array.from({ length: lines.length }, (_, i) => {
        // Pad numbers with spaces for right alignment
        return String(i + 1).padStart(3, ' ');
    }).join('\n');
    
    lineNumbers.textContent = numbers;
    
    // Make sure line numbers area scrolls with editor
    lineNumbers.scrollTop = editor.scrollTop;
}

// Function to save content
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

// Function for auto-save
function autoSave() {
    if (lastSaveTimeout) {
        clearTimeout(lastSaveTimeout);
    }
    lastSaveTimeout = setTimeout(saveContent, 1000);
}

// Update the active users display
function updateUsersList(users) {
    if (!activeUsers) return;
    
    activeUsers.innerHTML = users.map(user => `
        <div class="user-avatar" style="background-color: ${user.color}">
            ${user.username}
        </div>
    `).join('');
}

// WebSocket connection handling
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
                updateLineNumbers();
                
                // Set current user info
                currentUserId = data.current_user_id;
                currentUsername = data.username;
                currentUserColor = data.color;
                
                // Show active editors
                if (data.active_editors) {
                    updateUsersList(data.active_editors);
                }
                
                updateStatus('File loaded');
                break;

            case 'save':
                updateStatus('Saved successfully');
                break;

            case 'error':
                updateStatus(data.message, 3000, true);
                break;

            case 'editor_joined':
                if (data.user.id !== currentUserId) {
                    updateStatus(`${data.user.username} joined`, 2000);
                    ws.send(JSON.stringify({
                        type: 'check_active',
                        path: currentPath
                    }));
                }
                break;

            case 'editor_left':
                if (data.user.id !== currentUserId) {
                    updateStatus(`${data.user.username} left`, 2000);
                    ws.send(JSON.stringify({
                        type: 'check_active',
                        path: currentPath
                    }));
                }
                break;

            case 'active_editors':
                updateUsersList(data.users);
                if (data.content && data.content !== editor.value) {
                    editor.value = data.content;
                    updateLineNumbers();
                }
                break;
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

// Initialize
if (currentPath) {
    document.getElementById('filepath').textContent = currentPath;
    connectWebSocket();

    // Set up editor event listeners
    editor.addEventListener('input', () => {
        autoSave();
        updateLineNumbers();
    });

    editor.addEventListener('scroll', () => {
        if (lineNumbers) {
            lineNumbers.scrollTop = editor.scrollTop;
        }
    });

    // Check active editors periodically
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'check_active',
                path: currentPath
            }));
        }
    }, 5000);
}