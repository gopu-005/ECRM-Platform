"""
Contacts router: Full CRUD
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Contact, User
from app.schemas.schemas import (
    ContactCreate, ContactUpdate, ContactResponse, PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [Contact.organization_id == org_id, Contact.is_deleted.is_(False)]

    if search:
        term = f"%{search}%"
        filters.append(or_(
            Contact.first_name.ilike(term),
            Contact.last_name.ilike(term),
            Contact.email.ilike(term),
        ))
    if account_id:
        filters.append(Contact.account_id == account_id)
    if owner_id:
        filters.append(Contact.owner_id == owner_id)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Contact).where(and_(*filters))
        .order_by(Contact.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    contacts = (await db.execute(stmt)).scalars().all()
    return _paginate([ContactResponse.model_validate(c) for c in contacts], total, page, page_size)


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    contact = Contact(**data)
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == current_user.organization_id,
            Contact.is_deleted.is_(False),
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactResponse.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == current_user.organization_id,
            Contact.is_deleted.is_(False),
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(contact, k, v)
    await db.flush()
    await db.refresh(contact)
    return ContactResponse.model_validate(contact)


@router.delete("/{contact_id}", response_model=MessageResponse)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.organization_id == current_user.organization_id,
            Contact.is_deleted.is_(False),
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact.is_deleted = True
    contact.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="Contact deleted successfully")
