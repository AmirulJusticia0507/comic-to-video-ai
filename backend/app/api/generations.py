import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.celery_app import RENDER_PANEL_TASK, celery_app
from app.core.database import get_db
from app.models import ComicPanel, Project, RenderJob, User
from app.schemas.generation import RenderRequest, RenderResponse
from app.services.credits import InsufficientCreditsError, deduct_credits

router = APIRouter(prefix="/generations", tags=["generations"])


@router.post("/render", response_model=RenderResponse, status_code=status.HTTP_202_ACCEPTED)
def render(
    payload: RenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    panel_ids = list(dict.fromkeys(payload.panel_ids))

    panels = db.query(ComicPanel).filter(ComicPanel.id.in_(panel_ids)).all()
    if len(panels) != len(panel_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="one or more panels not found")

    project_ids = {panel.project_id for panel in panels}
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    if {project.user_id for project in projects} != {current_user.id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="panels do not belong to current user")

    try:
        deduct_credits(db, current_user, len(panels))
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"insufficient credits: required {exc.required}, available {exc.available}",
        )

    jobs = [RenderJob(panel_id=panel.id, status="PENDING") for panel in panels]
    db.add_all(jobs)
    db.flush()

    pairs = [(str(panel.id), str(job.id)) for panel, job in zip(panels, jobs)]
    job_ids = [job.id for job in jobs]
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    enqueued: list[str] = []
    try:
        for panel_id, job_id in pairs:
            celery_app.send_task(RENDER_PANEL_TASK, args=[panel_id, job_id])
            enqueued.append(job_id)
    except Exception:
        failed_ids = set(job_ids) - {uuid.UUID(job_id) for job_id in enqueued}
        if failed_ids:
            for job in db.query(RenderJob).filter(RenderJob.id.in_(failed_ids)).all():
                job.status = "FAILED"
                job.error_message = "failed to enqueue render job"
            db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="failed to enqueue render jobs")

    return RenderResponse(job_ids=job_ids, credits_remaining=current_user.credits)
