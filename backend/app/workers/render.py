import uuid
from datetime import datetime, timedelta, timezone

from celery.schedules import crontab
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models import ComicPanel, RenderJob
from app.services.ai import generate_video_from_image
from app.services.job_events import JOB_TERMINAL_STATUSES, publish_job_event
from app.services.storage import upload_bytes

JOB_STALE_THRESHOLD_MINUTES = 30


def _get_job(db: Session, job_id: str, panel_id: str) -> RenderJob | None:
    job = db.query(RenderJob).filter(RenderJob.id == uuid.UUID(job_id)).one_or_none()
    if job is None or str(job.panel_id) != panel_id:
        return None
    return job


@celery_app.task(
    name="comic_video.render_panel",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def render_panel(self, panel_id: str, job_id: str):
    db = SessionLocal()
    try:
        job = _get_job(db, job_id, panel_id)
        if job is None:
            return {"status": "orphan", "job_id": job_id}
        if job.status in JOB_TERMINAL_STATUSES:
            return {"status": "skipped", "job_id": job_id, "current_status": job.status}

        panel = db.query(ComicPanel).filter(ComicPanel.id == uuid.UUID(panel_id)).one_or_none()
        if panel is None:
            job.status = "FAILED"
            job.error_message = "panel not found"
            db.commit()
            publish_job_event(job)
            return {"status": "failed", "job_id": job_id}

        job.status = "PROCESSING"
        job.progress = 0
        db.commit()
        publish_job_event(job)

        def on_progress(progress: int) -> None:
            job.progress = min(max(int(progress), 0), 100)
            db.commit()
            publish_job_event(job)

        video_bytes, content_type = generate_video_from_image(
            image_url=panel.image_url,
            motion_prompt=panel.motion_prompt,
            progress_callback=on_progress,
        )

        video_key = f"videos/{job_id}.mp4"
        upload_bytes(video_key, video_bytes, content_type)

        job.status = "COMPLETED"
        job.progress = 100
        job.video_url = video_key
        job.error_message = None
        db.commit()
        publish_job_event(job)
        return {"status": "completed", "job_id": job_id}
    except Exception as exc:
        db.rollback()
        job = _get_job(db, job_id, panel_id)
        if job is not None:
            job.status = "FAILED"
            job.error_message = str(exc)[:1000]
            db.commit()
            publish_job_event(job)
        raise
    finally:
        db.close()


@celery_app.task(name="comic_video.reap_stale_jobs")
def reap_stale_jobs(threshold_minutes: int = JOB_STALE_THRESHOLD_MINUTES):
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)
        stale_jobs = (
            db.query(RenderJob)
            .filter(
                RenderJob.status.in_(("PENDING", "PROCESSING")),
                RenderJob.updated_at < cutoff,
            )
            .all()
        )
        reaped = 0
        for job in stale_jobs:
            job.status = "FAILED"
            job.error_message = f"job stale for more than {threshold_minutes} minutes"
            reaped += 1
        db.commit()
        for job in stale_jobs:
            publish_job_event(job)
        return {"reaped": reaped}
    finally:
        db.close()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute="*/5"),
        reap_stale_jobs.s(),
        name="reap-stale-render-jobs",
    )
