import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ComicPanelBase(BaseModel):
    image_url: str = Field(..., min_length=1)
    panel_order: int = Field(..., ge=0)
    motion_prompt: Optional[str] = None


class ComicPanelCreate(ComicPanelBase):
    project_id: uuid.UUID


class ComicPanelUpdate(BaseModel):
    image_url: Optional[str] = Field(default=None, min_length=1)
    panel_order: Optional[int] = Field(default=None, ge=0)
    motion_prompt: Optional[str] = None


class ComicPanelResponse(ComicPanelBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
