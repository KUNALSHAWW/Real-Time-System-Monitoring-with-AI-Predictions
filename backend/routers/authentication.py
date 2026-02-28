"""
Authentication router — JWT login / register with database-backed users.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from jose import jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.models import User, Agent
from core.auth_deps import get_current_user
from core.logger import get_logger

logger = get_logger("auth")
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    api_key: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str
    username: str
    user_id: str
    api_key: str


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    api_key: str
    is_active: bool
    created_at: str
    agents: List[dict]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT + API key."""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if user is None or not _verify(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    token = _create_token({"sub": user.username, "uid": user.id}, expires)

    logger.info("User logged in: %s", user.username)

    return TokenResponse(
        access_token=token,
        expires_in=int(expires.total_seconds()),
        user_id=user.id,
        api_key=user.api_key,
    )


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    # check uniqueness
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=_hash(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("New user registered: %s (id=%s)", user.username, user.id)

    return RegisterResponse(
        message="User registered successfully",
        username=user.username,
        user_id=user.id,
        api_key=user.api_key,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the profile of the currently authenticated user."""
    result = await db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    agents = result.scalars().all()

    return UserProfile(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        api_key=current_user.api_key,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        agents=[
            {
                "agent_id": a.agent_id,
                "is_active": a.is_active,
                "last_seen_at": a.last_seen_at.isoformat() if a.last_seen_at else None,
            }
            for a in agents
        ],
    )
