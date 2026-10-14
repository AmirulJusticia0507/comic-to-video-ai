from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "comic_to_video",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,
    timezone="UTC",
    enable_utc=True,
)

RENDER_PANEL_TASK = "comic_to_video.render_panel"
