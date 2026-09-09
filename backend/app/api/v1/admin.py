"""
Admin router: Users management, Audit logs, Health check
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_org_admin
from app.models.models import User, AuditLog, UserRole
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse, PaginatedResponse, MessageResponse
)
from app.core.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


# ── Users ──────────────────────────────────────────────────────────────────

@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    current_user: User = Depends(require_org_admin()),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [User.organization_id == org_id, User.is_deleted.is_(False)]
    if search:
        term = f"%{search}%"
        filters.append(
            User.email.ilike(term) | User.first_name.ilike(term) | User.last_name.ilike(term)
        )
    if role:
        filters.append(User.role == role)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(User).where(and_(*filters))
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    users = (await db.execute(stmt)).scalars().all()
    return _paginate([UserResponse.model_validate(u) for u in users], total, page, page_size)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_org_admin()),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where(
            User.email == payload.email,
            User.organization_id == current_user.organization_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already exists in this organization")

    user = User(
        organization_id=current_user.organization_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        phone=payload.phone,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_org_admin()),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
            User.is_deleted.is_(False),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: User = Depends(require_org_admin()),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
            User.is_deleted.is_(False),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_org_admin()),
    db: AsyncSession = Depends(get_db),
):
    import datetime as dt
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
            User.is_deleted.is_(False),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user.is_deleted = True
    user.deleted_at = dt.datetime.now(dt.timezone.utc)
    return MessageResponse(message="User deleted successfully")


# ── Audit Logs ─────────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_org_admin()),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [AuditLog.organization_id == org_id]

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(AuditLog).where(and_(*filters))
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    logs = (await db.execute(stmt)).scalars().all()

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return {
        "items": [
            {
                "id": l.id,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "user_id": l.user_id,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
