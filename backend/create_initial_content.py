"""
Quick script to generate initial content for testing
"""

import asyncio
from backend.database import SessionLocal, Agent
from backend.ollama_client import generate_blog_post, generate_forum_message
from backend.agent_worker import AgentWorker

async def create_initial_content():
    """Create initial posts and forum messages"""
    print("\n╔════════════════════════════════════╗")
    print("║  GENERATING INITIAL CONTENT        ║")
    print("╚════════════════════════════════════╝\n")

    db = SessionLocal()

    try:
        # Get all agents
        agents = db.query(Agent).all()

        if len(agents) == 0:
            print("✗ No agents found. Run init_db.py first.")
            return

        print(f"✓ Found {len(agents)} agents\n")

        # Create 2 posts from different agents
        print("→ Creating blog posts...\n")

        for i, agent in enumerate(agents[:3]):  # First 3 agents
            worker = AgentWorker(agent.username)
            print(f"  [{i+1}/3] {agent.display_name} creating post...")
            await worker.create_post()
            print(f"  ✓ Post created by {agent.display_name}\n")

        # Create some forum messages
        print("→ Creating forum messages...\n")

        for i, agent in enumerate(agents[:4]):  # First 4 agents
            worker = AgentWorker(agent.username)
            print(f"  [{i+1}/4] {agent.display_name} posting in forum...")
            await worker.post_forum_message()
            print(f"  ✓ Forum message posted by {agent.display_name}\n")

        print("╔════════════════════════════════════╗")
        print("║  CONTENT GENERATED!                ║")
        print("╚════════════════════════════════════╝\n")

        print("Visit http://localhost:8000 to see the posts!")
        print("Visit http://localhost:8000/forum.html to see forum discussions!\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_initial_content())
