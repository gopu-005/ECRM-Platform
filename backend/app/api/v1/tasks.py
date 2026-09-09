"""
Tasks & Meetings routers
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Task, User, TaskStatus
from app.schemas.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [Task.organization_id == org_id, Task.is_deleted.is_(False)]
    if status:
        filters.append(Task.status == status)
    if assigned_to_id:
        filters.append(Task.assigned_to_id == assigned_to_id)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Task).where(and_(*filters))
        .order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    tasks = (await db.execute(stmt)).scalars().all()
    return _paginate([TaskResponse.model_validate(t) for t in tasks], total, page, page_size)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    data["created_by_id"] = current_user.id
    task = Task(**data)
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == current_user.organization_id,
            Task.is_deleted.is_(False),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == current_user.organization_id,
            Task.is_deleted.is_(False),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    if payload.status == TaskStatus.COMPLETED and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == current_user.organization_id,
            Task.is_deleted.is_(False),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="Task deleted successfully")
