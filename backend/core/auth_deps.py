"""
Shared authentication dependencies for FastAPI routers.

Provides:
  - get_current_user : JWT Bearer token → User ORM object
  - require_api_key  : X-API-Key header  → User ORM object (for agents)
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.models import User

_bearer_scheme = HTTPBearer(auto_error=False)


# --------------------------------------------------------------------------
# JWT-based auth (for dashboard / human users)
# --------------------------------------------------------------------------

async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT token from the ``Authorization: Bearer <token>`` header
    and return the corresponding User row.

    Raises 401 if the token is missing, expired, or belongs to no user.
    """
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            creds.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


# --------------------------------------------------------------------------
# API-key auth (for agents / sensors)
# --------------------------------------------------------------------------

async def require_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the ``X-API-Key`` header sent by the lightweight agent
    and return the owning User.

    Raises 401 if the key is missing or unknown.
    """
    result = await db.execute(select(User).where(User.api_key == x_api_key))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    return user
