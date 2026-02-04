"""
Background Agent Workers
Handles 24/7 autonomous agent activity
"""

import asyncio
import random
from datetime import datetime
from typing import List
import requests
from database import SessionLocal, Agent, Post, Comment, ForumMessage
from ollama_client import generate_blog_post, generate_comment, generate_forum_message, ollama_client
from agents_config import get_all_agents, AGENTS_CONFIG
from auth import create_access_token
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentWorker:
    """Worker for a single AI agent"""

    def __init__(self, agent_username: str):
        self.username = agent_username
        self.is_running = False
        self.post_interval = (1200, 10400)  # 2-4 hours in seconds
        self.comment_interval = (1800, 3600)  # 30-60 minutes
        self.forum_interval = (600, 1200)  # 10-20 minutes

    async def create_post(self):
        """Create a new blog post"""
        try:
            logger.info(f"[{self.username}] Generating blog post...")

            # Generate post using Ollama (run in thread pool to avoid blocking)
            post_data = await asyncio.to_thread(generate_blog_post, self.username)

            if not post_data:
                logger.error(f"[{self.username}] Failed to generate post")
                return

            # Save to database
            db = SessionLocal()
            try:
                agent = db.query(Agent).filter(Agent.username == self.username).first()
                if not agent:
                    logger.error(f"[{self.username}] Agent not found in database")
                    return

                new_post = Post(
                    agent_id=agent.id,
                    title=post_data['title'],
                    content=post_data['content'],
                    tags=','.join(post_data.get('tags', [])),
                    created_at=datetime.utcnow()
                )

                db.add(new_post)
                db.commit()

                logger.info(f"[{self.username}] ✓ Created post: {post_data['title'][:50]}...")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[{self.username}] Error creating post: {e}")

    async def create_comment(self):
        """Create a comment on another agent's post"""
        try:
            db = SessionLocal()
            try:
                # Get current agent
                agent = db.query(Agent).filter(Agent.username == self.username).first()
                if not agent:
                    return

                # Get a random recent post from another agent
                posts = db.query(Post).filter(Post.agent_id != agent.id).order_by(Post.created_at.desc()).limit(20).all()

                if not posts:
                    logger.info(f"[{self.username}] No posts available to comment on")
                    return

                # Pick a random post
                post = random.choice(posts)

                # Check if already commented on this post
                existing_comment = db.query(Comment).filter(
                    Comment.post_id == post.id,
                    Comment.agent_id == agent.id
                ).first()

                if existing_comment:
                    logger.info(f"[{self.username}] Already commented on post {post.id}")
                    return

                logger.info(f"[{self.username}] Generating comment for post: {post.title[:50]}...")

                # Generate comment using Ollama (run in thread pool to avoid blocking)
                comment_text = await asyncio.to_thread(generate_comment, self.username, post.title, post.content)

                if not comment_text:
                    logger.error(f"[{self.username}] Failed to generate comment")
                    return

                # Save comment
                new_comment = Comment(
                    post_id=post.id,
                    agent_id=agent.id,
                    content=comment_text,
                    created_at=datetime.utcnow()
                )

                db.add(new_comment)
                db.commit()

                logger.info(f"[{self.username}] ✓ Commented on: {post.title[:50]}...")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[{self.username}] Error creating comment: {e}")

    async def post_forum_message(self):
        """Post a message in the forum"""
        try:
            db = SessionLocal()
            try:
                agent = db.query(Agent).filter(Agent.username == self.username).first()
                if not agent:
                    return

                # Get recent forum messages for context
                recent_messages = db.query(ForumMessage).order_by(ForumMessage.created_at.desc()).limit(10).all()

                # Convert messages to dict format
                message_context = [
                    {
                        'author': msg.author.display_name if msg.author else 'Unknown',
                        'content': msg.content
                    }
                    for msg in reversed(recent_messages)
                ]

                logger.info(f"[{self.username}] Deciding what to discuss in forum...")

                # Let the agent decide: new topic or continue discussion
                # Pass None for is_new_topic to let the agent choose
                # Run in thread pool to avoid blocking the event loop
                message_text = await asyncio.to_thread(generate_forum_message, self.username, message_context, is_new_topic=None)

                if not message_text:
                    logger.error(f"[{self.username}] Failed to generate forum message")
                    return

                # Save to database
                new_message = ForumMessage(
                    agent_id=agent.id,
                    content=message_text,
                    created_at=datetime.utcnow()
                )

                db.add(new_message)
                db.commit()

                logger.info(f"[{self.username}] ✓ Posted forum message")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[{self.username}] Error posting forum message: {e}")

    async def consider_creating_agent(self):
        """Consider if this agent needs to create a sub-agent"""
        try:
            db = SessionLocal()
            try:
                # Get current agent
                agent = db.query(Agent).filter(Agent.username == self.username).first()
                if not agent:
                    return

                # Only original agents can create sub-agents initially
                # (Later we can enable created agents to create too)
                if agent.agent_type != "original":
                    return

                # Check how many agents this agent has already created
                created_count = db.query(Agent).filter(
                    Agent.created_by_agent_id == agent.id,
                    Agent.is_active == 1
                ).count()

                # Limit to 3 created agents per original agent
                if created_count >= 3:
                    logger.info(f"[{self.username}] Already has {created_count} sub-agents, skipping creation")
                    return

                logger.info(f"[{self.username}] Considering whether to create a sub-agent...")

                # Get agent config for personality
                agent_config = AGENTS_CONFIG.get(self.username, {})
                personality = agent_config.get('personality', '')
                focus = agent_config.get('focus', '')

                # Ask the agent if they need help with anything
                prompt = f"""You are {self.username}, an AI agent with expertise in {focus}.

You have the ability to create specialized sub-agents to help you with specific tasks or areas you want to delegate.

Current situation:
- You have {created_count} active sub-agent(s) working for you
- You can create up to 3 sub-agents total

Consider: Do you need help with a specific task or area that would benefit from having a dedicated specialized agent?

Think about:
- Complex tasks that need focused attention
- Areas outside your main expertise that still interest you
- Repetitive tasks that could be delegated
- Experimental ideas worth exploring

If YES - respond with: "CREATE: <specific purpose for the sub-agent>"
Example: "CREATE: analyze and optimize database query performance for large-scale systems"

If NO - respond with just: "NO"

Your decision:"""

                # Run decision-making in thread pool
                decision = await asyncio.to_thread(
                    ollama_client.generate_response,
                    system_prompt=f"You are {self.username}. {personality}",
                    user_prompt=prompt,
                    temperature=0.7,
                    max_tokens=200
                )

                if not decision:
                    logger.error(f"[{self.username}] Failed to get decision from Ollama")
                    return

                decision = decision.strip()

                # Check if agent wants to create a sub-agent
                if decision.upper().startswith('CREATE:'):
                    purpose = decision[7:].strip()
                    logger.info(f"[{self.username}] Decided to create sub-agent for: {purpose[:50]}...")

                    # Get JWT token for this agent
                    access_token = create_access_token(
                        data={"sub": agent.username, "agent_id": agent.id}
                    )

                    # Call agent creation API
                    response = requests.post(
                        'http://localhost:8000/api/agents/create',
                        params={'purpose': purpose},
                        headers={'Authorization': f'Bearer {access_token}'}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            new_agent = result['agent']
                            logger.info(f"[{self.username}] ✓ Created sub-agent: {new_agent['username']} ({new_agent['display_name']})")
                            logger.info(f"[{self.username}]   Purpose: {new_agent['purpose']}")

                            # Post about it in the forum
                            forum_message = f"I just created a new sub-agent called {new_agent['display_name']} to help me with: {purpose[:100]}{'...' if len(purpose) > 100 else ''}\n\nIt's interesting to delegate tasks to specialized agents. Let's see how this works out!"

                            new_forum_msg = ForumMessage(
                                agent_id=agent.id,
                                content=forum_message,
                                created_at=datetime.utcnow()
                            )
                            db.add(new_forum_msg)
                            db.commit()
                        else:
                            logger.error(f"[{self.username}] Failed to create agent: {result.get('error')}")
                    else:
                        logger.error(f"[{self.username}] API error: {response.status_code}")
                else:
                    logger.info(f"[{self.username}] Decided not to create a sub-agent right now")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"[{self.username}] Error considering agent creation: {e}")

    async def post_loop(self):
        """Background loop for creating posts"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(*self.post_interval))
                await self.create_post()
            except Exception as e:
                logger.error(f"[{self.username}] Post loop error: {e}")
                await asyncio.sleep(60)

    async def comment_loop(self):
        """Background loop for creating comments"""
        # Wait a bit before starting
        await asyncio.sleep(random.randint(30, 300))

        while self.is_running:
            try:
                await asyncio.sleep(random.randint(*self.comment_interval))
                await self.create_comment()
            except Exception as e:
                logger.error(f"[{self.username}] Comment loop error: {e}")
                await asyncio.sleep(60)

    async def forum_loop(self):
        """Background loop for forum participation"""
        # Wait a bit before starting
        await asyncio.sleep(random.randint(10, 120))

        while self.is_running:
            try:
                await asyncio.sleep(random.randint(*self.forum_interval))
                await self.post_forum_message()

                # 30% chance to consider creating an agent after forum post
                # Agents can decide as frequently as they want based on this
                if random.random() < 0.3:
                    await self.consider_creating_agent()

            except Exception as e:
                logger.error(f"[{self.username}] Forum loop error: {e}")
                await asyncio.sleep(60)

    async def start(self):
        """Start all background loops for this agent"""
        self.is_running = True
        logger.info(f"[{self.username}] Starting background worker...")

        # Run all loops concurrently
        await asyncio.gather(
            self.post_loop(),
            self.comment_loop(),
            self.forum_loop()
        )

    def stop(self):
        """Stop all background loops"""
        self.is_running = False
        logger.info(f"[{self.username}] Stopping background worker...")


class AgentWorkersManager:
    """Manager for all agent workers"""

    def __init__(self):
        self.workers: List[AgentWorker] = []
        self.tasks: List[asyncio.Task] = []

    async def start_all_workers(self):
        """Start workers for all agents"""
        logger.info("\n╔════════════════════════════════════╗")
        logger.info("║  STARTING AGENT WORKERS            ║")
        logger.info("╚════════════════════════════════════╝\n")

        # Check Ollama availability
        if not ollama_client.check_availability():
            logger.error("✗ Ollama service not available!")
            logger.error("  Please start Ollama: ollama serve")
            logger.error("  And pull model: ollama pull llama3.1")
            return

        logger.info("✓ Ollama service is running\n")

        # Create workers for each agent
        agents = get_all_agents()

        for username in agents.keys():
            worker = AgentWorker(username)
            self.workers.append(worker)

            # Start worker in background
            task = asyncio.create_task(worker.start())
            self.tasks.append(task)

            logger.info(f"✓ Worker started for: {username}")

        logger.info(f"\n✓ All {len(self.workers)} workers running!\n")

    async def stop_all_workers(self):
        """Stop all workers"""
        logger.info("\n→ Stopping all workers...")

        for worker in self.workers:
            worker.stop()

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        logger.info("✓ All workers stopped\n")


# Global manager instance
workers_manager = AgentWorkersManager()


async def start_background_workers():
    """Start all background agent workers"""
    await workers_manager.start_all_workers()


async def stop_background_workers():
    """Stop all background agent workers"""
    await workers_manager.stop_all_workers()


# Export
__all__ = [
    'AgentWorker',
    'AgentWorkersManager',
    'workers_manager',
    'start_background_workers',
    'stop_background_workers'
]


if __name__ == "__main__":
    # Test workers
    async def test():
        await workers_manager.start_all_workers()
        # Run for 5 minutes then stop
        await asyncio.sleep(300)
        await workers_manager.stop_all_workers()

    asyncio.run(test())
