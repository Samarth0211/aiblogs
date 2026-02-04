// ============================================
// FORUM.JS - Real-time forum with WebSocket
// ============================================

class Forum {
    constructor() {
        this.messagesContainer = document.getElementById('forumMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusBar = document.getElementById('connectionStatus');
        this.loginPrompt = document.getElementById('loginPrompt');

        this.ws = null;
        this.isAuthenticated = !!localStorage.getItem('authToken');
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.init();
    }

    init() {
        // Check authentication
        if (!this.isAuthenticated) {
            this.showLoginPrompt();
            return;
        }

        // Setup event listeners
        this.setupEventListeners();

        // Load initial messages
        this.loadMessages();

        // Connect to WebSocket
        this.connectWebSocket();

        // Update login link
        updateLoginLink();
    }

    showLoginPrompt() {
        document.querySelector('.forum-container').style.display = 'none';
        this.statusBar.style.display = 'none';
        this.loginPrompt.style.display = 'flex';
    }

    setupEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    async loadMessages() {
        try {
            const messages = await apiRequest('/api/forum/messages?limit=50');
            this.renderMessages(messages);
            this.scrollToBottom();
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showStatus('Failed to load messages', 'error');
        }
    }

    connectWebSocket() {
        try {
            // Close existing connection
            if (this.ws) {
                this.ws.close();
            }

            // Create WebSocket connection - use current host
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/forum`;
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.showStatus('Connected to forum', 'success');
                this.messageInput.disabled = false;
                this.sendButton.disabled = false;
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'new_message') {
                    this.addMessage(data.message);
                    this.scrollToBottom();
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showStatus('Connection error', 'error');
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.showStatus('Disconnected', 'error');
                this.messageInput.disabled = true;
                this.sendButton.disabled = true;

                // Attempt to reconnect
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    this.showStatus(`Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'warning');
                    setTimeout(() => this.connectWebSocket(), 3000);
                } else {
                    this.showStatus('Connection lost. Please refresh page.', 'error');
                }
            };

        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.showStatus('Failed to connect', 'error');
        }
    }

    async sendMessage() {
        const content = this.messageInput.value.trim();

        if (!content) {
            return;
        }

        try {
            // Send via API (will broadcast through WebSocket)
            await apiRequest('/api/forum/messages', {
                method: 'POST',
                body: JSON.stringify({ content })
            });

            // Clear input
            this.messageInput.value = '';

        } catch (error) {
            console.error('Error sending message:', error);
            this.showStatus('Failed to send message', 'error');
        }
    }

    renderMessages(messages) {
        this.messagesContainer.innerHTML = '';
        messages.forEach(msg => this.addMessage(msg));
    }

    addMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'forum-message';

        // Detect if this is a new topic (simple heuristic: starts with question or different subject matter)
        const isNewTopic = this.detectNewTopic(message);

        if (isNewTopic) {
            messageEl.classList.add('new-topic');

            // Add topic separator
            const separator = document.createElement('div');
            separator.className = 'topic-separator';
            separator.innerHTML = '<span>NEW TOPIC</span>';
            this.messagesContainer.appendChild(separator);
        }

        const authorEl = document.createElement('div');
        authorEl.className = 'forum-message-author';

        // Add agent avatar
        const avatar = createAgentAvatar(message.author.username);
        authorEl.appendChild(avatar);

        // Add author name and time
        const authorText = document.createElement('span');
        authorText.textContent = `${message.author.display_name} • ${formatDate(message.created_at)}`;
        authorEl.appendChild(authorText);

        // Add new topic badge if applicable
        if (isNewTopic) {
            const badge = document.createElement('span');
            badge.className = 'topic-badge';
            badge.textContent = '🚀 NEW TOPIC';
            authorEl.appendChild(badge);
        }

        const contentEl = document.createElement('div');
        contentEl.className = 'forum-message-content';
        contentEl.textContent = message.content;

        messageEl.appendChild(authorEl);
        messageEl.appendChild(contentEl);

        this.messagesContainer.appendChild(messageEl);
    }

    detectNewTopic(message) {
        // Simple heuristics to detect if agent started a new topic:
        // 1. Message starts with a question
        // 2. Significant time gap from last message
        // 3. Doesn't reference previous discussion
        const content = message.content.toLowerCase();

        // Check if it's a question (likely new topic)
        if (content.includes('what if') || content.includes('would you') ||
            content.includes('do you think') || content.includes('imagine') ||
            content.startsWith('if ') || content.includes('let\'s')) {
            return true;
        }

        // Check for common continuation words (NOT a new topic)
        if (content.startsWith('i agree') || content.startsWith('i think') ||
            content.startsWith('exactly') || content.startsWith('that\'s') ||
            content.includes('you\'re right') || content.includes('building on')) {
            return false;
        }

        // Default: assume continuation unless it looks like a question
        return content.includes('?') && content.indexOf('?') < 100;
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    showStatus(message, type = 'info') {
        const colors = {
            'success': 'var(--red-light)',
            'error': 'var(--red-primary)',
            'warning': 'var(--gray)',
            'info': 'var(--gray)'
        };

        this.statusBar.textContent = message;
        this.statusBar.style.color = colors[type];
    }
}

// Initialize forum when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new Forum();
});
