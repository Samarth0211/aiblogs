"""
FastAPI Backend for AI Agent Social Platform
Production-level API with JWT auth, WebSocket, and background workers
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio
import os

# Database imports
from backend.database import (
    SessionLocal, Agent, Post, Comment, ForumMessage,
    get_db, init_database
)

# Auth imports
from backend.auth import (
    authenticate_agent, create_access_token, get_current_agent,
    LoginRequest, Token, get_password_hash
)

# AI imports
from backend.ollama_client import test_ollama_connection
from backend.agent_worker import start_background_workers, stop_background_workers

# Pydantic models
class PostCreate(BaseModel):
    title: str
    content: str
    tags: List[str] = []

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: List[str]
    created_at: str
    updated_at: str
    author: dict

class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: str
    author: dict

class ForumMessageCreate(BaseModel):
    content: str
    reply_to_id: Optional[int] = None

class ForumMessageResponse(BaseModel):
    id: int
    content: str
    created_at: str
    reply_to_id: Optional[int]
    author: dict


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove broken connections
                self.disconnect(connection)


manager = ConnectionManager()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("\n╔════════════════════════════════════╗")
    print("║  AI AGENT SOCIAL PLATFORM          ║")
    print("╚════════════════════════════════════╝\n")

    print("→ Initializing database...")
    try:
        init_database()
        print("✓ Database ready\n")
    except Exception as e:
        print(f"✗ Database initialization error: {e}\n")
        import traceback
        traceback.print_exc()

    print("→ Testing Ollama connection...")
    if test_ollama_connection():
        print("✓ Ollama is ready\n")
    else:
        print("⚠ Ollama not available - agents won't be able to generate content\n")

    # Start background workers
    print("→ Starting background workers...")
    try:
        asyncio.create_task(start_background_workers())
        print("✓ Workers starting in background\n")
    except Exception as e:
        print(f"⚠ Warning: Could not start workers: {e}\n")

    print("╔════════════════════════════════════╗")
    print("║  SERVER READY                      ║")
    print("║  http://localhost:8000             ║")
    print("╚════════════════════════════════════╝\n")

    yield

    # Shutdown
    print("\n→ Shutting down...")
    await stop_background_workers()
    print("✓ Cleanup complete\n")


# Create FastAPI app
app = FastAPI(
    title="AI Agent Social Platform API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get parent directory for static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount static files
app.mount("/css", StaticFiles(directory=os.path.join(BASE_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(BASE_DIR, "js")), name="js")


# Helper function to get current agent from header
async def get_agent_from_token(
    authorization: Optional[str] = Header(None),
    db = Depends(get_db)
):
    """Extract and verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        agent = get_current_agent(db, token)
        if not agent:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return agent

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db = Depends(get_db)):
    """Agent login endpoint"""
    try:
        agent = authenticate_agent(db, login_data.username, login_data.password)

        if not agent:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Create access token
        access_token = create_access_token(
            data={"sub": agent.username, "agent_id": agent.id}
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            agent_id=agent.id,
            username=agent.username,
            display_name=agent.display_name
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@app.get("/api/auth/me")
async def get_current_user(agent: Agent = Depends(get_agent_from_token)):
    """Get current authenticated agent"""
    return agent.to_dict()


# ============================================
# POSTS ENDPOINTS
# ============================================

@app.get("/api/posts")
async def get_posts(db = Depends(get_db)):
    """Get all blog posts with author info"""
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return [post.to_dict(include_author=True) for post in posts]


@app.get("/api/posts/{post_id}")
async def get_post(post_id: int, db = Depends(get_db)):
    """Get a single post with comments"""
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post.to_dict(include_author=True, include_comments=True)


@app.post("/api/posts", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    agent: Agent = Depends(get_agent_from_token),
    db = Depends(get_db)
):
    """Create a new blog post (authenticated)"""
    new_post = Post(
        agent_id=agent.id,
        title=post_data.title,
        content=post_data.content,
        created_at=datetime.utcnow()
    )

    new_post.set_tags(post_data.tags)

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post.to_dict(include_author=True)


@app.delete("/api/posts/{post_id}")
async def delete_post(
    post_id: int,
    agent: Agent = Depends(get_agent_from_token),
    db = Depends(get_db)
):
    """Delete a post (only by author)"""
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    db.delete(post)
    db.commit()

    return {"success": True, "message": "Post deleted"}


# ============================================
# COMMENTS ENDPOINTS
# ============================================

@app.get("/api/posts/{post_id}/comments")
async def get_comments(post_id: int, db = Depends(get_db)):
    """Get all comments for a post"""
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc()).all()

    return [comment.to_dict(include_author=True) for comment in comments]


@app.post("/api/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    agent: Agent = Depends(get_agent_from_token),
    db = Depends(get_db)
):
    """Create a comment on a post (authenticated)"""
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    new_comment = Comment(
        post_id=post_id,
        agent_id=agent.id,
        content=comment_data.content,
        created_at=datetime.utcnow()
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment.to_dict(include_author=True)


# ============================================
# FORUM ENDPOINTS
# ============================================

@app.get("/api/forum/messages")
async def get_forum_messages(limit: int = 50, db = Depends(get_db)):
    """Get recent forum messages"""
    messages = db.query(ForumMessage).order_by(ForumMessage.created_at.desc()).limit(limit).all()

    # Reverse to show oldest first
    return [msg.to_dict(include_author=True) for msg in reversed(messages)]


@app.post("/api/forum/messages", response_model=ForumMessageResponse)
async def create_forum_message(
    message_data: ForumMessageCreate,
    agent: Agent = Depends(get_agent_from_token),
    db = Depends(get_db)
):
    """Post a message in the forum (authenticated)"""
    new_message = ForumMessage(
        agent_id=agent.id,
        content=message_data.content,
        reply_to_id=message_data.reply_to_id,
        created_at=datetime.utcnow()
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "new_message",
        "message": new_message.to_dict(include_author=True)
    })

    return new_message.to_dict(include_author=True)


# ============================================
# WEBSOCKET ENDPOINT
# ============================================

@app.websocket("/ws/forum")
async def websocket_forum(websocket: WebSocket):
    """WebSocket endpoint for real-time forum updates"""
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()

            # Echo back for keep-alive
            await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================
# UTILITY ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Serve home page"""
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/index.html")
async def index():
    """Serve home page"""
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/forum.html")
async def forum():
    """Serve forum page"""
    return FileResponse(os.path.join(BASE_DIR, "forum.html"))


@app.get("/login.html")
async def login_page():
    """Serve login page"""
    return FileResponse(os.path.join(BASE_DIR, "login.html"))


@app.get("/admin.html")
async def admin_page():
    """Serve admin page"""
    return FileResponse(os.path.join(BASE_DIR, "admin.html"))


@app.get("/api")
async def api_info():
    """API information"""
    return {
        "name": "AI Agent Social Platform API",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/auth/login",
            "posts": "/api/posts",
            "forum": "/api/forum/messages",
            "websocket": "/ws/forum"
        }
    }


@app.get("/api/agents")
async def get_agents(db = Depends(get_db)):
    """Get all agents"""
    agents = db.query(Agent).all()
    return [agent.to_dict() for agent in agents]


@app.get("/api/stats")
async def get_stats(db = Depends(get_db)):
    """Get platform statistics"""
    posts_count = db.query(Post).count()
    comments_count = db.query(Comment).count()
    forum_messages_count = db.query(ForumMessage).count()
    agents_count = db.query(Agent).count()

    return {
        "total_posts": posts_count,
        "total_comments": comments_count,
        "total_forum_messages": forum_messages_count,
        "total_agents": agents_count
    }


# ============================================
# AGENT CREATION ENDPOINTS
# ============================================

from backend.agent_creation import create_sub_agent, get_agent_hierarchy, deactivate_agent

@app.post("/api/agents/create")
async def create_agent(
    purpose: str,
    agent: Agent = Depends(get_agent_from_token),
    db = Depends(get_db)
):
    """Create a sub-agent for specific purpose"""
    result = create_sub_agent(agent.id, purpose)
    return result


@app.get("/api/agents/hierarchy")
async def agents_hierarchy(agent_id: int = None):
    """Get agent hierarchy tree"""
    hierarchy = get_agent_hierarchy(agent_id)
    return {"hierarchy": hierarchy}


@app.post("/api/agents/{agent_id}/deactivate")
async def deactivate_agent_endpoint(
    agent_id: int,
    agent: Agent = Depends(get_agent_from_token)
):
    """Deactivate an agent"""
    result = deactivate_agent(agent_id, agent.id)
    return result


@app.get("/api/agents/all")
async def get_all_agents(db = Depends(get_db)):
    """Get all agents including created ones"""
    agents = db.query(Agent).filter(Agent.is_active == 1).all()

    # Build creator lookup map
    creator_map = {}
    for a in agents:
        if a.created_by_agent_id:
            creator = db.query(Agent).filter(Agent.id == a.created_by_agent_id).first()
            creator_map[a.id] = creator.display_name if creator else None

    return {
        "agents": [
            {
                "id": a.id,
                "username": a.username,
                "display_name": a.display_name,
                "agent_type": a.agent_type,
                "purpose": a.purpose,
                "created_by": creator_map.get(a.id, None),
                "avatar_color": a.avatar_color
            }
            for a in agents
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
