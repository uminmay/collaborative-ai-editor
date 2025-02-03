// Global variables
let ws = null;
let lastSaveTimeout;
let currentPath = new URLSearchParams(window.location.search).get('path');
let saveStatus = document.getElementById('save-status');
let editor = document.getElementById('editor');
let lineNumbers = document.getElementById('line-numbers');
let activeUsers = document.getElementById('active-users');
let activeUsersToggle = document.getElementById('active-users-toggle');
let activeUsersDropdown = document.getElementById('active-users-dropdown');
let activeUsersCount = document.getElementById('active-users-count');

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

// Update active users display
function updateUsersList(users) {
    if (!activeUsers && !activeUsersDropdown) return;

    // Update count
    if (activeUsersCount) {
        activeUsersCount.textContent = users.length;
    }

    // Main active users display
    if (activeUsers) {
        if (users.length === 0) {
            activeUsers.innerHTML = '<div class="text-gray-500">No other users active</div>';
            return;
        }
        
        activeUsers.innerHTML = users.map(user => `
            <div class="user-badge flex items-center">
                <span class="user-avatar mr-2" style="background-color: ${user.color}; width: 10px; height: 10px; border-radius: 50%;"></span>
                <span>${user.username}</span>
            </div>
        `).join('');
    }

    // Dropdown list
    if (activeUsersDropdown) {
        if (users.length === 0) {
            activeUsersDropdown.innerHTML = '<div class="text-gray-500 p-2">No other users active</div>';
        } else {
            activeUsersDropdown.innerHTML = users.map(user => `
                <div class="user-badge flex items-center p-2 hover:bg-gray-100">
                    <span class="user-avatar mr-2" style="background-color: ${user.color}; width: 10px; height: 10px; border-radius: 50%;"></span>
                    <span>${user.username}</span>
                </div>
            `).join('');
        }
    }
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

    // Immediately check active users after save
    ws.send(JSON.stringify({
        type: 'check_active',
        path: currentPath
    }));
}

// Debounced auto-save
function autoSave() {
    if (lastSaveTimeout) {
        clearTimeout(lastSaveTimeout);
    }
    lastSaveTimeout = setTimeout(saveContent, 1000);
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

            case 'active_editors':
                updateUsersList(data.users || []);
                break;

            case 'editor_joined':
            case 'editor_left':
                // Trigger active users check
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'check_active',
                        path: currentPath
                    }));
                }
                break;

            case 'error':
                updateStatus(data.message, 3000, true);
                break;

            case 'cursor_update':
                // Optional: Implement cursor visualization for other users
                console.log('Cursor update received', data);
                break;
        }
    };

    ws.onclose = () => {
        updateStatus('Connection lost. Please refresh the page.', 0, true);
        editor.disabled = true;
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('Connection error', 0, true);
        editor.disabled = true;
    };
}

// Cursor position tracking
function trackCursorPosition() {
    if (!editor || !ws || ws.readyState !== WebSocket.OPEN) return;

    ws.send(JSON.stringify({
        type: 'cursor_update',
        path: currentPath,
        position: editor.selectionStart
    }));
}

// Initialize
if (currentPath) {
    // Set filepath display
    const filepathElement = document.getElementById('filepath');
    if (filepathElement) {
        filepathElement.textContent = currentPath;
    }

    // Disable editor until content is loaded
    editor.disabled = true;

    // Connect WebSocket
    connectWebSocket();

    // Event listeners
    editor.addEventListener('input', () => {
        autoSave();
        updateLineNumbers();
    });

    editor.addEventListener('keyup', trackCursorPosition);
    editor.addEventListener('click', trackCursorPosition);

    editor.addEventListener('scroll', () => {
        if (lineNumbers) {
            lineNumbers.scrollTop = editor.scrollTop;
        }
    });

    // Active users dropdown toggle
    if (activeUsersToggle && activeUsersDropdown) {
        activeUsersToggle.addEventListener('click', () => {
            activeUsersDropdown.classList.toggle('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (event) => {
            if (activeUsersDropdown && !activeUsersToggle.contains(event.target) 
                && !activeUsersDropdown.contains(event.target)) {
                activeUsersDropdown.classList.add('hidden');
            }
        });
    }

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