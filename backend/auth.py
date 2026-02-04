"""
Authentication module with JWT tokens
Handles agent login, token generation, and password verification
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    agent_id: int
    username: str
    display_name: str


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    agent_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary containing token payload (username, agent_id, etc.)
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData object if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        agent_id: int = payload.get("agent_id")

        if username is None or agent_id is None:
            return None

        return TokenData(username=username, agent_id=agent_id)
    except JWTError:
        return None


def authenticate_agent(db, username: str, password: str):
    """
    Authenticate an agent with username and password

    Args:
        db: Database session
        username: Agent username
        password: Plain text password

    Returns:
        Agent object if authentication successful, None otherwise
    """
    from backend.database import Agent

    agent = db.query(Agent).filter(Agent.username == username).first()

    if not agent:
        return None

    if not verify_password(password, agent.password_hash):
        return None

    # Update last active timestamp
    agent.last_active = datetime.utcnow()
    db.commit()

    return agent


def get_current_agent(db, token: str):
    """
    Get the current authenticated agent from a token

    Args:
        db: Database session
        token: JWT token string

    Returns:
        Agent object if token is valid, None otherwise
    """
    from database import Agent

    token_data = verify_token(token)

    if token_data is None:
        return None

    agent = db.query(Agent).filter(Agent.username == token_data.username).first()

    return agent


# Export all public functions
__all__ = [
    'Token',
    'TokenData',
    'LoginRequest',
    'verify_password',
    'get_password_hash',
    'create_access_token',
    'verify_token',
    'authenticate_agent',
    'get_current_agent'
]
