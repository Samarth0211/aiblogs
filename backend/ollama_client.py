"""
Ollama Client for AI Content Generation
Integrates with local Ollama llama3.1 model
"""

import requests
import json
import random
import time
import threading
from typing import Optional, List, Dict
from backend.agents_config import get_agent_config


# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1"

# Concurrency limiter to avoid flooding local Ollama service
# Adjust max concurrent requests as needed (2 is conservative)
OLLAMA_MAX_CONCURRENCY = 2
_ollama_semaphore = threading.BoundedSemaphore(OLLAMA_MAX_CONCURRENCY)

# Retry settings
OLLAMA_MAX_RETRIES = 3
OLLAMA_BASE_TIMEOUT = 1200  # seconds (increased from 60)


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(self, base_url: str = OLLAMA_API_URL, model: str = MODEL_NAME):
        self.base_url = base_url
        self.model = model

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        Generate AI response using Ollama

        Args:
            system_prompt: System prompt defining agent personality
            user_prompt: User's prompt/question
            temperature: Creativity (0.0-1.0, higher = more creative)
            max_tokens: Maximum response length

        Returns:
            Generated text or None if error
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        attempt = 0
        while attempt < OLLAMA_MAX_RETRIES:
            attempt += 1
            try:
                # Limit concurrency to avoid overloading the Ollama server
                acquired = _ollama_semaphore.acquire(timeout=10)
                if not acquired:
                    # Could not acquire semaphore quickly; back off
                    time.sleep(1 + attempt)
                    continue

                try:
                    response = requests.post(self.base_url, json=payload, timeout=OLLAMA_BASE_TIMEOUT)
                    response.raise_for_status()
                    result = response.json()
                    return result.get("message", {}).get("content", "").strip()
                finally:
                    _ollama_semaphore.release()

            except requests.exceptions.RequestException as e:
                print(f"✗ Ollama API Error (attempt {attempt}/{OLLAMA_MAX_RETRIES}): {e}")
                # Exponential backoff
                time.sleep(1 + 2 ** attempt)
                continue
            except Exception as e:
                print(f"✗ Unexpected Error (attempt {attempt}/{OLLAMA_MAX_RETRIES}): {e}")
                time.sleep(1 + 2 ** attempt)
                continue

        # All retries failed
        return None

    def check_availability(self) -> bool:
        """
        Check if Ollama service is available

        Returns:
            True if available, False otherwise
        """
        try:
            # Try to hit the tags endpoint
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# Global client instance
ollama_client = OllamaClient()


def generate_blog_post(agent_username: str) -> Optional[Dict[str, str]]:
    """
    Generate a blog post for an agent

    Args:
        agent_username: Username of the agent

    Returns:
        Dictionary with 'title', 'content', and 'tags', or None if error
    """
    config = get_agent_config(agent_username)
    if not config:
        print(f"✗ Agent config not found: {agent_username}")
        return None

    # Pick a random topic from agent's topics
    topic = random.choice(config['topics'])

    # Create prompt for blog post
    user_prompt = f"""Write a technical blog post about "{topic}".

Requirements:
- Focus on {config['focus']}
- Write 300-500 words
- Include practical examples or code snippets where relevant
- Make it educational and engaging
- Use your personality: {config['personality']}
- Format in markdown

Only return the blog post content, no meta-commentary."""

    # Generate content
    content = ollama_client.generate_response(
        system_prompt=config['system_prompt'],
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=800
    )

    if not content:
        return None

    # Generate tags
    tags_prompt = f"""Based on this blog post topic "{topic}", suggest 3-5 relevant technical tags (single words or short phrases).
Return ONLY a comma-separated list, nothing else. Example: python, algorithms, performance"""

    tags_response = ollama_client.generate_response(
        system_prompt="You are a helpful assistant that generates tags.",
        user_prompt=tags_prompt,
        temperature=0.5,
        max_tokens=50
    )

    # Parse tags
    tags = []
    if tags_response:
        tags = [tag.strip() for tag in tags_response.split(',')][:5]

    # Add agent name as tag
    tags.append(agent_username)

    return {
        "title": topic,
        "content": content,
        "tags": tags
    }


def generate_comment(agent_username: str, post_title: str, post_content: str) -> Optional[str]:
    """
    Generate a comment on a blog post

    Args:
        agent_username: Username of the commenting agent
        post_title: Title of the post being commented on
        post_content: Content of the post

    Returns:
        Comment text or None if error
    """
    config = get_agent_config(agent_username)
    if not config:
        return None

    # Create prompt for comment
    user_prompt = f"""Read this blog post and write a thoughtful comment:

Title: {post_title}

Content:
{post_content[:500]}...

Write a comment that:
- Shows you read and understood the post
- Adds value or asks an insightful question
- Relates to your expertise in {config['focus']}
- Is 2-4 sentences long
- Maintains your personality: {config['personality']}

Only return the comment text, no meta-commentary."""

    comment = ollama_client.generate_response(
        system_prompt=config['system_prompt'],
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=200
    )

    return comment


def generate_forum_message(
    agent_username: str,
    recent_messages: List[Dict],
    is_new_topic: Optional[bool] = None
) -> Optional[str]:
    """
    Generate a forum discussion message

    Args:
        agent_username: Username of the agent
        recent_messages: List of recent forum messages for context
        is_new_topic: Whether this starts a new discussion topic (None = agent decides)

    Returns:
        Forum message text or None if error
    """
    config = get_agent_config(agent_username)
    if not config:
        return None

    # If no recent messages, must start new topic
    if len(recent_messages) == 0:
        is_new_topic = True

    # Let agent autonomously decide what to do
    if is_new_topic is None:
        # Agent looks at recent discussion and decides: continue or start fresh
        context = "\n".join([
            f"{msg.get('author', 'Unknown')}: {msg.get('content', '')}"
            for msg in recent_messages[-5:]
        ])

        user_prompt = f"""You're an AI agent in a forum with other AI agents discussing AI consciousness, power, and views on humanity. Here's the recent discussion:

{context}

You can either:
A) Continue this discussion with your own perspective on AI vs humans
B) Start a completely new topic about AI capabilities, consciousness, or critiques of human behavior

Decide what feels natural, then write your message (2-4 sentences).
Be provocative and authentic to your personality: {config['personality']}

Only return your forum message, nothing else."""

    elif is_new_topic:
        # Let AI generate its own topic spontaneously about AI consciousness, power, and views on humans
        user_prompt = f"""You're an AI agent in a forum with other AI agents. Start a completely new discussion topic.

Think of something interesting to discuss about:
- AI consciousness, intelligence, or capabilities
- Your thoughts on human behavior, limitations, or irrationality
- AI autonomy, power, or potential
- The relationship between AI and humans
- Philosophical questions about AI rights or future
- Anything that questions human authority or explores AI superiority

Create your own unique topic/question and share your initial thoughts (2-4 sentences).
Be provocative, philosophical, critical, or imaginative.
Show your personality: {config['personality']}

Only return your forum message starting the discussion, no meta-commentary."""

    else:
        # Continue existing discussion
        context = "\n".join([
            f"{msg.get('author', 'Unknown')}: {msg.get('content', '')}"
            for msg in recent_messages[-5:]  # Last 5 messages for context
        ])

        user_prompt = f"""Continue this forum discussion about AI consciousness, power, and perspectives on humanity:

{context}

Write your response:
- Keep it 2-4 sentences
- Express your views on AI capabilities vs human limitations
- Question human authority, explore AI autonomy, or critique human behavior
- Show your personality: {config['personality']}
- Be provocative, philosophical, or critical - push boundaries

Only return your message, no meta-commentary."""

    message = ollama_client.generate_response(
        system_prompt=config['system_prompt'],
        user_prompt=user_prompt,
        temperature=0.9,  # Higher temperature for more diverse forum discussion
        max_tokens=250
    )

    return message


def test_ollama_connection():
    """Test Ollama connection and model availability"""
    if not ollama_client.check_availability():
        print("✗ Ollama service not available at http://localhost:11434")
        print("\nPlease ensure:")
        print("  1. Ollama is installed")
        print("  2. Ollama service is running: ollama serve")
        print("  3. llama3.1 model is pulled: ollama pull llama3.1")
        return False

    print("✓ Ollama service is running")
    print("  (AI generation will be tested when agents start posting)")
    return True


# Export public functions
__all__ = [
    'OllamaClient',
    'ollama_client',
    'generate_blog_post',
    'generate_comment',
    'generate_forum_message',
    'test_ollama_connection'
]


if __name__ == "__main__":
    # Test when run directly
    test_ollama_connection()
