"""
Accounts router: Full CRUD
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Account, User
from app.schemas.schemas import (
    AccountCreate, AccountUpdate, AccountResponse, PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("", response_model=PaginatedResponse[AccountResponse])
async def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [Account.organization_id == org_id, Account.is_deleted.is_(False)]

    if search:
        term = f"%{search}%"
        filters.append(or_(Account.name.ilike(term), Account.domain.ilike(term)))
    if industry:
        filters.append(Account.industry == industry)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Account).where(and_(*filters))
        .order_by(Account.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    accounts = (await db.execute(stmt)).scalars().all()
    return _paginate([AccountResponse.model_validate(a) for a in accounts], total, page, page_size)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    account = Account(**data)
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.organization_id == current_user.organization_id,
            Account.is_deleted.is_(False),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    payload: AccountUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.organization_id == current_user.organization_id,
            Account.is_deleted.is_(False),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(account, k, v)
    await db.flush()
    await db.refresh(account)
    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", response_model=MessageResponse)
async def delete_account(
    account_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Account).where(
            Account.id == account_id,
            Account.organization_id == current_user.organization_id,
            Account.is_deleted.is_(False),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_deleted = True
    account.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="Account deleted successfully")
