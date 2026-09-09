"""
Leads router: Full CRUD + convert + score
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Lead, User, Activity, ActivityType, LeadStatus
from app.schemas.schemas import (
    LeadCreate, LeadUpdate, LeadResponse, PaginatedResponse, MessageResponse
)
from app.core.config import settings

router = APIRouter(prefix="/leads", tags=["Leads"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[LeadStatus] = Query(None),
    source: Optional[str] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List leads with filtering, searching, and pagination."""
    org_id = current_user.organization_id
    filters = [Lead.organization_id == org_id, Lead.is_deleted.is_(False)]

    if search:
        search_term = f"%{search}%"
        filters.append(
            or_(
                Lead.first_name.ilike(search_term),
                Lead.last_name.ilike(search_term),
                Lead.email.ilike(search_term),
                Lead.company.ilike(search_term),
            )
        )
    if status:
        filters.append(Lead.status == status)
    if source:
        filters.append(Lead.source == source)
    if assigned_to_id:
        filters.append(Lead.assigned_to_id == assigned_to_id)
    if min_score is not None:
        filters.append(Lead.score >= min_score)

    # Count
    count_stmt = select(func.count()).where(and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    sort_col = getattr(Lead, sort_by, Lead.created_at)
    order = sort_col.desc() if sort_dir == "desc" else sort_col.asc()

    stmt = (
        select(Lead)
        .where(and_(*filters))
        .order_by(order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    leads = result.scalars().all()

    return _paginate([LeadResponse.model_validate(l) for l in leads], total, page, page_size)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new lead."""
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    lead = Lead(**data)
    db.add(lead)
    await db.flush()

    # Log activity
    activity = Activity(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        type=ActivityType.NOTE,
        title=f"Lead created: {lead.full_name}",
        lead_id=lead.id,
    )
    db.add(activity)
    await db.flush()
    await db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single lead by ID."""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
            Lead.is_deleted.is_(False),
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a lead."""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
            Lead.is_deleted.is_(False),
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)

    await db.flush()
    await db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.delete("/{lead_id}", response_model=MessageResponse)
async def delete_lead(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a lead."""
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
            Lead.is_deleted.is_(False),
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.is_deleted = True
    lead.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="Lead deleted successfully")


@router.post("/{lead_id}/convert", response_model=MessageResponse)
async def convert_lead(
    lead_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert a lead to a Contact."""
    from app.models.models import Contact
    result = await db.execute(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.organization_id == current_user.organization_id,
            Lead.is_deleted.is_(False),
        )
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status == LeadStatus.CONVERTED:
        raise HTTPException(status_code=400, detail="Lead already converted")

    # Create contact
    contact = Contact(
        organization_id=current_user.organization_id,
        first_name=lead.first_name,
        last_name=lead.last_name,
        email=lead.email,
        phone=lead.phone,
        title=lead.title,
        owner_id=current_user.id,
        lead_id=lead.id,
    )
    db.add(contact)
    await db.flush()

    # Update lead
    lead.status = LeadStatus.CONVERTED
    lead.converted_at = datetime.now(timezone.utc)

    # Log activity
    db.add(Activity(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        type=ActivityType.LEAD_CONVERTED,
        title=f"Lead converted: {lead.full_name}",
        lead_id=lead.id,
        contact_id=contact.id,
    ))

    return MessageResponse(message=f"Lead converted to contact. Contact ID: {contact.id}")


@router.get("/analytics/score", response_model=dict)
async def lead_scoring_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get lead scoring distribution analytics."""
    org_id = current_user.organization_id
    base_filter = and_(Lead.organization_id == org_id, Lead.is_deleted.is_(False))

    total_leads = (await db.execute(select(func.count(Lead.id)).where(base_filter))).scalar() or 0
    avg_score = (await db.execute(select(func.avg(Lead.score)).where(base_filter))).scalar() or 0

    hot_leads = (await db.execute(
        select(func.count(Lead.id)).where(and_(base_filter, Lead.score >= 70))
    )).scalar() or 0

    warm_leads = (await db.execute(
        select(func.count(Lead.id)).where(and_(base_filter, Lead.score >= 40, Lead.score < 70))
    )).scalar() or 0

    cold_leads = (await db.execute(
        select(func.count(Lead.id)).where(and_(base_filter, Lead.score < 40))
    )).scalar() or 0

    return {
        "total_leads": total_leads,
        "average_score": round(float(avg_score), 1),
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "score_distribution": {
            "hot": hot_leads,
            "warm": warm_leads,
            "cold": cold_leads,
        }
    }
