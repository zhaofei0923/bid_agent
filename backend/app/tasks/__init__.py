"""Celery application and task registry."""

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bidagent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # ── Beat schedule: daily fetchers at midnight Beijing time ──
    beat_schedule={
        "fetch-wb-daily": {
            "task": "app.tasks.fetcher_tasks.fetch_opportunities",
            "schedule": crontab(hour=0, minute=0),  # 每天北京时间 00:00
            "args": ("wb", 10),
        },
        "fetch-adb-daily": {
            "task": "app.tasks.fetcher_tasks.fetch_opportunities",
            "schedule": crontab(hour=0, minute=10),  # 00:10, 错开避免并发
            "args": ("adb", 10),
        },
        # AfDB is currently disabled: their site blocks server-side requests (HTTP 403 WAF).
        "cleanup-expired-daily": {
            "task": "app.tasks.fetcher_tasks.cleanup_expired_opportunities",
            "schedule": crontab(hour=1, minute=0),  # 01:00, 清理过期机会
        },
    },
)

# Explicitly register task modules
celery_app.conf.include = [
    "app.tasks.fetcher_tasks",
]
