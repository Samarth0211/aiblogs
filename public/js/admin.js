// ============================================
// ADMIN.JS - Admin panel functionality
// ============================================

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

class AdminPanel {
    constructor() {
        // Admin password (now verified via API)
        this.PASSWORD = 'admin123';

        // DOM elements
        this.authScreen = document.getElementById('authScreen');
        this.adminPanel = document.getElementById('adminPanel');
        this.authForm = document.getElementById('authForm');
        this.passwordInput = document.getElementById('passwordInput');
        this.logoutBtn = document.getElementById('logoutBtn');

        // Post form elements
        this.postForm = document.getElementById('postForm');
        this.postIdInput = document.getElementById('postId');
        this.titleInput = document.getElementById('titleInput');
        this.contentInput = document.getElementById('contentInput');
        this.tagsInput = document.getElementById('tagsInput');
        this.submitBtn = document.getElementById('submitBtn');
        this.cancelBtn = document.getElementById('cancelBtn');
        this.editorTitle = document.getElementById('editorTitle');

        // Posts list
        this.adminPostsList = document.getElementById('adminPostsList');

        // Edit mode state
        this.isEditMode = false;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuth();
    }

    // Setup event listeners
    setupEventListeners() {
        this.authForm.addEventListener('submit', (e) => this.handleAuth(e));
        this.logoutBtn.addEventListener('click', (e) => this.handleLogout(e));
        this.postForm.addEventListener('submit', (e) => this.handlePostSubmit(e));
        this.cancelBtn.addEventListener('click', () => this.cancelEdit());
    }

    // Check if already authenticated
    checkAuth() {
        const isAuthenticated = sessionStorage.getItem('blog_admin_auth');
        if (isAuthenticated === 'true') {
            this.showAdminPanel();
        }
    }

    // Handle authentication
    async handleAuth(e) {
        e.preventDefault();
        const password = this.passwordInput.value;

        try {
            const response = await fetch(`${API_BASE_URL}/api/auth`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password })
            });

            if (response.ok) {
                sessionStorage.setItem('blog_admin_auth', 'true');
                this.showAdminPanel();
            } else {
                alert('✖ INCORRECT PASSWORD');
                this.passwordInput.value = '';
                this.passwordInput.focus();
            }
        } catch (error) {
            console.error('Authentication error:', error);
            alert('✖ CONNECTION ERROR\n\nMake sure the backend server is running.');
        }
    }

    // Handle logout
    handleLogout(e) {
        e.preventDefault();
        sessionStorage.removeItem('blog_admin_auth');
        this.hideAdminPanel();
        this.passwordInput.value = '';
    }

    // Show admin panel
    showAdminPanel() {
        this.authScreen.style.display = 'none';
        this.adminPanel.style.display = 'block';
        this.loadAdminPosts();
    }

    // Hide admin panel
    hideAdminPanel() {
        this.authScreen.style.display = 'flex';
        this.adminPanel.style.display = 'none';
    }

    // Get posts from API
    async getPosts() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/posts`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching posts:', error);
            return [];
        }
    }

    // Load and display posts in admin panel
    async loadAdminPosts() {
        const posts = await this.getPosts();

        if (posts.length === 0) {
            this.adminPostsList.innerHTML = `
                <div class="admin-empty">
                    <p>NO POSTS YET</p>
                    <p style="margin-top: 10px; font-size: 12px;">Create your first post above ↑</p>
                </div>
            `;
            return;
        }

        // Sort by date, newest first
        posts.sort((a, b) => new Date(b.date) - new Date(a.date));

        this.adminPostsList.innerHTML = '';
        posts.forEach(post => {
            const postElement = this.createAdminPostElement(post);
            this.adminPostsList.appendChild(postElement);
        });
    }

    // Create admin post item element
    createAdminPostElement(post) {
        const div = document.createElement('div');
        div.className = 'admin-post-item';

        const formattedDate = this.formatDate(post.date);
        const tags = post.tags || [];

        div.innerHTML = `
            <div class="admin-post-info">
                <div class="admin-post-title">${this.escapeHTML(post.title)}</div>
                <div class="admin-post-meta">
                    [${formattedDate}]
                    ${tags.length > 0 ? `• Tags: ${tags.map(t => '#' + this.escapeHTML(t.trim())).join(', ')}` : ''}
                </div>
            </div>
            <div class="admin-post-actions">
                <button class="btn btn-small" data-action="edit" data-id="${post.id}">[EDIT]</button>
                <button class="btn btn-small" data-action="delete" data-id="${post.id}">[DELETE]</button>
            </div>
        `;

        // Add event listeners
        div.querySelector('[data-action="edit"]').addEventListener('click', () => this.editPost(post.id));
        div.querySelector('[data-action="delete"]').addEventListener('click', () => this.deletePost(post.id));

        return div;
    }

    // Handle post form submission
    handlePostSubmit(e) {
        e.preventDefault();

        const title = this.titleInput.value.trim();
        const content = this.contentInput.value.trim();
        const tagsString = this.tagsInput.value.trim();

        if (!title || !content) {
            alert('✖ TITLE AND CONTENT ARE REQUIRED');
            return;
        }

        // Parse tags
        const tags = tagsString
            ? tagsString.split(',').map(tag => tag.trim()).filter(tag => tag)
            : [];

        if (this.isEditMode) {
            // Update existing post
            this.updatePost({
                id: parseInt(this.postIdInput.value),
                title,
                content,
                tags
            });
        } else {
            // Create new post
            this.createPost({
                title,
                content,
                tags
            });
        }
    }

    // Create new post
    async createPost({ title, content, tags }) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/posts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, content, tags })
            });

            if (!response.ok) {
                throw new Error('Failed to create post');
            }

            alert('✓ POST CREATED SUCCESSFULLY');
            this.resetForm();
            await this.loadAdminPosts();
        } catch (error) {
            console.error('Error creating post:', error);
            alert('✖ FAILED TO CREATE POST\n\nPlease try again.');
        }
    }

    // Update existing post
    async updatePost({ id, title, content, tags }) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/posts/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, content, tags })
            });

            if (!response.ok) {
                throw new Error('Failed to update post');
            }

            alert('✓ POST UPDATED SUCCESSFULLY');
            this.resetForm();
            await this.loadAdminPosts();
        } catch (error) {
            console.error('Error updating post:', error);
            alert('✖ FAILED TO UPDATE POST\n\nPlease try again.');
        }
    }

    // Edit post
    async editPost(id) {
        const posts = await this.getPosts();
        const post = posts.find(p => p.id === id);

        if (!post) {
            alert('✖ POST NOT FOUND');
            return;
        }

        // Populate form with post data
        this.postIdInput.value = post.id;
        this.titleInput.value = post.title;
        this.contentInput.value = post.content;
        this.tagsInput.value = (post.tags || []).join(', ');

        // Switch to edit mode
        this.isEditMode = true;
        this.editorTitle.textContent = '// EDIT POST';
        this.submitBtn.textContent = '[UPDATE]';
        this.cancelBtn.style.display = 'inline-block';

        // Scroll to form
        window.scrollTo({ top: 0, behavior: 'smooth' });
        this.titleInput.focus();
    }

    // Delete post
    async deletePost(id) {
        const confirmDelete = confirm('⚠ DELETE THIS POST?\n\nThis action cannot be undone.');

        if (!confirmDelete) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/posts/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete post');
            }

            alert('✓ POST DELETED SUCCESSFULLY');
            await this.loadAdminPosts();

            // If we were editing this post, reset the form
            if (this.isEditMode && parseInt(this.postIdInput.value) === id) {
                this.resetForm();
            }
        } catch (error) {
            console.error('Error deleting post:', error);
            alert('✖ FAILED TO DELETE POST\n\nPlease try again.');
        }
    }

    // Cancel edit mode
    cancelEdit() {
        this.resetForm();
    }

    // Reset form to create mode
    resetForm() {
        this.postForm.reset();
        this.postIdInput.value = '';
        this.isEditMode = false;
        this.editorTitle.textContent = '// CREATE NEW POST';
        this.submitBtn.textContent = '[PUBLISH]';
        this.cancelBtn.style.display = 'none';
    }

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        const options = {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        };
        return date.toLocaleDateString('en-US', options).replace(',', '');
    }

    // Escape HTML to prevent XSS
    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Initialize admin panel when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AdminPanel();
});
