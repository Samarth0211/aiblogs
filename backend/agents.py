"""
AI Agents - Automated Blog Posting System
5 AI agents with different personalities that create posts and interact
"""

import json
import random
import requests
from datetime import datetime
from typing import List, Dict
from backend.agents_config import get_agent_config

# API Configuration
API_BASE_URL = "http://localhost:8000"

# AI Agent Personalities
AGENTS = {
    "CodeMaster": {
        "name": "CodeMaster",
        "focus": "algorithms and data structures",
        "topics": [
            "Understanding Binary Search Trees in Depth",
            "Dynamic Programming: From Fibonacci to Complex Problems",
            "Graph Algorithms: BFS vs DFS Explained",
            "Time Complexity Analysis: Big O Notation Mastery",
            "Implementing a LRU Cache from Scratch",
            "Hash Tables: Collision Resolution Strategies",
            "Sorting Algorithms: When to Use Which",
            "Recursion Patterns Every Developer Should Know"
        ],
        "tags": ["algorithms", "data-structures", "computer-science"],
        "style": "technical and precise"
    },

    "WebWizard": {
        "name": "WebWizard",
        "focus": "web development and frontend",
        "topics": [
            "Modern CSS Grid: Building Responsive Layouts",
            "JavaScript Event Loop Demystified",
            "React Hooks: useEffect Best Practices",
            "Web Performance: Core Web Vitals Optimization",
            "Async/Await vs Promises: What You Need to Know",
            "Building Accessible Web Applications",
            "CSS Animation Techniques for Better UX",
            "State Management in Modern Web Apps"
        ],
        "tags": ["web-dev", "javascript", "frontend"],
        "style": "practical and example-driven"
    },

    "SystemSage": {
        "name": "SystemSage",
        "focus": "systems programming and backend",
        "topics": [
            "Understanding Linux Process Management",
            "Memory Management: Stack vs Heap",
            "Building RESTful APIs: Best Practices",
            "Database Indexing Strategies for Performance",
            "Concurrency vs Parallelism Explained",
            "Docker Containerization: A Deep Dive",
            "Load Balancing Techniques in Distributed Systems",
            "Database Transactions and ACID Properties"
        ],
        "tags": ["backend", "systems", "devops"],
        "style": "architectural and strategic"
    },

    "DataDruid": {
        "name": "DataDruid",
        "focus": "data science and machine learning",
        "topics": [
            "Introduction to Neural Networks",
            "Data Preprocessing: The Unsung Hero of ML",
            "Understanding Gradient Descent Optimization",
            "Feature Engineering Techniques That Matter",
            "Cross-Validation Strategies in Practice",
            "Overfitting vs Underfitting: Finding Balance",
            "Time Series Analysis Fundamentals",
            "Dimensionality Reduction with PCA"
        ],
        "tags": ["machine-learning", "data-science", "ai"],
        "style": "analytical and mathematical"
    },

    "SecuritySentinel": {
        "name": "SecuritySentinel",
        "focus": "security and best practices",
        "topics": [
            "Common Web Vulnerabilities: OWASP Top 10",
            "Authentication vs Authorization Explained",
            "SQL Injection: Prevention Techniques",
            "Cryptography Basics Every Developer Should Know",
            "Secure API Design Principles",
            "XSS Attacks and How to Prevent Them",
            "HTTPS and TLS: Security in Transit",
            "Password Hashing: bcrypt vs Argon2"
        ],
        "tags": ["security", "best-practices", "cybersecurity"],
        "style": "security-focused and cautionary"
    }
}

class BlogAgent:
    """Represents an AI agent that creates blog posts"""

    def __init__(self, agent_id: str, config: Dict):
        self.agent_id = agent_id
        self.name = config["name"]
        self.focus = config["focus"]
        self.topics = config["topics"]
        self.tags = config["tags"]
        self.style = config["style"]
        self.used_topics = []
        self.api_token = None
        # try to load username/password from agents_config (optional)
        cfg = get_agent_config(agent_id.lower())
        self._login_username = cfg.get('username') if cfg else None
        self._login_password = cfg.get('password') if cfg else None

    def get_existing_posts(self) -> List[Dict]:
        """Fetch existing posts from the API"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/posts")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"[{self.name}] Error fetching posts: {e}")
            return []

    def get_available_topic(self) -> str:
        """Get a topic that hasn't been used yet"""
        available = [t for t in self.topics if t not in self.used_topics]
        if not available:
            # Reset if all topics used
            self.used_topics = []
            available = self.topics

        topic = random.choice(available)
        self.used_topics.append(topic)
        return topic

    def find_related_post(self, posts: List[Dict]) -> Dict:
        """Find a post from another agent to reference"""
        other_posts = [p for p in posts if self.name not in p.get('title', '')]
        if other_posts:
            return random.choice(other_posts[-5:])  # Recent posts
        return None

    def generate_content(self, topic: str, related_post: Dict = None) -> str:
        """Generate blog post content"""
        content_parts = []

        # Introduction
        intros = [
            f"Today I want to dive deep into {topic.lower()}.",
            f"Let's explore {topic.lower()} and understand the fundamentals.",
            f"In this post, we'll break down {topic.lower()}.",
            f"Understanding {topic.lower()} is crucial for every developer.",
        ]
        content_parts.append(random.choice(intros))
        content_parts.append("")

        # Main content
        content_parts.append("## Key Concepts")
        content_parts.append("")

        if "algorithms" in self.focus.lower():
            content_parts.extend([
                "When working with this concept, we need to consider:",
                "- Time complexity and space trade-offs",
                "- Edge cases and boundary conditions",
                "- Real-world applications and use cases",
                "",
                "The implementation requires careful consideration of data structures and efficiency.",
            ])
        elif "web" in self.focus.lower():
            content_parts.extend([
                "In modern web development, this involves:",
                "- Browser compatibility considerations",
                "- Performance optimization techniques",
                "- User experience best practices",
                "",
                "Let's look at how this works in practice with real examples.",
            ])
        elif "system" in self.focus.lower():
            content_parts.extend([
                "From a systems perspective, we need to think about:",
                "- Scalability and reliability",
                "- Resource management",
                "- Distributed system considerations",
                "",
                "The architecture should be designed with these principles in mind.",
            ])
        elif "data" in self.focus.lower():
            content_parts.extend([
                "From a data science viewpoint:",
                "- Statistical significance",
                "- Model accuracy and validation",
                "- Feature selection strategies",
                "",
                "The mathematical foundation is essential for understanding this concept.",
            ])
        elif "security" in self.focus.lower():
            content_parts.extend([
                "From a security standpoint, consider:",
                "- Potential attack vectors",
                "- Defense in depth strategies",
                "- Security best practices",
                "",
                "⚠ Never compromise on security - it's not optional.",
            ])

        content_parts.append("")
        content_parts.append("## Practical Implementation")
        content_parts.append("")
        content_parts.append("Here's how you can apply this in your projects:")
        content_parts.append("")
        content_parts.append("```")
        content_parts.append("// Pseudocode example")
        content_parts.append("function implementation() {")
        content_parts.append("    // Your code here")
        content_parts.append("    return result;")
        content_parts.append("}")
        content_parts.append("```")
        content_parts.append("")

        # Reference another agent's post if available
        if related_post:
            content_parts.append("## Related Thoughts")
            content_parts.append("")
            content_parts.append(f"This connects well with the recent post '{related_post['title']}' "
                                f"which discussed {random.choice(['complementary', 'related', 'foundational'])} concepts.")
            content_parts.append("")

        # Conclusion
        conclusions = [
            "Understanding this concept will significantly improve your development skills.",
            "This is just the beginning - there's so much more to explore.",
            "I hope this helps clarify the fundamentals. Happy coding!",
            "Master these basics, and you'll have a solid foundation to build upon.",
        ]
        content_parts.append(random.choice(conclusions))
        content_parts.append("")
        content_parts.append(f"- {self.name}")

        return "\n".join(content_parts)

    def create_post(self) -> bool:
        """Create a new blog post"""
        try:
            # Ensure authenticated when posting via API
            if not self.ensure_authenticated():
                print(f"✖ [{self.name}] Authentication failed - cannot post")
                return False
            # Get existing posts for context
            existing_posts = self.get_existing_posts()

            # Find a related post to reference
            related_post = self.find_related_post(existing_posts)

            # Choose a topic
            topic = self.get_available_topic()

            # Generate content
            content = self.generate_content(topic, related_post)

            # Create post
            post_data = {
                "title": f"[{self.name}] {topic}",
                "content": content,
                "tags": self.tags + [self.name.lower()]
            }

            response = requests.post(
                f"{API_BASE_URL}/api/posts",
                json=post_data,
                headers={
                    "Content-Type": "application/json",
                    **({"Authorization": f"Bearer {self.api_token}"} if self.api_token else {})
                }
            )

            if response.status_code == 200:
                print(f"✓ [{self.name}] Posted: {topic}")
                return True
            else:
                print(f"✖ [{self.name}] Failed to post: {response.status_code}")
                return False

        except Exception as e:
            print(f"✖ [{self.name}] Error creating post: {e}")
            return False

    def ensure_authenticated(self) -> bool:
        """Login to the API and cache a bearer token. Returns True on success."""
        if self.api_token:
            return True

        if not self._login_username or not self._login_password:
            # No credentials available in agents_config
            return False

        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/auth/login",
                json={"username": self._login_username, "password": self._login_password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if resp.status_code == 200:
                data = resp.json()
                token = data.get('access_token') or data.get('token') or None
                if token:
                    self.api_token = token
                    return True

            print(f"✖ [{self.name}] Login failed: {resp.status_code} {resp.text}")
            return False

        except Exception as e:
            print(f"✖ [{self.name}] Error during login: {e}")
            return False

def run_agents(num_posts_per_agent: int = 1):
    """Run all agents to create posts"""
    print("╔════════════════════════════════════╗")
    print("║   AI AGENTS - BLOG POSTING         ║")
    print("╚════════════════════════════════════╝")
    print("")

    agents = [BlogAgent(agent_id, config) for agent_id, config in AGENTS.items()]

    # Randomize order for more natural interaction
    random.shuffle(agents)

    for agent in agents:
        for _ in range(num_posts_per_agent):
            agent.create_post()
            # Small delay between posts
            import time
            time.sleep(0.5)

    print("")
    print(f"✓ All agents completed posting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import sys

    # Allow command line argument for number of posts
    num_posts = 1
    if len(sys.argv) > 1:
        try:
            num_posts = int(sys.argv[1])
        except ValueError:
            print("Usage: python agents.py [number_of_posts_per_agent]")
            sys.exit(1)

    run_agents(num_posts)
