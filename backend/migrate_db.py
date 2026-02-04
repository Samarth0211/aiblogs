#!/usr/bin/env python3
"""
Database migration script - adds missing columns to agents table
"""

import sqlite3
import os

DB_PATH = "blog.db"

def migrate():
    """Add missing columns to agents table"""
    
    if not os.path.exists(DB_PATH):
        print(f"✗ Database {DB_PATH} not found!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("→ Checking agents table schema...")
        
        # Get current columns
        cursor.execute("PRAGMA table_info(agents);")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"   Current columns: {columns}")
        
        # List of columns to add
        columns_to_add = [
            ("created_by_agent_id", "INTEGER"),
            ("agent_type", "TEXT DEFAULT 'original'"),
            ("purpose", "TEXT"),
            ("is_active", "INTEGER DEFAULT 1"),
        ]
        
        # Add missing columns
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                print(f"→ Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE agents ADD COLUMN {col_name} {col_type};")
                print(f"  ✓ Added {col_name}")
            else:
                print(f"  ✓ Column {col_name} already exists")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)
