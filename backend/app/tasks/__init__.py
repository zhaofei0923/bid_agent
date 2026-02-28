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
    # ── Beat schedule: daily crawlers at midnight Beijing time ──
    beat_schedule={
        "crawl-adb-daily": {
            "task": "app.tasks.crawler_tasks.crawl_opportunities",
            "schedule": crontab(hour=0, minute=0),  # 每天北京时间 00:00
            "args": ("adb", 10),
        },
        "crawl-wb-daily": {
            "task": "app.tasks.crawler_tasks.crawl_opportunities",
            "schedule": crontab(hour=0, minute=5),  # 00:05, 错开避免并发
            "args": ("wb", 10),
        },
    },
)

# Auto-discover tasks from app.tasks sub-modules
celery_app.autodiscover_tasks(["app.tasks"])
