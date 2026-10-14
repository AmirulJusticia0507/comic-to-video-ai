import uuid

from pydantic import BaseModel, Field


class RenderRequest(BaseModel):
    panel_ids: list[uuid.UUID] = Field(min_length=1)


class RenderResponse(BaseModel):
    job_ids: list[uuid.UUID]
    credits_remaining: int
