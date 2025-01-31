const { useState, useEffect } = React;

function FolderStructure() {
    const [structure, setStructure] = useState({});
    const [error, setError] = useState('');
    const [expandedPaths, setExpandedPaths] = useState(new Set());
    const [selectedPath, setSelectedPath] = useState('');
    const [newItemName, setNewItemName] = useState('');
    const [showNewItemInput, setShowNewItemInput] = useState(false);
    const [newItemType, setNewItemType] = useState('');
    const [currentPath, setCurrentPath] = useState('');

    useEffect(() => {
        fetchStructure();
        document.addEventListener('click', handleOutsideClick);
        return () => {
            document.removeEventListener('click', handleOutsideClick);
        };
    }, []);

    const handleOutsideClick = (event) => {
        // Get the form container and folder structure container
        const formContainer = document.querySelector('.create-form-container');
        const structureContainer = document.querySelector('.folder-structure-container');

        // Don't deselect if clicking inside the form when it's open
        if (formContainer && formContainer.contains(event.target)) {
            return;
        }

        // Don't deselect if clicking the "New" button
        if (event.target.closest('.new-button-container')) {
            return;
        }

        // Only deselect if clicking outside both the form and structure
        if ((!structureContainer || !structureContainer.contains(event.target)) && 
            (!formContainer || !formContainer.contains(event.target))) {
            setSelectedPath('');
            setCurrentPath('');
        }
    };

    const fetchStructure = async () => {
        try {
            const response = await fetch('/api/structure');
            if (!response.ok) throw new Error('Failed to fetch structure');
            const data = await response.json();
            setStructure(data);
        } catch (err) {
            setError('Failed to load project structure');
        }
    };

    const handleSelect = (e, path, type) => {
        e.stopPropagation();
        if (type === 'file') {
            window.location.href = `/editor?path=${encodeURIComponent(path)}`;
        } else {
            setExpandedPaths(prev => {
                const newPaths = new Set(prev);
                if (newPaths.has(path)) {
                    newPaths.delete(path);
                } else {
                    newPaths.add(path);
                }
                return newPaths;
            });
            setSelectedPath(path);
            setCurrentPath(path);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!newItemName) return;

        const isRoot = !currentPath;
        const itemType = isRoot ? 'folder' : newItemType;

        if (isRoot && structure[newItemName]) {
            setError('A project with this name already exists');
            return;
        }

        try {
            const response = await fetch('/api/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newItemName,
                    type: itemType,
                    path: currentPath || '/'
                })
            });

            if (!response.ok) throw new Error('Failed to create item');
            
            setNewItemName('');
            setShowNewItemInput(false);
            setNewItemType('');
            fetchStructure();

            if (currentPath) {
                setExpandedPaths(prev => new Set([...prev, currentPath]));
            }
        } catch (err) {
            setError('Failed to create new item');
        }
    };

    const handleDelete = async (e, path) => {
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this item?')) return;

        try {
            const response = await fetch('/api/delete', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });

            if (!response.ok) throw new Error('Failed to delete item');
            fetchStructure();
            
            if (selectedPath.startsWith(path)) {
                setSelectedPath('');
                setCurrentPath('');
            }
        } catch (err) {
            setError('Failed to delete item');
        }
    };

    const getIndentLevel = (path) => {
        return path ? path.split('/').length - 1 : 0;
    };

    const renderCreateButton = () => {
        const isRoot = !currentPath;
        return React.createElement('div', { 
            className: 'flex items-center gap-2 mb-4 new-button-container'
        },
            React.createElement('button', {
                className: 'bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600',
                onClick: () => {
                    setShowNewItemInput(true);
                    setNewItemType(isRoot ? 'folder' : '');
                }
            }, isRoot ? '+ New Project' : '+ New')
        );
    };

    const renderForm = () => {
        const isRoot = !currentPath;
        return React.createElement('div', {
            className: 'create-form-container'
        },
            React.createElement('form', {
                onSubmit: handleCreate,
                className: 'mb-4 flex gap-2'
            },
                React.createElement('input', {
                    type: 'text',
                    value: newItemName,
                    onChange: (e) => setNewItemName(e.target.value),
                    placeholder: isRoot ? 'Project Name' : 'Name',
                    className: 'border p-1 rounded',
                    autoFocus: true
                }),
                !isRoot && React.createElement('select', {
                    value: newItemType,
                    onChange: (e) => setNewItemType(e.target.value),
                    className: 'border p-1 rounded',
                    required: true
                },
                    React.createElement('option', { value: '' }, 'Select type'),
                    React.createElement('option', { value: 'folder' }, 'Folder'),
                    React.createElement('option', { value: 'file' }, 'File')
                ),
                React.createElement('button', {
                    type: 'submit',
                    className: 'bg-blue-500 text-white px-2 py-1 rounded'
                }, 'Create'),
                React.createElement('button', {
                    type: 'button',
                    className: 'bg-gray-500 text-white px-2 py-1 rounded',
                    onClick: () => {
                        setShowNewItemInput(false);
                        setNewItemName('');
                        setNewItemType('');
                    }
                }, 'Cancel')
            )
        );
    };

    const renderTree = (node, path = '') => {
        return Object.entries(node).map(([key, value]) => {
            const currentPath = path ? `${path}/${key}` : key;
            const isFolder = typeof value === 'object';
            const isExpanded = expandedPaths.has(currentPath);
            const isSelected = selectedPath === currentPath;
            const indentLevel = getIndentLevel(currentPath);
            
            return React.createElement('div', { 
                key: currentPath,
                className: 'group'
            },
                React.createElement('div', { 
                    className: `flex items-center gap-2 py-2 px-2 rounded cursor-pointer 
                              ${isSelected ? 'bg-blue-100' : 'hover:bg-gray-100'}
                              ${indentLevel === 0 ? 'font-semibold' : ''}`,
                    onClick: (e) => handleSelect(e, currentPath, isFolder ? 'folder' : 'file'),
                    style: { marginLeft: `${indentLevel * 16}px` }
                },
                    React.createElement('span', { 
                        className: `${isFolder ? 'text-blue-500' : 'text-gray-500'}`
                    }, isFolder ? (isExpanded ? '📂' : '📁') : '📄'),
                    React.createElement('span', {
                        className: 'flex-grow'
                    }, key),
                    React.createElement('button', {
                        className: 'invisible group-hover:visible text-red-500 hover:text-red-700',
                        onClick: (e) => handleDelete(e, currentPath)
                    }, '🗑️')
                ),
                isFolder && isExpanded && value && 
                    renderTree(value, currentPath)
            );
        });
    };

    return React.createElement('div', { 
        className: 'p-4',
        onClick: handleOutsideClick
    },
        React.createElement('h1', { 
            className: 'text-2xl font-bold mb-4'
        }, 'Projects List'),

        error && React.createElement('div', { 
            className: 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 flex justify-between items-center'
        }, 
            React.createElement('span', {}, error),
            React.createElement('button', {
                className: 'text-red-700 hover:text-red-900',
                onClick: () => setError('')
            }, '×')
        ),
        
        renderCreateButton(),
        showNewItemInput && renderForm(),

        React.createElement('div', { 
            className: 'border rounded p-4 folder-structure-container'
        },
            Object.keys(structure).length === 0 
                ? React.createElement('p', { className: 'text-gray-500' }, 'No projects yet. Create one to get started!')
                : renderTree(structure)
        )
    );
}

// Render the app
ReactDOM.render(
    React.createElement(FolderStructure),
    document.getElementById('root')
);