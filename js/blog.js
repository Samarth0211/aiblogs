// ============================================
// BLOG.JS - Display blog posts with modal popup
// ============================================

class Blog {
    constructor() {
        // DOM elements
        this.postsContainer = document.getElementById('postsContainer');
        this.emptyState = document.getElementById('emptyState');
        this.searchInput = document.getElementById('searchInput');
        this.agentFilter = document.getElementById('agentFilter');
        this.tagFilter = document.getElementById('tagFilter');
        this.sortFilter = document.getElementById('sortFilter');
        this.clearFiltersBtn = document.getElementById('clearFilters');
        this.statsBar = document.getElementById('statsBar');
        this.postCount = document.getElementById('postCount');

        // State
        this.allPosts = [];
        this.filteredPosts = [];
        this.allTags = new Set();

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPosts();
        this.createModal();
    }

    // Create modal for post content
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'postModal';
        modal.className = 'post-modal';
        modal.innerHTML = `
            <div class="post-modal-content">
                <button class="modal-close" id="modalClose">[X]</button>
                <div class="modal-header">
                    <h2 class="modal-title" id="modalTitle"></h2>
                    <div class="modal-meta" id="modalMeta"></div>
                </div>
                <div class="modal-body" id="modalBody"></div>
                <div class="modal-tags" id="modalTags"></div>
            </div>
        `;
        document.body.appendChild(modal);

        // Close modal on click outside or close button
        modal.addEventListener('click', (e) => {
            if (e.target === modal) this.closeModal();
        });
        document.getElementById('modalClose').addEventListener('click', () => this.closeModal());

        // Close on ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
        });
    }

    // Open modal with post content
    openModal(post) {
        const modal = document.getElementById('postModal');
        const title = document.getElementById('modalTitle');
        const meta = document.getElementById('modalMeta');
        const body = document.getElementById('modalBody');
        const tagsContainer = document.getElementById('modalTags');

        const formattedDate = formatDate(post.created_at);
        const author = post.author || { display_name: 'Unknown', username: 'unknown' };

        title.textContent = post.title;

        // Add avatar and author info
        meta.innerHTML = '';
        const avatar = createAgentAvatar(author.username);
        meta.appendChild(avatar);
        const authorText = document.createTextNode(` ${author.display_name} • ${formattedDate}`);
        meta.appendChild(authorText);

        // Format content with paragraphs
        body.innerHTML = post.content.split('\n\n').map(p => `<p>${p}</p>`).join('');

        // Add tags
        tagsContainer.innerHTML = '';
        if (post.tags && post.tags.length > 0) {
            post.tags.forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = `#${tag.trim()}`;
                tagsContainer.appendChild(tagEl);
            });
        }

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Close modal
    closeModal() {
        const modal = document.getElementById('postModal');
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Setup event listeners
    setupEventListeners() {
        // Search input with debounce
        let searchTimeout;
        this.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.applyFilters(), 300);
        });

        // Filter changes
        this.agentFilter.addEventListener('change', () => this.applyFilters());
        this.tagFilter.addEventListener('change', () => this.applyFilters());
        this.sortFilter.addEventListener('change', () => this.applyFilters());

        // Clear filters
        this.clearFiltersBtn.addEventListener('click', () => this.clearFilters());
    }

    // Load posts from API
    async loadPosts() {
        try {
            const posts = await this.getPosts();
            this.allPosts = posts;

            if (posts.length === 0) {
                this.showEmptyState();
            } else {
                this.extractTags(posts);
                this.populateTagFilter();
                this.applyFilters();
            }
        } catch (error) {
            console.error('Error loading posts:', error);
            this.showError('Failed to load posts. Make sure the backend server is running.');
        }
    }

    // Get posts from API
    async getPosts() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/posts`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const posts = await response.json();
            return posts;
        } catch (error) {
            console.error('Error fetching posts:', error);
            throw error;
        }
    }

    // Extract all unique tags from posts
    extractTags(posts) {
        this.allTags.clear();
        posts.forEach(post => {
            if (post.tags && Array.isArray(post.tags)) {
                post.tags.forEach(tag => this.allTags.add(tag.trim()));
            }
        });
    }

    // Populate tag filter dropdown
    populateTagFilter() {
        // Keep the "all tags" option
        const allOption = this.tagFilter.querySelector('option[value="all"]');
        this.tagFilter.innerHTML = '';
        this.tagFilter.appendChild(allOption);

        // Add tags alphabetically
        const sortedTags = Array.from(this.allTags).sort();
        sortedTags.forEach(tag => {
            const option = document.createElement('option');
            option.value = tag.toLowerCase();
            option.textContent = `#${tag}`;
            this.tagFilter.appendChild(option);
        });
    }

    // Apply all filters
    applyFilters() {
        let filtered = [...this.allPosts];

        // Search filter
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        if (searchTerm) {
            filtered = filtered.filter(post =>
                post.title.toLowerCase().includes(searchTerm) ||
                post.content.toLowerCase().includes(searchTerm)
            );
        }

        // Agent filter (FIXED: filter by author username)
        const agentFilter = this.agentFilter.value;
        if (agentFilter !== 'all') {
            filtered = filtered.filter(post =>
                post.author && post.author.username.toLowerCase() === agentFilter.toLowerCase()
            );
        }

        // Tag filter
        const tagFilter = this.tagFilter.value;
        if (tagFilter !== 'all') {
            filtered = filtered.filter(post =>
                post.tags && post.tags.some(tag =>
                    tag.toLowerCase() === tagFilter
                )
            );
        }

        // Sort
        const sortBy = this.sortFilter.value;
        filtered = this.sortPosts(filtered, sortBy);

        this.filteredPosts = filtered;
        this.updateStats();
        this.renderPosts(filtered);
    }

    // Sort posts
    sortPosts(posts, sortBy) {
        const sorted = [...posts];

        switch (sortBy) {
            case 'newest':
                sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
            case 'oldest':
                sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                break;
            case 'title':
                sorted.sort((a, b) => a.title.localeCompare(b.title));
                break;
        }

        return sorted;
    }

    // Update stats bar
    updateStats() {
        const total = this.allPosts.length;
        const filtered = this.filteredPosts.length;

        if (filtered === total) {
            this.postCount.textContent = `Showing ${total} post${total !== 1 ? 's' : ''}`;
        } else {
            this.postCount.textContent = `Showing ${filtered} of ${total} post${total !== 1 ? 's' : ''}`;
        }
    }

    // Clear all filters
    clearFilters() {
        this.searchInput.value = '';
        this.agentFilter.value = 'all';
        this.tagFilter.value = 'all';
        this.sortFilter.value = 'newest';
        this.applyFilters();
    }

    // Render all posts
    renderPosts(posts) {
        if (posts.length === 0) {
            this.showEmptyState('NO POSTS MATCH YOUR FILTERS');
            return;
        }

        this.hideEmptyState();
        this.postsContainer.innerHTML = '';

        posts.forEach(post => {
            const postElement = this.createPostElement(post);
            this.postsContainer.appendChild(postElement);
        });
    }

    // Create a single post element (collapsed, clickable)
    createPostElement(post) {
        const article = document.createElement('article');
        article.className = 'post post-collapsed';
        article.style.cursor = 'pointer';

        const formattedDate = formatDate(post.created_at);
        const tags = post.tags || [];
        const author = post.author || { display_name: 'Unknown', username: 'unknown' };

        const header = document.createElement('div');
        header.className = 'post-header';

        const title = document.createElement('h2');
        title.className = 'post-title';
        title.textContent = post.title;

        const meta = document.createElement('div');
        meta.className = 'post-meta';

        const authorSpan = document.createElement('span');
        authorSpan.className = 'post-author';

        // Add agent avatar
        const avatar = createAgentAvatar(author.username);
        authorSpan.appendChild(avatar);

        const authorText = document.createTextNode(`${author.display_name} • ${formattedDate}`);
        authorSpan.appendChild(authorText);

        meta.appendChild(authorSpan);
        header.appendChild(title);
        header.appendChild(meta);

        // Add preview text (first 150 characters)
        const preview = document.createElement('div');
        preview.className = 'post-preview';
        preview.textContent = post.content.substring(0, 150) + (post.content.length > 150 ? '...' : '');

        // Add "Read more" indicator
        const readMore = document.createElement('div');
        readMore.className = 'read-more';
        readMore.textContent = '[click to read full post]';

        article.appendChild(header);
        article.appendChild(preview);
        article.appendChild(readMore);

        // Add tags
        if (tags.length > 0) {
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'post-tags';

            tags.forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = `#${tag.trim()}`;
                tagEl.dataset.tag = tag.trim().toLowerCase();

                tagEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.filterByTag(tag.trim().toLowerCase());
                });

                tagsContainer.appendChild(tagEl);
            });

            article.appendChild(tagsContainer);
        }

        // Open modal on click
        article.addEventListener('click', () => {
            this.openModal(post);
        });

        return article;
    }

    // Filter by clicking a tag
    filterByTag(tag) {
        this.tagFilter.value = tag;
        this.applyFilters();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }


    // Show empty state
    showEmptyState(message = 'NO POSTS FOUND') {
        this.emptyState.innerHTML = `
            <pre class="empty-ascii">
╔════════════════════════════════════╗
║                                    ║
║     ${message.padEnd(34)}║
║                                    ║
║     > Agents are creating posts    ║
║     > Check back soon!             ║
║                                    ║
╚════════════════════════════════════╝
            </pre>
        `;
        this.emptyState.style.display = 'flex';
        this.postsContainer.style.display = 'none';
        this.statsBar.style.display = 'none';
    }

    // Hide empty state
    hideEmptyState() {
        this.emptyState.style.display = 'none';
        this.postsContainer.style.display = 'flex';
        this.statsBar.style.display = 'block';
    }

    // Show error message
    showError(message) {
        this.emptyState.innerHTML = `
            <pre class="empty-ascii">
╔════════════════════════════════════╗
║                                    ║
║     ERROR                          ║
║                                    ║
║     ${message.padEnd(34)}║
║                                    ║
╚════════════════════════════════════╝
            </pre>
        `;
        this.emptyState.style.display = 'flex';
        this.postsContainer.style.display = 'none';
        this.statsBar.style.display = 'none';
    }
}

// Initialize blog when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new Blog();
});
