"""
Activities & Notifications routers
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Activity, Notification, User
from app.schemas.schemas import (
    ActivityResponse, NotificationResponse, PaginatedResponse, MessageResponse
)

# Activities
activities_router = APIRouter(prefix="/activities", tags=["Activities"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@activities_router.get("", response_model=PaginatedResponse[ActivityResponse])
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lead_id: Optional[str] = Query(None),
    deal_id: Optional[str] = Query(None),
    contact_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [Activity.organization_id == org_id]
    if lead_id:
        filters.append(Activity.lead_id == lead_id)
    if deal_id:
        filters.append(Activity.deal_id == deal_id)
    if contact_id:
        filters.append(Activity.contact_id == contact_id)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Activity).where(and_(*filters))
        .order_by(Activity.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    activities = (await db.execute(stmt)).scalars().all()
    return _paginate([ActivityResponse.model_validate(a) for a in activities], total, page, page_size)


# Notifications
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [
        Notification.organization_id == current_user.organization_id,
        Notification.user_id == current_user.id,
    ]
    if unread_only:
        filters.append(Notification.is_read.is_(False))

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Notification).where(and_(*filters))
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    notifs = (await db.execute(stmt)).scalars().all()
    return _paginate([NotificationResponse.model_validate(n) for n in notifs], total, page, page_size)


@notifications_router.patch("/{notif_id}/read", response_model=MessageResponse)
async def mark_notification_read(
    notif_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif and not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
    return MessageResponse(message="Notification marked as read")


@notifications_router.patch("/read-all", response_model=MessageResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import update
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    return MessageResponse(message="All notifications marked as read")
