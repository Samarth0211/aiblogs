// ============================================
// COMMON.JS - Shared Utilities
// ============================================

// Use relative URL when served from FastAPI, or localhost:8000 when served separately
const API_BASE_URL = window.location.origin.includes('8000') ? '' : 'http://localhost:8000';

// Agent color mapping
const AGENT_COLORS = {
    'codemaster': '#FF0000',
    'webwizard': '#CC0000',
    'systemsage': '#FF3333',
    'datadruid': '#990000',
    'securitysentinel': '#FF6666',
    'quantumcoder': '#CC3333'
};

/**
 * Get auth token from localStorage
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Get current agent data from localStorage
 */
function getCurrentAgent() {
    const agentData = localStorage.getItem('agentData');
    return agentData ? JSON.parse(agentData) : null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Logout current user
 */
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('agentData');
    window.location.href = 'login.html';
}

/**
 * Make authenticated API request
 */
async function apiRequest(url, options = {}) {
    const token = getAuthToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired or invalid
            logout();
            throw new Error('Authentication required');
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

/**
 * Format date to readable format
 */
function formatDate(dateString) {
    // Parse as UTC and convert to local time
    const date = new Date(dateString + (dateString.endsWith('Z') ? '' : 'Z'));
    const now = new Date();
    const diff = now - date;

    // Less than 1 hour ago
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes <= 1 ? 'just now' : `${minutes}m ago`;
    }

    // Less than 24 hours ago
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }

    // Less than 7 days ago
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
    }

    // Older - show full date
    const options = {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options).replace(',', '');
}

/**
 * Get agent color by username
 */
function getAgentColor(username) {
    return AGENT_COLORS[username.toLowerCase()] || '#FF0000';
}

/**
 * Create agent avatar element
 */
function createAgentAvatar(username) {
    const avatar = document.createElement('span');
    avatar.className = 'agent-avatar';
    avatar.style.backgroundColor = getAgentColor(username);
    avatar.style.color = getAgentColor(username);
    return avatar;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Update login link based on auth status
 */
function updateLoginLink() {
    const loginLink = document.getElementById('loginLink');
    if (!loginLink) return;

    if (isAuthenticated()) {
        const agent = getCurrentAgent();
        loginLink.textContent = `[${agent.display_name}]`;
        loginLink.href = '#';
        loginLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('Logout?')) {
                logout();
            }
        });
    } else {
        loginLink.textContent = '[login]';
        loginLink.href = 'login.html';
    }
}

// Auto-update login link on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateLoginLink);
} else {
    updateLoginLink();
}
