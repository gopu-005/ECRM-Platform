"""
Lead scoring background task.
Scores leads based on multiple criteria:
  - Email provided (+10)
  - Phone provided (+10)
  - Company provided (+10)
  - Annual revenue tiers (+0 to +25)
  - Employee count (+0 to +15)
  - Source quality (+0 to +15)
  - Status advancement (+5 to +20)
"""
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


def calculate_lead_score(lead_data: dict) -> int:
    """Pure function: calculate lead score from lead attributes."""
    score = 0

    # Contact info completeness
    if lead_data.get("email"):
        score += 10
    if lead_data.get("phone"):
        score += 10
    if lead_data.get("company"):
        score += 10

    # Revenue tier
    revenue = lead_data.get("annual_revenue") or 0
    if revenue >= 10_000_000:
        score += 25
    elif revenue >= 1_000_000:
        score += 15
    elif revenue >= 100_000:
        score += 5

    # Employee count
    employees = lead_data.get("employee_count") or 0
    if employees >= 500:
        score += 15
    elif employees >= 100:
        score += 10
    elif employees >= 10:
        score += 5

    # Source quality
    source_scores = {
        "referral": 15,
        "website": 10,
        "email": 8,
        "trade_show": 12,
        "social_media": 5,
        "cold_call": 3,
        "advertisement": 5,
    }
    source = lead_data.get("source")
    if source:
        score += source_scores.get(source, 0)

    # Status
    status_scores = {
        "new": 0,
        "contacted": 5,
        "qualified": 20,
        "unqualified": -10,
        "converted": 30,
    }
    status = lead_data.get("status", "new")
    score += status_scores.get(status, 0)

    return max(0, min(100, score))  # Clamp 0-100


@celery_app.task(name="app.tasks.lead_scoring.score_lead", bind=True, max_retries=3)
def score_lead(self, lead_id: str, org_id: str):
    """Score a single lead and update the database."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.core.config import settings
        from app.models.models import Lead

        engine = create_engine(settings.DATABASE_URL_SYNC)
        with Session(engine) as session:
            lead = session.get(Lead, lead_id)
            if not lead or lead.organization_id != org_id:
                return {"status": "not_found", "lead_id": lead_id}

            lead_data = {
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "annual_revenue": lead.annual_revenue,
                "employee_count": lead.employee_count,
                "source": lead.source.value if lead.source else None,
                "status": lead.status.value,
            }
            new_score = calculate_lead_score(lead_data)
            lead.score = new_score
            session.commit()

        return {"status": "scored", "lead_id": lead_id, "score": new_score}
    except Exception as exc:
        logger.error(f"Lead scoring failed for {lead_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.lead_scoring.score_all_leads")
def score_all_leads():
    """Batch re-score all active leads across all organizations."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.models.models import Lead

    engine = create_engine(settings.DATABASE_URL_SYNC)
    updated = 0
    with Session(engine) as session:
        leads = session.query(Lead).filter(Lead.is_deleted.is_(False)).all()
        for lead in leads:
            lead_data = {
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "annual_revenue": lead.annual_revenue,
                "employee_count": lead.employee_count,
                "source": lead.source.value if lead.source else None,
                "status": lead.status.value,
            }
            lead.score = calculate_lead_score(lead_data)
            updated += 1
        session.commit()

    logger.info(f"Batch scored {updated} leads")
    return {"updated": updated}
