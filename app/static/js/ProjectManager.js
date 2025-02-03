// ProjectManager.js
class ProjectManager {
    constructor() {
        // State
        this.currentUser = null;
        this.projects = [];
        this.currentProjectId = null;
        this.currentProjectPath = '';
        this.currentFolderPath = '';

        // Bind methods
        this.loadProjects = this.loadProjects.bind(this);
        this.createProject = this.createProject.bind(this);
        this.deleteProject = this.deleteProject.bind(this);
        this.handleCollaborators = this.handleCollaborators.bind(this);
        this.handleOwnershipTransfer = this.handleOwnershipTransfer.bind(this);
        this.handleProjectExplorer = this.handleProjectExplorer.bind(this);
        this.init = this.init.bind(this);

        // Initialize
        this.init();
    }

    init() {
        this.loadProjects();
        this.setupEventListeners();
        this.setupModalHandlers();
    }

    setupModalHandlers() {
        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('fixed')) {
                e.target.classList.add('hidden');
            }
        });

        // Close modals on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.fixed').forEach(modal => {
                    modal.classList.add('hidden');
                });
            }
        });
    }

    setupEventListeners() {
        // Create Project Button
        document.getElementById('createProjectBtn')?.addEventListener('click', () => {
            const modal = document.getElementById('create-project-modal');
            modal.classList.remove('hidden');
            document.getElementById('project-name')?.focus();
        });

        // Create Project Form
        document.getElementById('createProjectForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nameInput = document.getElementById('project-name');
            if (await this.createProject(nameInput.value)) {
                document.getElementById('create-project-modal').classList.add('hidden');
                nameInput.value = '';
            }
        });

        // Cancel Create Project
        document.getElementById('cancelCreateProject')?.addEventListener('click', () => {
            const modal = document.getElementById('create-project-modal');
            modal.classList.add('hidden');
            document.getElementById('project-name').value = '';
        });

        // Collaborator Modal
        document.getElementById('addCollaboratorBtn')?.addEventListener('click', () => {
            const select = document.getElementById('collaborator-select');
            if (select.value) {
                this.handleCollaborators(this.currentProjectId, 'add', parseInt(select.value));
            }
        });

        // Transfer Modal
        document.getElementById('confirmTransfer')?.addEventListener('click', () => {
            const select = document.getElementById('new-owner-select');
            if (select.value) {
                this.handleOwnershipTransfer(this.currentProjectId, select.value);
            }
        });
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (!response.ok) throw new Error('Failed to load projects');
            
            const data = await response.json();
            this.currentUser = data.user;
            this.projects = data.projects;
            
            this.renderProjects();
        } catch (error) {
            console.error('Error loading projects:', error);
            this.showError('Failed to load projects');
        }
    }

    renderProjects() {
        const projectsList = document.getElementById('projects-list');
        const emptyState = document.getElementById('empty-state');
        const tableContainer = projectsList?.closest('.bg-white.rounded-lg.shadow');
        
        if (!this.projects?.length) {
            if (tableContainer) tableContainer.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (tableContainer) tableContainer.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        
        if (projectsList) {
            projectsList.innerHTML = this.projects.map(project => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${this.formatDate(project.created_at)}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <a href="#" onclick="projectManager.handleProjectClick('${project.path}'); return false;" 
                           class="text-blue-600 hover:text-blue-900">
                            ${this.escapeHtml(project.name)}
                        </a>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${this.escapeHtml(project.owner.username)}
                        ${project.is_owner ? '<span class="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Owner</span>' : ''}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center space-x-2">
                            ${project.collaborators.map(collab => `
                                <span class="inline-flex items-center justify-center h-8 w-8 rounded-full bg-gray-500 text-white text-sm" 
                                      title="${this.escapeHtml(collab.username)}">
                                    ${this.escapeHtml(collab.username.substring(0, 2).toUpperCase())}
                                </span>
                            `).join('')}
                            ${(project.is_owner || this.currentUser.is_admin) ? `
                                <button onclick="projectManager.showCollaboratorModal(${project.id})"
                                        class="text-sm text-blue-600 hover:text-blue-900 ml-2">
                                    Manage
                                </button>
                            ` : ''}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <div class="flex items-center space-x-4">
                            ${(project.is_owner || this.currentUser.is_admin) ? `
                                <button onclick="projectManager.deleteProject('${project.path}')"
                                        class="text-red-600 hover:text-red-900">
                                    Delete
                                </button>
                            ` : ''}
                            ${this.currentUser.is_admin ? `
                                <button onclick="projectManager.showTransferModal(${project.id})"
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

    async createProject(name) {
        if (!name.trim()) return false;
        
        try {
            const response = await fetch('/api/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name.trim(),
                    path: '/',
                    type: 'folder'
                })
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to create project');
            }
            
            await this.loadProjects();
            return true;
        } catch (error) {
            console.error('Error creating project:', error);
            this.showError(error.message || 'Failed to create project');
            return false;
        }
    }

    async deleteProject(path) {
        if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
            return false;
        }
        
        try {
            const response = await fetch('/api/delete', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to delete project');
            }
            
            await this.loadProjects();
            return true;
        } catch (error) {
            console.error('Error deleting project:', error);
            this.showError(error.message || 'Failed to delete project');
            return false;
        }
    }

    async handleCollaborators(projectId, action, userId = null) {
        if (action === 'load') {
            this.showCollaboratorModal(projectId);
            return;
        }

        try {
            const response = await fetch(`/api/projects/${projectId}/collaborators`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    action: action
                })
            });
            
            if (!response.ok) throw new Error(`Failed to ${action} collaborator`);
            
            // Refresh collaborators list
            const collabResponse = await fetch(`/api/projects/${projectId}/collaborators`);
            if (!collabResponse.ok) throw new Error('Failed to load collaborators');
            
            const data = await collabResponse.json();
            this.updateCollaboratorsList(data.collaborators);
            
            await this.loadProjects();
            return true;
        } catch (error) {
            console.error('Collaborator operation error:', error);
            this.showError(error.message);
            return false;
        }
    }

    showCollaboratorModal(projectId) {
        this.currentProjectId = projectId;
        const modal = document.getElementById('collaborator-modal');
        modal.classList.remove('hidden');
        this.loadCollaboratorsList();
    }

    async loadCollaboratorsList() {
        try {
            const response = await fetch(`/api/projects/${this.currentProjectId}/collaborators`);
            if (!response.ok) throw new Error('Failed to load collaborators');
            
            const data = await response.json();
            this.updateCollaboratorsList(data.collaborators);
        } catch (error) {
            console.error('Error loading collaborators:', error);
            this.showError('Failed to load collaborators');
        }
    }

    updateCollaboratorsList(collaborators) {
        const container = document.getElementById('current-collaborators');
        if (container) {
            container.innerHTML = collaborators.map(collaborator => `
                <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span>${this.escapeHtml(collaborator.username)}</span>
                    <button onclick="projectManager.handleCollaborators(${this.currentProjectId}, 'remove', ${collaborator.user_id})"
                            class="text-red-600 hover:text-red-900 text-sm">
                        Remove
                    </button>
                </div>
            `).join('');
        }
    }

    showTransferModal(projectId) {
        this.currentProjectId = projectId;
        document.getElementById('transfer-modal').classList.remove('hidden');
    }

    async handleOwnershipTransfer(projectId, newOwnerId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/transfer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_owner_id: parseInt(newOwnerId) })
            });
            
            if (!response.ok) throw new Error('Failed to transfer ownership');
            
            document.getElementById('transfer-modal').classList.add('hidden');
            await this.loadProjects();
            return true;
        } catch (error) {
            console.error('Error transferring ownership:', error);
            this.showError('Failed to transfer ownership');
            return false;
        }
    }

    handleProjectClick(path) {
        window.location.href = `/editor?path=${encodeURIComponent(path)}`;
    }

    // Utility Methods
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    showError(message) {
        alert(message);
    }

    toggleModal(modalId, show = true) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.toggle('hidden', !show);
            if (show) {
                const input = modal.querySelector('input');
                if (input) input.focus();
            }
        }
    }
}

// Initialize and export
const projectManager = new ProjectManager();
export default projectManager;

// Make it available globally for onclick handlers
window.projectManager = projectManager;