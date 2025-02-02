// Modal elements
const createProjectModal = document.getElementById('create-project-modal');
const collaboratorModal = document.getElementById('collaborator-modal');
const transferModal = document.getElementById('transfer-modal');
const projectNameInput = document.getElementById('project-name');
const collaboratorSelect = document.getElementById('collaborator-select');
const newOwnerSelect = document.getElementById('new-owner-select');
const currentCollaborators = document.getElementById('current-collaborators');

let currentProjectId = null;

// Project Management Functions
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
        window.location.reload();
    } catch (error) {
        console.error('Error creating project:', error);
        alert(error.message || 'Failed to create project');
    }
}

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
        
        window.location.reload();
    } catch (error) {
        console.error('Error deleting project:', error);
        alert(error.message || 'Failed to delete project');
    }
}

// Collaborator Management Functions
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
        if (!response.ok) {
            throw new Error('Failed to load collaborators');
        }
        
        const data = await response.json();
        updateCollaboratorsList(data.collaborators);
    } catch (error) {
        console.error('Error loading collaborators:', error);
        alert('Failed to load collaborators');
    }
}

function updateCollaboratorsList(collaborators) {
    currentCollaborators.innerHTML = collaborators.map(collaborator => `
        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span>${collaborator.username}</span>
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
        
        if (!response.ok) {
            throw new Error('Failed to add collaborator');
        }
        
        await loadCollaborators();
        collaboratorSelect.value = '';
    } catch (error) {
        console.error('Error adding collaborator:', error);
        alert('Failed to add collaborator');
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
        
        if (!response.ok) {
            throw new Error('Failed to remove collaborator');
        }
        
        await loadCollaborators();
    } catch (error) {
        console.error('Error removing collaborator:', error);
        alert('Failed to remove collaborator');
    }
}

// Ownership Transfer Functions
function showTransferModal(projectId) {
    currentProjectId = projectId;
    transferModal.classList.remove('hidden');
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
        
        if (!response.ok) {
            throw new Error('Failed to transfer ownership');
        }
        
        hideTransferModal();
        window.location.reload();
    } catch (error) {
        console.error('Error transferring ownership:', error);
        alert('Failed to transfer ownership');
    }
}

// Handle Enter key in modals
projectNameInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createProject();
    }
});