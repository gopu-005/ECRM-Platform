from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ecrm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.lead_scoring",
        "app.tasks.notifications",
        "app.tasks.csv_import",
        "app.tasks.reports",
        "app.tasks.cleanup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "nightly-analytics-rollup": {
            "task": "app.tasks.cleanup.aggregate_analytics",
            "schedule": 86400,  # every 24h
        },
        "hourly-lead-scoring": {
            "task": "app.tasks.lead_scoring.score_all_leads",
            "schedule": 3600,  # every hour
        },
        "daily-cleanup": {
            "task": "app.tasks.cleanup.cleanup_expired_tokens",
            "schedule": 86400,
        },
    },
)
