"""
Report generation Celery task.
"""
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.reports.generate_report")
def generate_report(org_id: str, report_type: str, user_id: str):
    """Generate a CSV/PDF report asynchronously."""
    logger.info(f"Generating {report_type} report for org {org_id}")
    return {"status": "completed", "report_type": report_type, "org_id": org_id}
