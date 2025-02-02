let fileTree = document.getElementById('file-tree');
let emptyState = document.getElementById('empty-state');
let createProjectModal = document.getElementById('create-project-modal');
let createItemModal = document.getElementById('create-item-modal');
let projectNameInput = document.getElementById('project-name');
let itemNameInput = document.getElementById('item-name');
let currentPathInput = document.getElementById('current-path');
let typeInputs = document.querySelectorAll('input[name="type"]');

// Load file tree on page load
loadFileTree();

async function loadFileTree() {
    try {
        const response = await fetch('/api/structure');
        const structure = await response.json();
        
        // Show empty state if no projects
        if (Object.keys(structure).length === 0) {
            fileTree.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            fileTree.innerHTML = buildTreeHTML(structure);
        }
    } catch (error) {
        console.error('Error loading file tree:', error);
    }
}

function buildTreeHTML(structure, path = '') {
    let html = '<ul class="pl-4">';
    
    for (const [name, value] of Object.entries(structure)) {
        const fullPath = path ? `${path}/${name}` : name;
        const isFile = typeof value === 'string';
        
        html += `
            <li class="py-1">
                <div class="flex items-center group">
                    <span class="mr-2">${isFile ? '📄' : '📁'}</span>
                    ${isFile 
                        ? `<a href="/editor?path=${encodeURIComponent(fullPath)}" 
                             class="text-blue-500 hover:text-blue-700"
                             title="Open ${name}">${name}</a>`
                        : `<span class="font-medium cursor-default">${name}</span>`
                    }
                    <div class="ml-auto hidden group-hover:flex space-x-2">
                        ${!isFile ? `
                            <button onclick="showCreateItemModal('${fullPath}')" 
                                    class="text-sm text-blue-500 hover:text-blue-700"
                                    title="Add new item">
                                Add Item
                            </button>
                        ` : ''}
                        <button onclick="deleteItem('${fullPath}')" 
                                class="text-sm text-red-500 hover:text-red-700"
                                title="Delete ${isFile ? 'file' : 'folder'}">
                            Delete
                        </button>
                    </div>
                </div>
                ${!isFile && Object.keys(value).length ? buildTreeHTML(value, fullPath) : ''}
            </li>`;
    }
    
    return html + '</ul>';
}

function showCreateProjectModal() {
    createProjectModal.classList.remove('hidden');
    projectNameInput.value = '';
    projectNameInput.focus();
}

function hideCreateProjectModal() {
    createProjectModal.classList.add('hidden');
    projectNameInput.value = '';
}

function showCreateItemModal(path) {
    createItemModal.classList.remove('hidden');
    currentPathInput.value = path;
    itemNameInput.value = '';
    typeInputs[0].checked = true;  // Select 'file' by default
    itemNameInput.focus();
}

function hideCreateItemModal() {
    createItemModal.classList.add('hidden');
    itemNameInput.value = '';
}

async function createProject() {
    const name = projectNameInput.value.trim();
    if (!name) return;
    
    try {
        const response = await fetch('/api/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name,
                path: '/',
                type: 'folder'
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to create project');
        }
        
        hideCreateProjectModal();
        await loadFileTree();
    } catch (error) {
        console.error('Error creating project:', error);
        alert(error.message || 'Failed to create project');
    }
}

async function createItem() {
    const name = itemNameInput.value.trim();
    const path = currentPathInput.value;
    const type = document.querySelector('input[name="type"]:checked').value;
    
    if (!name) return;
    
    try {
        const response = await fetch('/api/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, path, type })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to create item');
        }
        
        hideCreateItemModal();
        await loadFileTree();
    } catch (error) {
        console.error('Error creating item:', error);
        alert(error.message || 'Failed to create item');
    }
}

async function deleteItem(path) {
    const isRoot = path.split('/').length === 1;
    const message = isRoot 
        ? 'Are you sure you want to delete this project? This will delete all files and folders inside it.'
        : 'Are you sure you want to delete this item?';
        
    if (!confirm(message)) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to delete item');
        }
        
        await loadFileTree();
    } catch (error) {
        console.error('Error deleting item:', error);
        alert(error.message || 'Failed to delete item');
    }
}

// Handle Enter key in modals
projectNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createProject();
    }
});

itemNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createItem();
    }
});