import redis as redis_sync
import redis.asyncio as redis

from app.core.config import get_settings

_redis_url = get_settings().redis_url

redis_client = redis.from_url(_redis_url, decode_responses=True, protocol=2)
redis_sync_client = redis_sync.from_url(_redis_url, decode_responses=True, protocol=2)