import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.core.database import SessionLocal
from app.core.redis_client import redis_client
from app.core.security import decode_access_token
from app.models import ComicPanel, Project, RenderJob
from app.schemas.job import JobEvent
from app.services.job_events import JOB_TERMINAL_STATUSES, job_channel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["jobs"])

POLL_INTERVAL_SECONDS = 2.0

WS_UNAUTHORIZED = 4401
WS_NOT_FOUND = 4404
WS_BAD_REQUEST = 4400


def _resolve_user_id(websocket: WebSocket) -> uuid.UUID | None:
    token = websocket.query_params.get("token")
    if not token:
        header = websocket.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            token = header[7:].strip()
    subject = decode_access_token(token) if token else None
    if not subject:
        return None
    try:
        return uuid.UUID(subject)
    except ValueError:
        return None


def _load_authorized_job(job_id: uuid.UUID, user_id: uuid.UUID) -> JobEvent | None:
    db = SessionLocal()
    try:
        job = (
            db.query(RenderJob)
            .join(ComicPanel, RenderJob.panel_id == ComicPanel.id)
            .join(Project, ComicPanel.project_id == Project.id)
            .filter(RenderJob.id == job_id, Project.user_id == user_id)
            .one_or_none()
        )
        return JobEvent.from_job(job) if job else None
    finally:
        db.close()


def _load_job_event(job_id: uuid.UUID) -> JobEvent | None:
    db = SessionLocal()
    try:
        job = db.query(RenderJob).filter(RenderJob.id == job_id).one_or_none()
        return JobEvent.from_job(job) if job else None
    finally:
        db.close()


async def _drain_client_messages(websocket: WebSocket) -> None:
    while True:
        message = await websocket.receive_text()
        if message.strip() == "ping":
            await websocket.send_text(json.dumps({"type": "pong"}))


@router.websocket("/jobs/{job_id}")
async def stream_job_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()

    user_id = _resolve_user_id(websocket)
    if user_id is None:
        await websocket.close(code=WS_UNAUTHORIZED)
        return

    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        await websocket.close(code=WS_BAD_REQUEST)
        return

    current = await run_in_threadpool(_load_authorized_job, job_uuid, user_id)
    if current is None:
        await websocket.close(code=WS_NOT_FOUND)
        return

    try:
        await websocket.send_text(current.model_dump_json())
        if current.status in JOB_TERMINAL_STATUSES:
            await websocket.close()
            return
        await _bridge_pubsub(websocket, job_uuid, current)
    except WebSocketDisconnect:
        return
    finally:
        await _safe_close(websocket)


async def _bridge_pubsub(websocket: WebSocket, job_id: uuid.UUID, current: JobEvent) -> None:
    pubsub = await _subscribe(job_id)
    reader = asyncio.create_task(_drain_client_messages(websocket))
    try:
        while not reader.done():
            message = (
                await pubsub.get_message(ignore_subscribe_messages=True, timeout=POLL_INTERVAL_SECONDS)
                if pubsub is not None
                else None
            )
            if message is not None:
                current = _apply(current, message["data"])
                await websocket.send_text(message["data"])
                if current is not None and current.status in JOB_TERMINAL_STATUSES:
                    break
            else:
                fresh = await run_in_threadpool(_load_job_event, job_id)
                if fresh is not None and fresh != current:
                    current = fresh
                    await websocket.send_text(fresh.model_dump_json())
                    if fresh.status in JOB_TERMINAL_STATUSES:
                        break
    finally:
        reader.cancel()
        try:
            reader.exception()
        except Exception:
            pass
        if pubsub is not None:
            try:
                await pubsub.unsubscribe(job_channel(job_id))
                await pubsub.aclose()
            except Exception:
                logger.warning("failed to close pubsub for job %s", job_id, exc_info=True)


async def _subscribe(job_id: uuid.UUID):
    try:
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(job_channel(job_id))
        return pubsub
    except Exception:
        logger.warning("redis pubsub unavailable for job %s, falling back to db polling", job_id, exc_info=True)
        return None


def _apply(current: JobEvent, payload: str) -> JobEvent | None:
    try:
        return JobEvent.model_validate_json(payload)
    except Exception:
        return current


async def _safe_close(websocket: WebSocket) -> None:
    try:
        await websocket.close()
    except Exception:
        pass