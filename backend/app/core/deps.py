"""
FastAPI dependencies for authentication, authorization, and common utilities.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.redis import get_redis, is_token_blacklisted
from app.core.security import decode_token
from app.models.models import User, UserRole
import redis.asyncio as aioredis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check blacklist
    if await is_token_blacklisted(redis, token):
        raise credentials_exception

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        org_id: str = payload.get("org_id")
        if not user_id or not org_id:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id, User.is_deleted.is_(False)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_roles(*roles: UserRole):
    """Dependency factory to restrict access to specific roles."""
    async def _require_roles(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {[r.value for r in roles]}",
            )
        return current_user
    return _require_roles


def require_org_admin():
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN)


def require_manager_or_above():
    return require_roles(UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SALES_MANAGER)
