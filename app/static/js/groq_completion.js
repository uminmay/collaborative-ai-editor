class GroqCompletionManager {
    constructor(editor, websocket) {
        this.editor = editor;
        this.ws = websocket;
        this.currentCompletion = null;
        this.completionTimeout = null;
        this.isProcessingCompletion = false;
        
        this.completionStyles = {
            backgroundColor: '#f3f4f6',
            color: '#4b5563',
            fontStyle: 'italic'
        };
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Handle editor input events
        this.editor.addEventListener('input', () => {
            this.removeCompletion();
            this.requestCompletion();
        });
        
        // Handle tab key for accepting completions
        this.editor.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' && this.currentCompletion) {
                e.preventDefault();
                this.acceptCompletion();
            } else {
                this.removeCompletion();
            }
        });
    }
    
    showCompletion(completion, cursorPosition) {
        const beforeCursor = this.editor.value.substring(0, cursorPosition);
        const afterCursor = this.editor.value.substring(cursorPosition);
        
        // Create completion element
        const completionElement = document.createElement('div');
        completionElement.id = 'completion-suggestion';
        Object.assign(completionElement.style, {
            position: 'absolute',
            zIndex: '1000',
            backgroundColor: this.completionStyles.backgroundColor,
            color: this.completionStyles.color,
            fontStyle: this.completionStyles.fontStyle,
            padding: '4px',
            borderRadius: '4px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        });
        completionElement.textContent = completion;
        
        // Position the completion element
        const cursorCoords = this.getCaretCoordinates(cursorPosition);
        completionElement.style.left = `${cursorCoords.left}px`;
        completionElement.style.top = `${cursorCoords.top + 20}px`;
        
        // Remove any existing completion
        this.removeCompletion();
        
        document.body.appendChild(completionElement);
        this.currentCompletion = {
            text: completion,
            position: cursorPosition
        };
    }
    
    removeCompletion() {
        const completionElement = document.getElementById('completion-suggestion');
        if (completionElement) {
            completionElement.remove();
        }
        this.currentCompletion = null;
    }
    
    requestCompletion() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || this.isProcessingCompletion) {
            return;
        }
        
        const cursorPosition = this.editor.selectionStart;
        
        // Clear existing timeout
        if (this.completionTimeout) {
            clearTimeout(this.completionTimeout);
        }
        
        // Set new timeout for completion request
        this.completionTimeout = setTimeout(() => {
            this.ws.send(JSON.stringify({
                type: 'request_completion',
                content: this.editor.value,
                cursor_position: cursorPosition
            }));
            this.isProcessingCompletion = true;
        }, 500); // 500ms debounce
    }
    
    acceptCompletion() {
        if (!this.currentCompletion) {
            return;
        }
        
        const beforeCursor = this.editor.value.substring(0, this.currentCompletion.position);
        const afterCursor = this.editor.value.substring(this.currentCompletion.position);
        const newContent = beforeCursor + this.currentCompletion.text + afterCursor;
        
        this.editor.value = newContent;
        this.removeCompletion();
        
        // Save the accepted completion
        this.ws.send(JSON.stringify({
            type: 'accept_completion',
            content: newContent
        }));
        
        // Trigger editor update events
        this.editor.dispatchEvent(new Event('input'));
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'completion_suggestion') {
            this.isProcessingCompletion = false;
            if (data.completion) {
                this.showCompletion(data.completion, data.cursor_position);
            }
        }
    }
    
    getCaretCoordinates(position) {
        // Create a temporary element to calculate position
        const dummyElement = document.createElement('div');
        dummyElement.style.cssText = window.getComputedStyle(this.editor, null).cssText;
        dummyElement.style.height = 'auto';
        dummyElement.style.position = 'absolute';
        dummyElement.style.visibility = 'hidden';
        dummyElement.style.whiteSpace = 'pre-wrap';
        dummyElement.textContent = this.editor.value.substring(0, position);
        
        document.body.appendChild(dummyElement);
        const coordinates = {
            top: dummyElement.offsetHeight,
            left: dummyElement.offsetWidth
        };
        document.body.removeChild(dummyElement);
        
        return coordinates;
    }
}