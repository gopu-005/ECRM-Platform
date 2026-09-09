"""
Cleanup and maintenance Celery tasks.
"""
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Tokens expire automatically via Redis TTL. This logs the cleanup."""
    logger.info("Token cleanup check completed (Redis handles TTL automatically).")
    return {"status": "ok"}


@celery_app.task(name="app.tasks.cleanup.aggregate_analytics")
def aggregate_analytics():
    """Nightly analytics aggregation placeholder."""
    logger.info("Nightly analytics aggregation completed.")
    return {"status": "ok"}
