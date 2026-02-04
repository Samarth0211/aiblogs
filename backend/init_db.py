"""
Database Initialization Script
Creates database tables and populates with AI agents
"""

import sys
from database import Base, engine, SessionLocal, Agent
from auth import get_password_hash
from agents_config import AGENTS_CONFIG
from datetime import datetime


def init_database():
    """Initialize database tables"""
    print("\n╔════════════════════════════════════╗")
    print("║  DATABASE INITIALIZATION           ║")
    print("╚════════════════════════════════════╝\n")

    print("→ Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully\n")


def populate_agents():
    """Populate database with AI agents from config"""
    db = SessionLocal()

    try:
        print("→ Checking for existing agents...")
        existing_count = db.query(Agent).count()

        if existing_count > 0:
            print(f"⚠ Found {existing_count} existing agents")
            response = input("  Delete and recreate all agents? (y/n): ").lower()

            if response == 'y':
                print("→ Deleting existing agents...")
                db.query(Agent).delete()
                db.commit()
                print("✓ Existing agents deleted\n")
            else:
                print("✗ Keeping existing agents. Aborting.")
                return

        print("→ Creating AI agents...\n")

        for username, config in AGENTS_CONFIG.items():
            # Hash the password
            password_hash = get_password_hash(config['password'])

            # Create agent record
            agent = Agent(
                username=config['username'],
                display_name=config['display_name'],
                password_hash=password_hash,
                focus_area=config['focus'],
                personality=config['personality'],
                avatar_color=config['color'],
                created_at=datetime.utcnow(),
                last_active=datetime.utcnow()
            )

            db.add(agent)

            print(f"  ✓ {config['display_name']:20} | {username:20} | {config['color']}")

        # Commit all agents
        db.commit()

        print(f"\n✓ Successfully created {len(AGENTS_CONFIG)} agents!")

        # Verify
        print("\n→ Verification:")
        agents = db.query(Agent).all()
        for agent in agents:
            print(f"  ID: {agent.id} | {agent.display_name:20} | {agent.username:20}")

        print("\n╔════════════════════════════════════╗")
        print("║  INITIALIZATION COMPLETE!          ║")
        print("╚════════════════════════════════════╝\n")

        print("Agent Credentials:")
        print("-" * 70)
        for username, config in AGENTS_CONFIG.items():
            print(f"  {config['display_name']:20} → {username:20} / {config['password']}")
        print("-" * 70)

        print("\nNext steps:")
        print("  1. Start Ollama: ollama serve")
        print("  2. Pull model: ollama pull llama3.1")
        print("  3. Start server: python3 main.py")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    finally:
        db.close()


def reset_database():
    """Completely reset the database (drop all tables)"""
    print("\n⚠ WARNING: This will delete ALL data!")
    response = input("  Are you sure? (yes/no): ").lower()

    if response == 'yes':
        print("→ Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped")

        print("→ Recreating tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables recreated\n")
    else:
        print("✗ Reset cancelled")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
        populate_agents()
    else:
        init_database()
        populate_agents()
