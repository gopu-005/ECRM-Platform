"""
Deals router: Full CRUD + stage management + pipeline + forecast
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import Deal, User, Activity, ActivityType, DealStage
from app.schemas.schemas import (
    DealCreate, DealUpdate, DealResponse, DealStageUpdate,
    PaginatedResponse, MessageResponse
)

router = APIRouter(prefix="/deals", tags=["Deals"])


def _paginate(items, total, page, page_size):
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("", response_model=PaginatedResponse[DealResponse])
async def list_deals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    stage: Optional[DealStage] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = current_user.organization_id
    filters = [Deal.organization_id == org_id, Deal.is_deleted.is_(False)]

    if search:
        filters.append(Deal.name.ilike(f"%{search}%"))
    if stage:
        filters.append(Deal.stage == stage)
    if assigned_to_id:
        filters.append(Deal.assigned_to_id == assigned_to_id)
    if account_id:
        filters.append(Deal.account_id == account_id)
    if min_value is not None:
        filters.append(Deal.value >= min_value)

    total = (await db.execute(select(func.count()).where(and_(*filters)))).scalar() or 0
    stmt = (
        select(Deal).where(and_(*filters))
        .order_by(Deal.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    deals = (await db.execute(stmt)).scalars().all()
    return _paginate([DealResponse.model_validate(d) for d in deals], total, page, page_size)


@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    payload: DealCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["organization_id"] = current_user.organization_id
    deal = Deal(**data)
    db.add(deal)
    await db.flush()

    db.add(Activity(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        type=ActivityType.DEAL_STAGE_CHANGE,
        title=f"Deal created: {deal.name}",
        deal_id=deal.id,
    ))
    await db.flush()
    await db.refresh(deal)
    return DealResponse.model_validate(deal)


@router.get("/pipeline", response_model=dict)
async def get_pipeline(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Kanban pipeline view — deals grouped by stage."""
    org_id = current_user.organization_id
    filters = [Deal.organization_id == org_id, Deal.is_deleted.is_(False)]
    filters.append(Deal.stage.not_in([DealStage.CLOSED_WON, DealStage.CLOSED_LOST]))

    stmt = select(Deal).where(and_(*filters)).order_by(Deal.value.desc())
    deals = (await db.execute(stmt)).scalars().all()

    pipeline: dict[str, list] = {stage.value: [] for stage in DealStage}
    for deal in deals:
        pipeline[deal.stage.value].append(DealResponse.model_validate(deal).model_dump())

    return pipeline


@router.get("/forecast", response_model=dict)
async def get_forecast(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Revenue forecast based on weighted pipeline values."""
    org_id = current_user.organization_id
    open_filters = and_(
        Deal.organization_id == org_id,
        Deal.is_deleted.is_(False),
        Deal.stage.not_in([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])
    )
    won_filters = and_(
        Deal.organization_id == org_id,
        Deal.is_deleted.is_(False),
        Deal.stage == DealStage.CLOSED_WON
    )

    open_value = (await db.execute(select(func.sum(Deal.value)).where(open_filters))).scalar() or 0
    won_value = (await db.execute(select(func.sum(Deal.value)).where(won_filters))).scalar() or 0
    open_count = (await db.execute(select(func.count(Deal.id)).where(open_filters))).scalar() or 0
    won_count = (await db.execute(select(func.count(Deal.id)).where(won_filters))).scalar() or 0

    # Weighted value
    stmt = select(Deal.value, Deal.probability).where(open_filters)
    open_deals = (await db.execute(stmt)).all()
    weighted = sum(v * (p / 100) for v, p in open_deals)

    return {
        "open_pipeline_value": float(open_value),
        "weighted_forecast": round(float(weighted), 2),
        "closed_won_value": float(won_value),
        "open_deals_count": open_count,
        "closed_won_count": won_count,
    }


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == current_user.organization_id,
            Deal.is_deleted.is_(False),
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return DealResponse.model_validate(deal)


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: str,
    payload: DealUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == current_user.organization_id,
            Deal.is_deleted.is_(False),
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(deal, k, v)
    await db.flush()
    await db.refresh(deal)
    return DealResponse.model_validate(deal)


@router.patch("/{deal_id}/stage", response_model=DealResponse)
async def update_deal_stage(
    deal_id: str,
    payload: DealStageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Move a deal to a new pipeline stage."""
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == current_user.organization_id,
            Deal.is_deleted.is_(False),
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    old_stage = deal.stage
    deal.stage = payload.stage
    if payload.lost_reason:
        deal.lost_reason = payload.lost_reason
    if payload.stage in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]:
        deal.actual_close_date = datetime.now(timezone.utc)

    db.add(Activity(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        type=ActivityType.DEAL_STAGE_CHANGE,
        title=f"Deal stage changed: {old_stage.value} → {payload.stage.value}",
        deal_id=deal.id,
    ))
    await db.flush()
    await db.refresh(deal)
    return DealResponse.model_validate(deal)


@router.delete("/{deal_id}", response_model=MessageResponse)
async def delete_deal(
    deal_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.organization_id == current_user.organization_id,
            Deal.is_deleted.is_(False),
        )
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.is_deleted = True
    deal.deleted_at = datetime.now(timezone.utc)
    return MessageResponse(message="Deal deleted successfully")
