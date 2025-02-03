// State
let currentUser = null;
let projects = [];
let currentProjectId = null;
let currentProjectPath = '';
let currentFolderPath = '';

// DOM Elements
const projectsList = document.getElementById('projects-list');
const emptyState = document.getElementById('empty-state');
const createProjectModal = document.getElementById('create-project-modal');
const createProjectItemModal = document.getElementById('create-project-item-modal');
const projectExplorerModal = document.getElementById('project-explorer-modal');
const collaboratorModal = document.getElementById('collaborator-modal');
const transferModal = document.getElementById('transfer-modal');
const projectTree = document.getElementById('project-tree');

const projectNameInput = document.getElementById('project-name');
const collaboratorSelect = document.getElementById('collaborator-select');
const newOwnerSelect = document.getElementById('new-owner-select');
const currentCollaborators = document.getElementById('current-collaborators');
const currentProjectName = document.getElementById('current-project-name');
const newItemNameInput = document.getElementById('new-item-name');
const newItemPathInput = document.getElementById('new-item-path');
const newItemTypeInput = document.getElementById('new-item-type');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
});

// Project Management Functions
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        if (!response.ok) throw new Error('Failed to load projects');
        
        const data = await response.json();
        currentUser = data.user;
        projects = data.projects;
        
        renderProjects();
    } catch (error) {
        console.error('Error loading projects:', error);
        showError('Failed to load projects');
    }
}

function renderProjects() {
    const projectListContainer = document.querySelector('.bg-white.rounded-lg.shadow.overflow-hidden');
    
    if (!projects.length) {
        // Hide the table container
        if (projectListContainer) projectListContainer.innerHTML = `
            <div id="empty-state" class="text-center text-gray-500 py-8">
                <p class="text-lg mb-4">No projects yet</p>
                <button onclick="showCreateProjectModal()" 
                        class="text-blue-500 hover:text-blue-700">
                    Create your first project
                </button>
            </div>
        `;
        return;
    }

    // Show table with projects
    projectListContainer.innerHTML = `
        <table class="min-w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project Name</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Collaborators</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody id="projects-list" class="bg-white divide-y divide-gray-200"></tbody>
        </table>
    `;

    const projectsList = document.getElementById('projects-list');
    if (projectsList) {
        projectsList.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        
        projectsList.innerHTML = projects.map(project => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${formatDate(project.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <a href="#" onclick="openProjectExplorer('${project.path}'); return false;" 
                       class="text-blue-600 hover:text-blue-900">
                        ${escapeHtml(project.name)}
                    </a>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${escapeHtml(project.owner.username)}
                    ${project.is_owner ? '<span class="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Owner</span>' : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center space-x-2">
                        ${project.collaborators.map(collab => `
                            <span class="inline-flex items-center justify-center h-8 w-8 rounded-full bg-gray-500 text-white text-sm" 
                                  title="${escapeHtml(collab.username)}">
                                ${escapeHtml(collab.username.substring(0, 2).toUpperCase())}
                            </span>
                        `).join('')}
                        ${(project.is_owner || currentUser.is_admin) ? `
                            <button onclick="showCollaboratorModal(${project.id})"
                                    class="text-sm text-blue-600 hover:text-blue-900 ml-2">
                                Manage
                            </button>
                        ` : ''}
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <div class="flex items-center space-x-4">
                        ${(project.is_owner || currentUser.is_admin) ? `
                            <button onclick="deleteProject('${project.path}')"
                                    class="text-red-600 hover:text-red-900">
                                Delete
                            </button>
                        ` : ''}
                        ${currentUser.is_admin ? `
                            <button onclick="showTransferModal(${project.id})"
                                    class="text-blue-600 hover:text-blue-900">
                                Transfer
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }
}

// Project Creation Functions
function showCreateProjectModal() {
    createProjectModal.classList.remove('hidden');
    projectNameInput.value = '';
    projectNameInput.focus();
}

function hideCreateProjectModal() {
    createProjectModal.classList.add('hidden');
    projectNameInput.value = '';
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
        // Reload projects immediately after creation
        await loadProjects();
    } catch (error) {
        console.error('Error creating project:', error);
        showError(error.message || 'Failed to create project');
    }
}

// Project Explorer Functions
async function openProjectExplorer(projectPath) {
    currentProjectPath = projectPath;
    currentProjectName.textContent = projectPath;
    projectExplorerModal.classList.remove('hidden');
    await loadProjectStructure(projectPath);
}

function hideProjectExplorer() {
    projectExplorerModal.classList.add('hidden');
    currentProjectPath = '';
    currentFolderPath = '';
}

async function loadProjectStructure(projectPath) {
    try {
        const response = await fetch(`/api/structure?path=${encodeURIComponent(projectPath)}`);
        if (!response.ok) throw new Error('Failed to load project structure');
        
        const structure = await response.json();
        renderProjectTree(structure, projectPath);
    } catch (error) {
        console.error('Error loading project structure:', error);
        showError('Failed to load project structure');
    }
}

function renderProjectTree(structure, basePath = '', level = 0) {
    if (Object.keys(structure).length === 0) {
        return `
            <div class="text-center py-8 text-gray-500">
                <p class="text-lg mb-4">Empty! Create Something</p>
                <div class="space-x-2">
                    <button onclick="showCreateItemModal('file')" 
                            class="text-blue-500 hover:text-blue-700">
                        New File
                    </button>
                    <span class="text-gray-400">|</span>
                    <button onclick="showCreateItemModal('folder')" 
                            class="text-blue-500 hover:text-blue-700">
                        New Folder
                    </button>
                </div>
            </div>`;
    }
    
    let html = level === 0 ? '' : '<ul class="pl-4">';
    
    for (const [name, type] of Object.entries(structure)) {
        const isFile = type === 'file';
        const fullPath = basePath ? `${basePath}/${name}` : name;
        
        html += `
            <li class="py-1">
                <div class="flex items-center group">
                    <span class="mr-2">${isFile ? '📄' : '📁'}</span>
                    ${isFile 
                        ? `<a onclick="openFile('${fullPath}')" 
                             class="cursor-pointer text-blue-600 hover:text-blue-900">${name}</a>`
                        : `<span class="font-medium cursor-pointer" 
                                onclick="toggleFolder(this, '${fullPath}')">${name}</span>`
                    }
                    <div class="ml-auto hidden group-hover:flex space-x-2">
                        ${!isFile ? `
                            <button onclick="showCreateItemModal('file', '${fullPath}')"
                                    class="text-sm text-blue-600 hover:text-blue-900">
                                Add File
                            </button>
                            <button onclick="showCreateItemModal('folder', '${fullPath}')"
                                    class="text-sm text-blue-600 hover:text-blue-900">
                                Add Folder
                            </button>
                        ` : ''}
                        <button onclick="deleteProjectItem('${fullPath}')"
                                class="text-sm text-red-600 hover:text-red-900">
                            Delete
                        </button>
                    </div>
                </div>
                ${!isFile ? `<div class="folder-content hidden"></div>` : ''}
            </li>`;
    }
    
    html += level === 0 ? '' : '</ul>';
    
    if (level === 0) {
        projectTree.innerHTML = html;
    }
    return html;
}

async function toggleFolder(element, folderPath) {
    const contentDiv = element.parentElement.nextElementSibling;
    if (contentDiv.classList.contains('hidden')) {
        try {
            const response = await fetch(`/api/structure?path=${encodeURIComponent(folderPath)}`);
            if (!response.ok) throw new Error('Failed to load folder content');
            
            const structure = await response.json();
            if (Object.keys(structure).length === 0) {
                contentDiv.innerHTML = `
                    <div class="pl-6 py-2 text-gray-500">
                        <span class="text-sm">Empty folder</span>
                        <div class="space-x-2 mt-1">
                            <button onclick="showCreateItemModal('file', '${folderPath}')" 
                                    class="text-sm text-blue-500 hover:text-blue-700">
                                Add File
                            </button>
                            <span class="text-gray-400">|</span>
                            <button onclick="showCreateItemModal('folder', '${folderPath}')" 
                                    class="text-sm text-blue-500 hover:text-blue-700">
                                Add Folder
                            </button>
                        </div>
                    </div>`;
            } else {
                contentDiv.innerHTML = renderProjectTree(structure, folderPath, 1);
            }
        } catch (error) {
            console.error('Error loading folder content:', error);
            showError('Failed to load folder content');
            return;
        }
    }
    contentDiv.classList.toggle('hidden');
}

function openFile(path) {
    window.location.href = `/editor?path=${encodeURIComponent(path)}`;
}

// Create Item in Project Functions
function showCreateItemModal(type, path = '') {
    currentFolderPath = path || currentProjectPath;
    newItemTypeInput.value = type;
    newItemPathInput.value = currentFolderPath;
    newItemNameInput.value = '';
    
    const title = type === 'file' ? 'Create New File' : 'Create New Folder';
    document.getElementById('create-item-title').textContent = title;
    
    createProjectItemModal.classList.remove('hidden');
    newItemNameInput.focus();
}

function hideCreateItemModal() {
    createProjectItemModal.classList.add('hidden');
    newItemNameInput.value = '';
    currentFolderPath = '';
}

async function createProjectItem() {
    const name = newItemNameInput.value.trim();
    const path = newItemPathInput.value;
    const type = newItemTypeInput.value;
    
    if (!name) return;
    
    try {
        const response = await fetch('/api/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name,
                path,
                type
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to create item');
        }
        
        hideCreateItemModal();
        await loadProjectStructure(currentProjectPath);
    } catch (error) {
        console.error('Error creating item:', error);
        showError(error.message || 'Failed to create item');
    }
}

// Delete Functions
async function deleteProject(path) {
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
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
            throw new Error(data.detail || 'Failed to delete project');
        }
        
        await loadProjects();
    } catch (error) {
        console.error('Error deleting project:', error);
        showError(error.message || 'Failed to delete project');
    }
}

async function deleteProjectItem(path) {
    if (!confirm('Are you sure you want to delete this item?')) {
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
        
        await loadProjectStructure(currentProjectPath);
        if (path === currentProjectPath) {
            hideProjectExplorer();
            await loadProjects();  // Refresh main projects list
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        showError(error.message || 'Failed to delete item');
    }
}

// Collaborator Functions
async function showCollaboratorModal(projectId) {
    currentProjectId = projectId;
    collaboratorModal.classList.remove('hidden');
    await loadCollaborators();
}

function hideCollaboratorModal() {
    collaboratorModal.classList.add('hidden');
    currentProjectId = null;
}

async function loadCollaborators() {
    try {
        const response = await fetch(`/api/projects/${currentProjectId}/collaborators`);
        if (!response.ok) throw new Error('Failed to load collaborators');
        
        const data = await response.json();
        updateCollaboratorsList(data.collaborators);
    } catch (error) {
        console.error('Error loading collaborators:', error);
        showError('Failed to load collaborators');
    }
}

function updateCollaboratorsList(collaborators) {
    currentCollaborators.innerHTML = collaborators.map(collaborator => `
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span>${escapeHtml(collaborator.username)}</span>
            <button onclick="removeCollaborator(${collaborator.user_id})"
                    class="text-red-600 hover:text-red-900 text-sm">
                Remove
            </button>
        </div>
    `).join('');
}

async function addCollaborator() {
    const userId = collaboratorSelect.value;
    if (!userId || !currentProjectId) return;
    
    try {
        const response = await fetch(`/api/projects/${currentProjectId}/collaborators`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: parseInt(userId),
                action: 'add'
            })
        });
        
        if (!response.ok) throw new Error('Failed to add collaborator');
        
        await loadCollaborators();
        collaboratorSelect.value = '';
        await loadProjects();  // Refresh project list to show new collaborator
    } catch (error) {
        console.error('Error adding collaborator:', error);
        showError('Failed to add collaborator');
    }
}

async function removeCollaborator(userId) {
    if (!confirm('Are you sure you want to remove this collaborator?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${currentProjectId}/collaborators`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                action: 'remove'
            })
        });
        
        if (!response.ok) throw new Error('Failed to remove collaborator');
        
        await loadCollaborators();
        await loadProjects();  // Refresh project list to show updated collaborators
    } catch (error) {
        console.error('Error removing collaborator:', error);
        showError('Failed to remove collaborator');
    }
}

// Ownership Transfer Functions
function showTransferModal(projectId) {
    currentProjectId = projectId;
    transferModal.classList.remove('hidden');
    newOwnerSelect.focus();
}

function hideTransferModal() {
    transferModal.classList.add('hidden');
    currentProjectId = null;
    newOwnerSelect.value = '';
}

async function transferOwnership() {
    const newOwnerId = newOwnerSelect.value;
    if (!newOwnerId || !currentProjectId) return;
    
    if (!confirm('Are you sure you want to transfer ownership of this project?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${currentProjectId}/transfer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                new_owner_id: parseInt(newOwnerId)
            })
        });
        
        if (!response.ok) throw new Error('Failed to transfer ownership');
        
        hideTransferModal();
        await loadProjects();  // Refresh project list to show new owner
    } catch (error) {
        console.error('Error transferring ownership:', error);
        showError('Failed to transfer ownership');
    }
}

// Utility Functions
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showError(message) {
    alert(message);  // You can replace this with a more sophisticated error display
}

// Event Listeners
projectNameInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createProject();
    }
});

newItemNameInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createProjectItem();
    }
});

// Handle escape key to close modals
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        hideCreateProjectModal();
        hideProjectExplorer();
        hideCreateItemModal();
        hideCollaboratorModal();
        hideTransferModal();
    }
});

// Handle clicking outside modals to close them
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('fixed')) {
        hideCreateProjectModal();
        hideProjectExplorer();
        hideCreateItemModal();
        hideCollaboratorModal();
        hideTransferModal();
    }
});