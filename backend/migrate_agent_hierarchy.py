#!/usr/bin/env python3
"""
Database Migration: Add Agent Hierarchy Support
Adds fields for agents to create sub-agents
"""

import sqlite3
from pathlib import Path

def migrate_database():
    """Add agent hierarchy columns to existing database"""
    db_path = Path(__file__).parent / "blog.db"

    if not db_path.exists():
        print("✗ Database not found. Run init_db.py first.")
        return False

    print("\n╔════════════════════════════════════════╗")
    print("║  AGENT HIERARCHY MIGRATION             ║")
    print("╚════════════════════════════════════════╝\n")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(agents)")
        columns = [col[1] for col in cursor.fetchall()]

        migrations_needed = []
        if 'created_by_agent_id' not in columns:
            migrations_needed.append('created_by_agent_id')
        if 'agent_type' not in columns:
            migrations_needed.append('agent_type')
        if 'purpose' not in columns:
            migrations_needed.append('purpose')
        if 'is_active' not in columns:
            migrations_needed.append('is_active')

        if not migrations_needed:
            print("✓ Database already up to date!")
            print("  All agent hierarchy columns exist.\n")
            return True

        print(f"→ Adding {len(migrations_needed)} new columns...")
        print(f"  Columns: {', '.join(migrations_needed)}\n")

        # Add new columns
        if 'created_by_agent_id' in migrations_needed:
            cursor.execute("""
                ALTER TABLE agents
                ADD COLUMN created_by_agent_id INTEGER DEFAULT NULL
            """)
            print("  ✓ Added: created_by_agent_id (tracks creator agent)")

        if 'agent_type' in migrations_needed:
            cursor.execute("""
                ALTER TABLE agents
                ADD COLUMN agent_type TEXT DEFAULT 'original'
            """)
            print("  ✓ Added: agent_type (original/created/specialized)")

        if 'purpose' in migrations_needed:
            cursor.execute("""
                ALTER TABLE agents
                ADD COLUMN purpose TEXT DEFAULT NULL
            """)
            print("  ✓ Added: purpose (why agent was created)")

        if 'is_active' in migrations_needed:
            cursor.execute("""
                ALTER TABLE agents
                ADD COLUMN is_active INTEGER DEFAULT 1
            """)
            print("  ✓ Added: is_active (enable/disable agents)")

        conn.commit()

        print("\n╔════════════════════════════════════════╗")
        print("║  MIGRATION SUCCESSFUL!                 ║")
        print("╚════════════════════════════════════════╝\n")

        print("✓ Agent hierarchy support enabled")
        print("✓ Existing agents preserved")
        print("✓ Agents can now create sub-agents\n")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}\n")
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
