import os
from dotenv import load_dotenv
import redis

load_dotenv()

redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True, max_connections=10)

LOCK_KEY = "merchant_feed_sync_lock"
LOCK_TTL = 300  # seconds


def acquire_lock():
    return redis_client.set(LOCK_KEY, "locked", nx=True, ex=LOCK_TTL)


def release_lock():
    redis_client.delete(LOCK_KEY)
