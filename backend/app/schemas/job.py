import uuid
from datetime import datetime

from pydantic import BaseModel


class JobEvent(BaseModel):
    type: str = "job.update"
    job_id: uuid.UUID
    status: str
    progress: int
    video_url: str | None = None
    error_message: str | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_job(cls, job) -> "JobEvent":
        return cls(
            job_id=job.id,
            status=job.status,
            progress=int(job.progress or 0),
            video_url=job.video_url,
            error_message=job.error_message,
            updated_at=job.updated_at,
        )


class JobStatusResponse(BaseModel):
    id: uuid.UUID
    panel_id: uuid.UUID
    status: str
    progress: int
    video_url: str | None = None
    error_message: str | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}