"""
Meetings router
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Meeting, User
from app.schemas.schemas import (
    MeetingCreate, MeetingUpdate, MeetingResponse, PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/meetings", tags=["Meetings"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("", response_model=PaginatedResponse[MeetingResponse])
async def list_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    organizer_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [Meeting.organization_id == org_id]
    if organizer_id:
        filters.append(Meeting.organizer_id == organizer_id)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Meeting).where(and_(*filters))
        .order_by(Meeting.start_time.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    meetings = (await db.execute(stmt)).scalars().all()
    return _paginate([MeetingResponse.model_validate(m) for m in meetings], total, page, page_size)


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    data["organizer_id"] = current_user.id
    meeting = Meeting(**data)
    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)
    return MeetingResponse.model_validate(meeting)


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.organization_id == current_user.organization_id,
        )
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResponse.model_validate(meeting)


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    payload: MeetingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.organization_id == current_user.organization_id,
        )
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(meeting, k, v)
    await db.flush()
    await db.refresh(meeting)
    return MeetingResponse.model_validate(meeting)


@router.delete("/{meeting_id}", response_model=MessageResponse)
async def delete_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.organization_id == current_user.organization_id,
        )
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    await db.delete(meeting)
    return MessageResponse(message="Meeting deleted successfully")
