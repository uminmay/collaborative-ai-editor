// State
let currentUser = null;
let projects = [];
let currentProjectId = null;

// DOM Elements
const projectsList = document.getElementById('projects-list');
const emptyState = document.getElementById('empty-state');
const createProjectModal = document.getElementById('create-project-modal');
const collaboratorModal = document.getElementById('collaborator-modal');
const transferModal = document.getElementById('transfer-modal');
const projectNameInput = document.getElementById('project-name');
const collaboratorSelect = document.getElementById('collaborator-select');
const newOwnerSelect = document.getElementById('new-owner-select');
const currentCollaborators = document.getElementById('current-collaborators');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
});

// Project Loading
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
    if (projects.length === 0) {
        projectsList.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    projectsList.classList.remove('hidden');
    emptyState.classList.add('hidden');
    
    projectsList.innerHTML = projects.map(project => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatDate(project.created_at)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <a href="/editor?path=${encodeURIComponent(project.path)}" 
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

// Project Creation
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
        await loadProjects();
    } catch (error) {
        console.error('Error creating project:', error);
        showError(error.message || 'Failed to create project');
    }
}

// Project Deletion
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

// Collaborator Management
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

// Ownership Transfer
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