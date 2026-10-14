import logging
import uuid

from app.core.redis_client import redis_sync_client
from app.schemas.job import JobEvent

logger = logging.getLogger(__name__)

JOB_CHANNEL_PREFIX = "render_job"
JOB_TERMINAL_STATUSES = ("COMPLETED", "FAILED")


def job_channel(job_id: uuid.UUID | str) -> str:
    return f"{JOB_CHANNEL_PREFIX}:{job_id}"


def serialize_job_event(job) -> str:
    return JobEvent.from_job(job).model_dump_json()


def publish_job_event(job) -> bool:
    channel = job_channel(job.id)
    payload = serialize_job_event(job)
    try:
        redis_sync_client.publish(channel, payload)
        return True
    except Exception:
        logger.warning("failed to publish job event to %s", channel, exc_info=True)
        return False