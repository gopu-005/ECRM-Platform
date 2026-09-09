"""
Analytics router: Dashboard KPIs, lead funnel, pipeline, revenue, team performance
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, extract
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import (
    Lead, Contact, Account, Deal, Task, Meeting, Activity, User,
    LeadStatus, DealStage, TaskStatus
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _kpi(label, value, change=None, trend=None, unit=None):
    return {
        "label": label,
        "value": value,
        "change_percent": change,
        "trend": trend,
        "unit": unit,
    }


@router.get("/dashboard")
async def dashboard_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """20+ KPI dashboard summary."""
    org_id = current_user.organization_id
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Leads
    total_leads = (await db.execute(
        select(func.count(Lead.id)).where(Lead.organization_id == org_id, Lead.is_deleted.is_(False))
    )).scalar() or 0

    converted_leads = (await db.execute(
        select(func.count(Lead.id)).where(
            Lead.organization_id == org_id,
            Lead.status == LeadStatus.CONVERTED,
            Lead.is_deleted.is_(False),
        )
    )).scalar() or 0

    avg_score = (await db.execute(
        select(func.avg(Lead.score)).where(Lead.organization_id == org_id, Lead.is_deleted.is_(False))
    )).scalar() or 0

    # Contacts / Accounts
    total_contacts = (await db.execute(
        select(func.count(Contact.id)).where(Contact.organization_id == org_id, Contact.is_deleted.is_(False))
    )).scalar() or 0

    total_accounts = (await db.execute(
        select(func.count(Account.id)).where(Account.organization_id == org_id, Account.is_deleted.is_(False))
    )).scalar() or 0

    # Deals
    deal_filter = and_(Deal.organization_id == org_id, Deal.is_deleted.is_(False))
    total_deals = (await db.execute(select(func.count(Deal.id)).where(deal_filter))).scalar() or 0

    open_deal_filter = and_(
        deal_filter,
        Deal.stage.not_in([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])
    )
    pipeline_value = (await db.execute(
        select(func.sum(Deal.value)).where(open_deal_filter)
    )).scalar() or 0

    # Win rate
    closed_deals = (await db.execute(
        select(func.count(Deal.id)).where(
            and_(deal_filter, Deal.stage.in_([DealStage.CLOSED_WON, DealStage.CLOSED_LOST]))
        )
    )).scalar() or 0
    won_deals = (await db.execute(
        select(func.count(Deal.id)).where(and_(deal_filter, Deal.stage == DealStage.CLOSED_WON))
    )).scalar() or 0
    win_rate = round((won_deals / closed_deals * 100) if closed_deals > 0 else 0, 1)

    avg_deal_size = (await db.execute(
        select(func.avg(Deal.value)).where(open_deal_filter)
    )).scalar() or 0

    # Weighted pipeline
    open_deals_data = (await db.execute(
        select(Deal.value, Deal.probability).where(open_deal_filter)
    )).all()
    weighted_pipeline = sum(v * (p / 100) for v, p in open_deals_data)

    # Tasks
    open_tasks = (await db.execute(
        select(func.count(Task.id)).where(
            and_(
                Task.organization_id == org_id,
                Task.status != TaskStatus.COMPLETED,
                Task.status != TaskStatus.CANCELLED,
                Task.is_deleted.is_(False),
            )
        )
    )).scalar() or 0

    # Meetings
    upcoming_meetings = (await db.execute(
        select(func.count(Meeting.id)).where(
            and_(Meeting.organization_id == org_id, Meeting.start_time > now)
        )
    )).scalar() or 0

    # Activities this week
    week_ago = now - timedelta(days=7)
    activities_week = (await db.execute(
        select(func.count(Activity.id)).where(
            and_(Activity.organization_id == org_id, Activity.created_at >= week_ago)
        )
    )).scalar() or 0

    # Lead by status
    lead_status_rows = (await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(and_(Lead.organization_id == org_id, Lead.is_deleted.is_(False)))
        .group_by(Lead.status)
    )).all()
    lead_by_status = [{"status": s.value, "count": c} for s, c in lead_status_rows]

    # Deal by stage
    deal_stage_rows = (await db.execute(
        select(Deal.stage, func.count(Deal.id), func.sum(Deal.value))
        .where(deal_filter)
        .group_by(Deal.stage)
    )).all()
    deal_by_stage = [{"stage": s.value, "count": c, "total_value": float(v or 0)} for s, c, v in deal_stage_rows]

    # Revenue trend (last 6 months, monthly)
    revenue_trend = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        rev = (await db.execute(
            select(func.sum(Deal.value)).where(
                and_(
                    deal_filter,
                    Deal.stage == DealStage.CLOSED_WON,
                    Deal.actual_close_date >= month_start,
                    Deal.actual_close_date < month_end,
                )
            )
        )).scalar() or 0
        revenue_trend.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": float(rev),
        })

    # Top 5 deals
    top_deals_rows = (await db.execute(
        select(Deal).where(open_deal_filter).order_by(Deal.value.desc()).limit(5)
    )).scalars().all()

    from app.schemas.schemas import DealResponse
    top_deals = [DealResponse.model_validate(d).model_dump() for d in top_deals_rows]

    # Recent activities
    recent_acts = (await db.execute(
        select(Activity).where(Activity.organization_id == org_id)
        .order_by(Activity.created_at.desc()).limit(10)
    )).scalars().all()
    from app.schemas.schemas import ActivityResponse
    recent_activities = [ActivityResponse.model_validate(a).model_dump() for a in recent_acts]

    conversion_rate = round((converted_leads / total_leads * 100) if total_leads > 0 else 0, 1)

    return {
        "kpis": {
            "total_leads": _kpi("Total Leads", total_leads, unit="leads"),
            "lead_conversion_rate": _kpi("Conversion Rate", conversion_rate, unit="%"),
            "avg_lead_score": _kpi("Avg Lead Score", round(float(avg_score), 1)),
            "total_contacts": _kpi("Total Contacts", total_contacts),
            "total_accounts": _kpi("Total Accounts", total_accounts),
            "total_deals": _kpi("Total Deals", total_deals),
            "pipeline_value": _kpi("Pipeline Value", round(float(pipeline_value), 2), unit="USD"),
            "weighted_pipeline": _kpi("Weighted Pipeline", round(float(weighted_pipeline), 2), unit="USD"),
            "win_rate": _kpi("Win Rate", win_rate, unit="%"),
            "avg_deal_size": _kpi("Avg Deal Size", round(float(avg_deal_size), 2), unit="USD"),
            "open_tasks": _kpi("Open Tasks", open_tasks),
            "upcoming_meetings": _kpi("Upcoming Meetings", upcoming_meetings),
            "activities_this_week": _kpi("Activities This Week", activities_week),
        },
        "lead_by_status": lead_by_status,
        "deal_by_stage": deal_by_stage,
        "revenue_trend": revenue_trend,
        "top_deals": top_deals,
        "recent_activities": recent_activities,
    }


@router.get("/leads")
async def lead_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lead funnel analytics."""
    org_id = current_user.organization_id
    base = and_(Lead.organization_id == org_id, Lead.is_deleted.is_(False))

    by_source = (await db.execute(
        select(Lead.source, func.count(Lead.id))
        .where(base).group_by(Lead.source)
    )).all()

    by_status = (await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(base).group_by(Lead.status)
    )).all()

    monthly_new = []
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = (await db.execute(
            select(func.count(Lead.id)).where(
                and_(base, Lead.created_at >= month_start, Lead.created_at < month_end)
            )
        )).scalar() or 0
        monthly_new.append({"month": month_start.strftime("%b %Y"), "count": count})

    return {
        "by_source": [{"source": (s.value if s else "unknown"), "count": c} for s, c in by_source],
        "by_status": [{"status": s.value, "count": c} for s, c in by_status],
        "monthly_new_leads": monthly_new,
    }


@router.get("/pipeline")
async def pipeline_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Pipeline stage analytics."""
    org_id = current_user.organization_id
    base = and_(Deal.organization_id == org_id, Deal.is_deleted.is_(False))

    by_stage = (await db.execute(
        select(Deal.stage, func.count(Deal.id), func.sum(Deal.value))
        .where(base).group_by(Deal.stage)
    )).all()

    return {
        "stages": [
            {"stage": s.value, "count": c, "total_value": float(v or 0)}
            for s, c, v in by_stage
        ]
    }


@router.get("/revenue")
async def revenue_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Revenue trends (12 months)."""
    org_id = current_user.organization_id
    base = and_(Deal.organization_id == org_id, Deal.is_deleted.is_(False), Deal.stage == DealStage.CLOSED_WON)
    now = datetime.now(timezone.utc)

    monthly = []
    for i in range(11, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        rev = (await db.execute(
            select(func.sum(Deal.value)).where(
                and_(base, Deal.actual_close_date >= month_start, Deal.actual_close_date < month_end)
            )
        )).scalar() or 0
        count = (await db.execute(
            select(func.count(Deal.id)).where(
                and_(base, Deal.actual_close_date >= month_start, Deal.actual_close_date < month_end)
            )
        )).scalar() or 0
        monthly.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": float(rev),
            "deals_closed": count,
        })

    total_revenue = sum(m["revenue"] for m in monthly)
    return {"monthly_revenue": monthly, "total_revenue_12m": total_revenue}


@router.get("/team-performance")
async def team_performance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Per-rep performance metrics."""
    org_id = current_user.organization_id

    reps = (await db.execute(
        select(User).where(User.organization_id == org_id, User.is_deleted.is_(False), User.is_active.is_(True))
    )).scalars().all()

    results = []
    for rep in reps:
        deals_won = (await db.execute(
            select(func.count(Deal.id)).where(
                Deal.assigned_to_id == rep.id,
                Deal.stage == DealStage.CLOSED_WON,
                Deal.is_deleted.is_(False),
            )
        )).scalar() or 0
        revenue = (await db.execute(
            select(func.sum(Deal.value)).where(
                Deal.assigned_to_id == rep.id,
                Deal.stage == DealStage.CLOSED_WON,
                Deal.is_deleted.is_(False),
            )
        )).scalar() or 0
        open_deals = (await db.execute(
            select(func.count(Deal.id)).where(
                Deal.assigned_to_id == rep.id,
                Deal.is_deleted.is_(False),
                Deal.stage.not_in([DealStage.CLOSED_WON, DealStage.CLOSED_LOST])
            )
        )).scalar() or 0

        results.append({
            "user_id": rep.id,
            "name": rep.full_name,
            "role": rep.role.value,
            "deals_won": deals_won,
            "revenue_generated": float(revenue),
            "open_deals": open_deals,
        })

    # Sort by revenue
    results.sort(key=lambda x: x["revenue_generated"], reverse=True)
    return {"team_performance": results}


@router.get("/conversion")
async def conversion_funnel(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lead → Contact → Deal → Won conversion funnel."""
    org_id = current_user.organization_id

    total_leads = (await db.execute(
        select(func.count(Lead.id)).where(Lead.organization_id == org_id, Lead.is_deleted.is_(False))
    )).scalar() or 0

    total_contacts = (await db.execute(
        select(func.count(Contact.id)).where(Contact.organization_id == org_id, Contact.is_deleted.is_(False))
    )).scalar() or 0

    total_deals = (await db.execute(
        select(func.count(Deal.id)).where(Deal.organization_id == org_id, Deal.is_deleted.is_(False))
    )).scalar() or 0

    won_deals = (await db.execute(
        select(func.count(Deal.id)).where(
            Deal.organization_id == org_id,
            Deal.stage == DealStage.CLOSED_WON,
            Deal.is_deleted.is_(False),
        )
    )).scalar() or 0

    return {
        "funnel": [
            {"stage": "Leads", "count": total_leads},
            {"stage": "Contacts", "count": total_contacts},
            {"stage": "Deals", "count": total_deals},
            {"stage": "Won", "count": won_deals},
        ],
        "lead_to_contact_rate": round(total_contacts / total_leads * 100 if total_leads else 0, 1),
        "contact_to_deal_rate": round(total_deals / total_contacts * 100 if total_contacts else 0, 1),
        "deal_to_won_rate": round(won_deals / total_deals * 100 if total_deals else 0, 1),
    }
