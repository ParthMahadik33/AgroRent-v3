// Chatbot functionality
class Chatbot {
    constructor() {
        this.isOpen = false;
        this.chatHistory = [];
        this.init();
    }

    init() {
        this.createChatbotUI();
        this.attachEventListeners();
    }

    createChatbotUI() {
        const chatbotHTML = `
            <div id="chatbot-container" class="chatbot-container">
                <div id="chatbot-window" class="chatbot-window">
                    <div class="chatbot-header">
                        <div class="chatbot-header-content">
                            <i class="fas fa-robot"></i>
                            <span>AgroRent Support</span>
                        </div>
                        <button id="chatbot-minimize" class="chatbot-btn-minimize">
                            <i class="fas fa-minus"></i>
                        </button>
                    </div>
                    <div id="chatbot-messages" class="chatbot-messages">
                        <div class="chatbot-message bot-message">
                            <div class="message-content">
                                <p>Hi! 👋 I'm your AgroRent assistant. How can I help you today?</p>
                            </div>
                        </div>
                    </div>
                    <div class="chatbot-input-container">
                        <input type="text" id="chatbot-input" class="chatbot-input" placeholder="Type your message...">
                        <button id="chatbot-send" class="chatbot-btn-send">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
                <button id="chatbot-toggle" class="chatbot-toggle">
                    <i class="fas fa-comments"></i>
                    <span class="chatbot-badge" id="chatbot-badge" style="display: none;">1</span>
                </button>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    attachEventListeners() {
        const toggleBtn = document.getElementById('chatbot-toggle');
        const minimizeBtn = document.getElementById('chatbot-minimize');
        const sendBtn = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggleBtn.addEventListener('click', () => this.toggleChatbot());
        minimizeBtn.addEventListener('click', () => this.toggleChatbot());
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    toggleChatbot() {
        const container = document.getElementById('chatbot-container');
        const window = document.getElementById('chatbot-window');
        
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            container.classList.add('chatbot-open');
            window.classList.add('chatbot-window-open');
            document.getElementById('chatbot-input').focus();
        } else {
            container.classList.remove('chatbot-open');
            window.classList.remove('chatbot-window-open');
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Clear input
        input.value = '';
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Show typing indicator
        const typingId = this.addTypingIndicator();
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            if (response.ok && data.response) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again later.', 'bot');
            }
        } catch (error) {
            this.removeTypingIndicator(typingId);
            this.addMessage('Sorry, I couldn\'t connect to the server. Please check your connection.', 'bot');
        }
    }

    addMessage(text, sender) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>${this.formatMessage(text)}</p>`;
        
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Store in history
        this.chatHistory.push({ text, sender });
    }

    addTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return 'typing-indicator';
    }

    removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    formatMessage(text) {
        // Use a placeholder to protect links during HTML escaping
        const linkPlaceholders = [];
        let placeholderIndex = 0;
        
        // Convert markdown-style links [text](url) to HTML links
        let formatted = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
            const placeholder = `__LINK_PLACEHOLDER_${placeholderIndex}__`;
            linkPlaceholders.push({
                placeholder: placeholder,
                html: `<a href="${this.escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="chatbot-link">${this.escapeHtml(linkText)}</a>`
            });
            placeholderIndex++;
            return placeholder;
        });
        
        // Convert plain URLs to clickable links (http://, https://, www.)
        formatted = formatted.replace(/(https?:\/\/[^\s<>"']+|www\.[^\s<>"']+)/g, (url) => {
            // Skip if this is already a placeholder
            if (url.includes('__LINK_PLACEHOLDER__')) {
                return url;
            }
            
            let href = url;
            // Add https:// if it starts with www.
            if (url.startsWith('www.')) {
                href = 'https://' + url;
            }
            const placeholder = `__LINK_PLACEHOLDER_${placeholderIndex}__`;
            linkPlaceholders.push({
                placeholder: placeholder,
                html: `<a href="${this.escapeHtml(href)}" target="_blank" rel="noopener noreferrer" class="chatbot-link">${this.escapeHtml(url)}</a>`
            });
            placeholderIndex++;
            return placeholder;
        });
        
        // Escape HTML (but preserve placeholders)
        formatted = formatted
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Restore links from placeholders
        linkPlaceholders.forEach(item => {
            formatted = formatted.replace(item.placeholder, item.html);
        });
        
        // Convert newlines to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new Chatbot();
});

