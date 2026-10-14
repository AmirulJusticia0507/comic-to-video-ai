import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models import ComicPanel, Project, User
from app.schemas.comic_panel import ComicPanelCreate, ComicPanelResponse, ComicPanelUpdate

router = APIRouter(prefix="/panels", tags=["panels"])


def _get_owned_panel(db: Session, panel_id: uuid.UUID, user_id: uuid.UUID) -> ComicPanel:
    panel = (
        db.query(ComicPanel)
        .join(Project)
        .filter(ComicPanel.id == panel_id, Project.user_id == user_id)
        .first()
    )
    if panel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="panel not found",
        )
    return panel


def _get_owned_project(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="project not found",
        )
    return project


@router.post("", response_model=ComicPanelResponse, status_code=status.HTTP_201_CREATED)
def create_panel(
    payload: ComicPanelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComicPanelResponse:
    _get_owned_project(db, payload.project_id, current_user.id)
    panel = ComicPanel(**payload.model_dump())
    db.add(panel)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="panel_order must be unique within a project",
        )
    db.refresh(panel)
    return panel


@router.get("", response_model=list[ComicPanelResponse])
def list_panels(
    project_id: Optional[uuid.UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ComicPanelResponse]:
    query = db.query(ComicPanel).join(Project).filter(Project.user_id == current_user.id)
    if project_id is not None:
        query = query.filter(ComicPanel.project_id == project_id)
    return query.order_by(ComicPanel.panel_order).all()


@router.get("/{panel_id}", response_model=ComicPanelResponse)
def get_panel(
    panel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComicPanelResponse:
    return _get_owned_panel(db, panel_id, current_user.id)


@router.patch("/{panel_id}", response_model=ComicPanelResponse)
def update_panel(
    panel_id: uuid.UUID,
    payload: ComicPanelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComicPanelResponse:
    panel = _get_owned_panel(db, panel_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(panel, field, value)
    db.commit()
    db.refresh(panel)
    return panel


@router.delete("/{panel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_panel(
    panel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    panel = _get_owned_panel(db, panel_id, current_user.id)
    db.delete(panel)
    db.commit()
    return None
