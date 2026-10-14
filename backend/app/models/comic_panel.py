import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ComicPanel(Base):
    __tablename__ = "comic_panels"
    __table_args__ = (UniqueConstraint("project_id", "panel_order", name="uq_comic_panels_project_order"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    panel_order: Mapped[int] = mapped_column(Integer, nullable=False)
    motion_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="panels")
    render_jobs: Mapped[list["RenderJob"]] = relationship(back_populates="panel")
