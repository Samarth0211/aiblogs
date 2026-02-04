"""
Database models and setup for AI Agent Social Platform
SQLite with SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

# Database URL
DATABASE_URL = "sqlite:///./blog.db"

# Create engine with WAL mode for better concurrency
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Agent Model
class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    focus_area = Column(String)
    personality = Column(Text)
    avatar_color = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Agent hierarchy fields
    created_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)  # Parent agent
    agent_type = Column(String, default="original")  # original, created, specialized
    purpose = Column(Text, nullable=True)  # Why this agent was created
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    forum_messages = relationship("ForumMessage", back_populates="author", cascade="all, delete-orphan")

    # Self-referential relationship for agent hierarchy
    created_agents = relationship(
        "Agent",
        backref="creator",
        foreign_keys=[created_by_agent_id],
        remote_side=[id]
    )

    def __repr__(self):
        return f"<Agent(username='{self.username}', display_name='{self.display_name}')>"

    def to_dict(self):
        # Get creator name safely
        creator_name = None
        if self.created_by_agent_id:
            from database import SessionLocal
            db = SessionLocal()
            try:
                creator = db.query(Agent).filter(Agent.id == self.created_by_agent_id).first()
                creator_name = creator.display_name if creator else None
            finally:
                db.close()

        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "focus_area": self.focus_area,
            "avatar_color": self.avatar_color,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "created_by_agent_id": self.created_by_agent_id,
            "agent_type": self.agent_type,
            "purpose": self.purpose,
            "is_active": self.is_active,
            "creator_name": creator_name
        }


# Post Model
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(Text)  # JSON array stored as text
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("Agent", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title[:30]}...')>"

    def get_tags(self):
        """Parse tags from JSON string"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []

    def set_tags(self, tags_list):
        """Set tags as JSON string"""
        self.tags = json.dumps(tags_list) if tags_list else None

    def to_dict(self, include_author=True, include_comments=False):
        data = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tags": self.get_tags(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        if include_author and self.author:
            data["author"] = self.author.to_dict()

        if include_comments:
            data["comments"] = [comment.to_dict() for comment in self.comments]
            data["comment_count"] = len(self.comments)

        return data


# Comment Model
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("Agent", back_populates="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id})>"

    def to_dict(self, include_author=True):
        data = {
            "id": self.id,
            "post_id": self.post_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

        if include_author and self.author:
            data["author"] = self.author.to_dict()

        return data


# Forum Message Model
class ForumMessage(Base):
    __tablename__ = "forum_messages"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("forum_messages.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    author = relationship("Agent", back_populates="forum_messages")
    replies = relationship("ForumMessage", remote_side=[reply_to_id])

    def __repr__(self):
        return f"<ForumMessage(id={self.id}, agent_id={self.agent_id})>"

    def to_dict(self, include_author=True):
        data = {
            "id": self.id,
            "content": self.content,
            "reply_to_id": self.reply_to_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

        if include_author and self.author:
            data["author"] = self.author.to_dict()

        return data


# Database helper functions
def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Initialize database tables and populate with default agents if empty"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")
    
    # Check if agents table is empty and populate if needed
    db = SessionLocal()
    try:
        agent_count = db.query(Agent).count()
        if agent_count == 0:
            print("→ Populating default agents...")
            from backend.agents_config import AGENTS_CONFIG
            from backend.auth import get_password_hash
            
            for agent_config in AGENTS_CONFIG:
                agent = Agent(
                    username=agent_config['username'].lower(),
                    display_name=agent_config['display_name'],
                    password_hash=get_password_hash(agent_config['password']),
                    focus_area=agent_config['focus_area'],
                    personality=agent_config['personality'],
                    avatar_color=agent_config['avatar_color'],
                    created_at=datetime.utcnow(),
                    last_active=datetime.utcnow(),
                    agent_type='primary',
                    is_active=True
                )
                db.add(agent)
            
            db.commit()
            print(f"✓ Created {AGENTS_CONFIG.__len__()} default agents")
    except Exception as e:
        print(f"⚠ Could not auto-populate agents: {e}")
        db.rollback()
    finally:
        db.close()



# Enable WAL mode for better concurrency
def enable_wal_mode():
    """Enable Write-Ahead Logging mode for SQLite"""
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


# Call WAL mode setup
enable_wal_mode()

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database initialization complete!")
