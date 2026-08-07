import os
import json
import redis
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

def cache_set(key: str, value: dict, ttl: int = 300):
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception:
        pass

def cache_get(key: str) -> Optional[dict]:
    if not redis_client:
        return None
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None

def cache_delete(key: str):
    if not redis_client:
        return
    try:
        redis_client.delete(key)
    except Exception:
        pass
