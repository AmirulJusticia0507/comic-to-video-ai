import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

_ALLOWED_PROJECT_STATUS = {"draft", "processing", "completed"}


class ProjectBase(BaseModel):
    title: str = Field(..., max_length=255)
    status: Optional[str] = "draft"

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _ALLOWED_PROJECT_STATUS:
            raise ValueError("status must be one of: draft, processing, completed")
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _ALLOWED_PROJECT_STATUS:
            raise ValueError("status must be one of: draft, processing, completed")
        return v


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
