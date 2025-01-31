const { useState, useEffect } = React;

function FolderStructure() {
    const [structure, setStructure] = useState({});
    const [error, setError] = useState('');
    const [selectedPath, setSelectedPath] = useState('');
    const [newItemName, setNewItemName] = useState('');
    const [showNewItemInput, setShowNewItemInput] = useState(false);
    const [newItemType, setNewItemType] = useState('');

    useEffect(() => {
        fetchStructure();
    }, []);

    const fetchStructure = async () => {
        try {
            const response = await fetch('/api/structure');
            if (!response.ok) throw new Error('Failed to fetch structure');
            const data = await response.json();
            setStructure(data);
        } catch (err) {
            setError('Failed to load folder structure');
        }
    };

    const handleSelect = (path, type) => {
        if (type === 'file') {
            window.location.href = `/editor?path=${encodeURIComponent(path)}`;
        } else {
            setSelectedPath(path === selectedPath ? '' : path);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!newItemName) return;

        try {
            const response = await fetch('/api/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newItemName,
                    type: newItemType,
                    path: selectedPath || '/'
                })
            });

            if (!response.ok) throw new Error('Failed to create item');
            
            setNewItemName('');
            setShowNewItemInput(false);
            fetchStructure();
        } catch (err) {
            setError('Failed to create new item');
        }
    };

    const handleDelete = async (path) => {
        if (!confirm('Are you sure you want to delete this item?')) return;

        try {
            const response = await fetch('/api/delete', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });

            if (!response.ok) throw new Error('Failed to delete item');
            fetchStructure();
        } catch (err) {
            setError('Failed to delete item');
        }
    };

    const renderTree = (node, path = '') => {
        return Object.entries(node).map(([key, value]) => {
            const currentPath = path ? `${path}/${key}` : key;
            const isFolder = typeof value === 'object';
            
            return React.createElement('div', { key: currentPath, className: 'ml-4' },
                React.createElement('div', { 
                    className: 'flex items-center gap-2 py-1 hover:bg-gray-100 rounded px-2' 
                },
                    React.createElement('span', { 
                        className: `w-4 h-4 ${isFolder ? 'text-blue-500' : 'text-gray-500'}`
                    }, isFolder ? '📁' : '📄'),
                    React.createElement('span', {
                        className: 'cursor-pointer flex-grow',
                        onClick: () => handleSelect(currentPath, isFolder ? 'folder' : 'file')
                    }, key),
                    React.createElement('span', {
                        className: 'text-red-500 cursor-pointer hover:text-red-700',
                        onClick: () => handleDelete(currentPath)
                    }, '🗑️')
                ),
                isFolder && selectedPath.startsWith(currentPath) && 
                    React.createElement('div', { className: 'ml-4' }, 
                        renderTree(value, currentPath)
                    )
            );
        });
    };

    return React.createElement('div', { className: 'p-4' },
        error && React.createElement('div', { 
            className: 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4' 
        }, error),
        
        React.createElement('div', { className: 'flex items-center gap-2 mb-4' },
            React.createElement('button', {
                className: 'bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600',
                onClick: () => setShowNewItemInput(true)
            }, '+ New')
        ),

        showNewItemInput && React.createElement('form', {
            onSubmit: handleCreate,
            className: 'mb-4 flex gap-2'
        },
            React.createElement('input', {
                type: 'text',
                value: newItemName,
                onChange: (e) => setNewItemName(e.target.value),
                placeholder: 'Name',
                className: 'border p-1 rounded'
            }),
            React.createElement('select', {
                value: newItemType,
                onChange: (e) => setNewItemType(e.target.value),
                className: 'border p-1 rounded'
            },
                React.createElement('option', { value: '' }, 'Select type'),
                React.createElement('option', { value: 'folder' }, 'Folder'),
                React.createElement('option', { value: 'file' }, 'File')
            ),
            React.createElement('button', {
                type: 'submit',
                className: 'bg-blue-500 text-white px-2 py-1 rounded'
            }, 'Create')
        ),

        React.createElement('div', { className: 'border rounded p-4' },
            renderTree(structure)
        )
    );
}

// Render the app
ReactDOM.render(
    React.createElement(FolderStructure),
    document.getElementById('root')
);