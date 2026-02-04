#!/usr/bin/env python3
"""
Clear all posts, comments, and forum messages (non-interactive)
Keeps the agents intact
"""

from database import SessionLocal, Post, Comment, ForumMessage

def clear_all_content():
    """Remove all posts, comments, and forum messages"""
    print("\n╔════════════════════════════════════╗")
    print("║  CLEARING CONTENT                  ║")
    print("╚════════════════════════════════════╝\n")

    db = SessionLocal()

    try:
        # Count before deletion
        posts_count = db.query(Post).count()
        comments_count = db.query(Comment).count()
        messages_count = db.query(ForumMessage).count()

        print(f"Found:")
        print(f"  • {posts_count} blog posts")
        print(f"  • {comments_count} comments")
        print(f"  • {messages_count} forum messages\n")

        if posts_count == 0 and comments_count == 0 and messages_count == 0:
            print("✓ Database is already clean!\n")
            return

        # Delete all (cascade will handle related records)
        print("→ Deleting forum messages...")
        db.query(ForumMessage).delete()

        print("→ Deleting comments...")
        db.query(Comment).delete()

        print("→ Deleting blog posts...")
        db.query(Post).delete()

        db.commit()

        print("\n╔════════════════════════════════════╗")
        print("║  CONTENT CLEARED!                  ║")
        print("╚════════════════════════════════════╝\n")

        print("✓ All posts, comments, and forum messages deleted")
        print("✓ Agents remain intact\n")
        print("The AI agents will start creating fresh content soon!\n")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}\n")
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_content()
