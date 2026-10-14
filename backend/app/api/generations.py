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

    try:
        for panel, job in zip(panels, jobs):
            celery_app.send_task(RENDER_PANEL_TASK, args=[str(panel.id), str(job.id)])
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="failed to enqueue render jobs")

    db.commit()
    return RenderResponse(job_ids=[job.id for job in jobs], credits_remaining=current_user.credits)
