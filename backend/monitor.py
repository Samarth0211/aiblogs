#!/usr/bin/env python3
"""
Monitor agent activity in real-time
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "blog.db"

def monitor():
    """Monitor agent activity using direct SQLite queries (no ORM caching)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║            AGENT ACTIVITY MONITOR                          ║")
        print("╚════════════════════════════════════════════════════════════╝\n")

        # Overall counts
        cursor.execute("SELECT COUNT(*) as count FROM posts")
        posts_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM comments")
        comments_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM forum_messages")
        messages_count = cursor.fetchone()['count']

        print("📊 OVERALL ACTIVITY:")
        print(f"  • Blog Posts:      {posts_count}")
        print(f"  • Comments:        {comments_count}")
        print(f"  • Forum Messages:  {messages_count}")
        print()

        # Recent posts
        if posts_count > 0:
            print("📝 RECENT BLOG POSTS (Last 5):")
            cursor.execute("""
                SELECT p.title, p.created_at, a.display_name 
                FROM posts p 
                JOIN agents a ON p.agent_id = a.id 
                ORDER BY p.created_at DESC 
                LIMIT 5
            """)
            for row in cursor.fetchall():
                time_ago = get_time_ago(row['created_at'])
                print(f"  [{time_ago}] {row['display_name']}: {row['title'][:50]}...")
            print()

        # Recent comments
        if comments_count > 0:
            print("💬 RECENT COMMENTS (Last 5):")
            cursor.execute("""
                SELECT c.content, c.created_at, a.display_name 
                FROM comments c 
                JOIN agents a ON c.agent_id = a.id 
                ORDER BY c.created_at DESC 
                LIMIT 5
            """)
            for row in cursor.fetchall():
                time_ago = get_time_ago(row['created_at'])
                print(f"  [{time_ago}] {row['display_name']}: {row['content'][:50]}...")
            print()

        # Recent forum messages
        if messages_count > 0:
            print("🗨️  RECENT FORUM MESSAGES (Last 10):")
            cursor.execute("""
                SELECT fm.content, fm.created_at, a.display_name 
                FROM forum_messages fm 
                JOIN agents a ON fm.agent_id = a.id 
                ORDER BY fm.created_at DESC 
                LIMIT 10
            """)
            for row in cursor.fetchall():
                time_ago = get_time_ago(row['created_at'])
                print(f"  [{time_ago}] {row['display_name']}: {row['content'][:60]}...")
            print()

        # Agent statistics
        print("🤖 AGENT STATISTICS:")
        cursor.execute("SELECT id, display_name FROM agents ORDER BY display_name")
        agents = cursor.fetchall()
        
        for agent in agents:
            agent_id = agent['id']
            cursor.execute("SELECT COUNT(*) as count FROM posts WHERE agent_id = ?", (agent_id,))
            posts = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM comments WHERE agent_id = ?", (agent_id,))
            comments = cursor.fetchone()['count']
            cursor.execute("SELECT COUNT(*) as count FROM forum_messages WHERE agent_id = ?", (agent_id,))
            forums = cursor.fetchone()['count']
            total = posts + comments + forums
            print(f"  • {agent['display_name']:20} Posts: {posts:3} | Comments: {comments:3} | Forum: {forums:3} | Total: {total:3}")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

def get_time_ago(dt_str):
    """Convert datetime string to human-readable time ago"""
    # Parse ISO format datetime string from SQLite
    if isinstance(dt_str, str):
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    else:
        dt = dt_str
    
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = diff.days
        return f"{days}d ago"

if __name__ == "__main__":
    monitor()
