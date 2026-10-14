import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import ComicPanel, Project, RenderJob, User
from app.schemas.job import JobStatusResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(job: RenderJob) -> JobStatusResponse:
    return JobStatusResponse(
        id=job.id,
        panel_id=job.panel_id,
        status=job.status,
        progress=job.progress,
        video_url=job.video_url,
        error_message=job.error_message,
        updated_at=job.updated_at,
    )


def _get_owned_job(db: Session, job_id: uuid.UUID, user_id: uuid.UUID) -> RenderJob:
    job = db.get(RenderJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    panel = db.get(ComicPanel, job.panel_id)
    project = db.get(Project, panel.project_id) if panel else None
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job


@router.get("", response_model=list[JobStatusResponse])
def list_jobs(
    project_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JobStatusResponse]:
    project = db.get(Project, project_id)
    if project is None or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    jobs = (
        db.query(RenderJob)
        .join(ComicPanel, RenderJob.panel_id == ComicPanel.id)
        .filter(ComicPanel.project_id == project_id)
        .order_by(RenderJob.created_at.desc())
        .all()
    )
    return [_to_response(job) for job in jobs]


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobStatusResponse:
    return _to_response(_get_owned_job(db, job_id, current_user.id))
