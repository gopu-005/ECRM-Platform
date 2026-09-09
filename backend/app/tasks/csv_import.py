"""
CSV import background task.
"""
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.csv_import.import_leads_csv")
def import_leads_csv(job_id: str, org_id: str, rows: list[dict]):
    """Parse and insert leads from CSV data (already parsed rows)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import settings
    from app.models.models import Lead, ImportJob, ImportStatus, LeadStatus
    from datetime import datetime, timezone

    engine = create_engine(settings.DATABASE_URL_SYNC)
    success = 0
    errors = []

    with Session(engine) as session:
        job = session.get(ImportJob, job_id)
        if not job:
            return {"status": "error", "reason": "job_not_found"}

        job.status = ImportStatus.PROCESSING
        job.total_rows = len(rows)
        session.commit()

        for idx, row in enumerate(rows):
            try:
                lead = Lead(
                    organization_id=org_id,
                    first_name=row.get("first_name", ""),
                    last_name=row.get("last_name", ""),
                    email=row.get("email"),
                    phone=row.get("phone"),
                    company=row.get("company"),
                    title=row.get("title"),
                    status=LeadStatus.NEW,
                    industry=row.get("industry"),
                    country=row.get("country"),
                )
                session.add(lead)
                success += 1
            except Exception as e:
                errors.append({"row": idx + 1, "error": str(e)})

        job.status = ImportStatus.COMPLETED
        job.success_rows = success
        job.error_rows = len(errors)
        job.processed_rows = len(rows)
        job.errors = errors
        job.completed_at = datetime.now(timezone.utc)
        session.commit()

    return {"status": "completed", "success": success, "errors": len(errors)}
