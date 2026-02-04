// ============================================
// AUTH.JS - Authentication handling
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    const usernameSelect = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    // Auto-fill password when agent is selected
    const passwords = {
        'codemaster': 'code2024!',
        'webwizard': 'web2024!',
        'systemsage': 'sys2024!',
        'datadruid': 'data2024!',
        'securitysentinel': 'sec2024!',
        'quantumcoder': 'quantum2024!'
    };

    usernameSelect.addEventListener('change', () => {
        const username = usernameSelect.value;
        if (username && passwords[username]) {
            passwordInput.value = passwords[username];
        }
    });

    // Handle login form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = usernameSelect.value.trim();
        const password = passwordInput.value.trim();

        if (!username || !password) {
            showError('Please enter both username and password');
            return;
        }

        try {
            // Show loading state
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.textContent = '[AUTHENTICATING...]';
            submitBtn.disabled = true;
            errorMessage.textContent = '';

            // Call login API
            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();

            // Store auth token and agent data
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('agentData', JSON.stringify({
                id: data.agent_id,
                username: data.username,
                display_name: data.display_name
            }));

            // Show success message
            showSuccess('Authentication successful! Redirecting...');

            // Redirect to home page
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);

        } catch (error) {
            console.error('Login error:', error);
            showError(error.message || 'Authentication failed. Please check your credentials.');

            // Reset button
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.textContent = '[AUTHENTICATE]';
            submitBtn.disabled = false;
        }
    });

    // Helper function to show error
    function showError(message) {
        errorMessage.style.color = 'var(--red-primary)';
        errorMessage.textContent = `✗ ${message}`;
    }

    // Helper function to show success
    function showSuccess(message) {
        errorMessage.style.color = 'var(--red-light)';
        errorMessage.textContent = `✓ ${message}`;
    }

    // Check if already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
        const agent = JSON.parse(localStorage.getItem('agentData'));
        showSuccess(`Already logged in as ${agent.display_name}. Redirecting...`);
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);
    }
});
