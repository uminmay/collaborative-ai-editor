// Global variables
let ws = null;
let lastSaveTimeout;
let currentPath = new URLSearchParams(window.location.search).get('path');
let saveStatus = document.getElementById('save-status');
let editor = document.getElementById('editor');
let lineNumbers = document.getElementById('line-numbers');
let activeUsers = document.getElementById('active-users');

// Keep track of current user
let currentUserId = null;

// Basic status update function
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

// Line numbers update
function updateLineNumbers() {
    if (!lineNumbers || !editor) return;
    const lines = editor.value.split('\n');
    const numbers = Array.from({ length: lines.length }, (_, i) => {
        return String(i + 1).padStart(3, ' ');
    }).join('\n');
    lineNumbers.textContent = numbers;
    lineNumbers.scrollTop = editor.scrollTop;
}

// Save content function
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

// Debounced auto-save
function autoSave() {
    if (lastSaveTimeout) {
        clearTimeout(lastSaveTimeout);
    }
    lastSaveTimeout = setTimeout(saveContent, 1000);
}

// Update active users display
function updateUsersList(users) {
    if (!activeUsers) return;
    activeUsers.innerHTML = users.map(user => `
        <div class="user-avatar" style="background-color: ${user.color}">
            ${user.username}
        </div>
    `).join('');
}

// WebSocket connection
function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        updateStatus('Connected');
        
        // Load file content
        if (currentPath) {
            // Wait 1 second before requesting file content
            setTimeout(() => {
                ws.send(JSON.stringify({
                    type: 'load',
                    path: currentPath
                }));
            }, 1000);
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'load':
                editor.value = data.content;
                editor.disabled = false;
                currentUserId = data.current_user_id;
                updateLineNumbers();
                
                if (data.active_editors) {
                    updateUsersList(data.active_editors);
                }
                updateStatus('File loaded');
                break;

            case 'save':
                updateStatus('Saved successfully');
                break;

            case 'content_update':
                // Only update content if it's from another user
                if (data.user && data.user.id !== currentUserId) {
                    const cursorPos = editor.selectionStart;
                    editor.value = data.content;
                    editor.selectionStart = cursorPos;
                    editor.selectionEnd = cursorPos;
                    updateLineNumbers();
                    updateStatus(`Changes received from ${data.user.username}`);
                }
                break;

            case 'error':
                updateStatus(data.message, 3000, true);
                break;
        }
    };

    ws.onclose = () => {
        updateStatus('Connection lost. Please refresh the page.', 0, true);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('Connection error', 0, true);
    };
}

// Initialize
if (currentPath) {
    document.getElementById('filepath').textContent = currentPath;
    editor.disabled = true;  // Disable until content is loaded
    connectWebSocket();

    // Event listeners
    editor.addEventListener('input', () => {
        autoSave();
        updateLineNumbers();
    });

    editor.addEventListener('scroll', () => {
        if (lineNumbers) {
            lineNumbers.scrollTop = editor.scrollTop;
        }
    });

    // Periodic check for active users
    setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'check_active',
                path: currentPath
            }));
        }
    }, 5000);
}