import os
from dotenv import load_dotenv
import redis
from src.jobs import JobStatus, JOB_TTL_SECONDS
import json
import time

load_dotenv()

redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True, max_connections=10)

LOCK_KEY = "merchant_feed_sync_lock"
LOCK_TTL = 300  # seconds


def acquire_lock():
    return redis_client.set(LOCK_KEY, "locked", nx=True, ex=LOCK_TTL)


def release_lock():
    redis_client.delete(LOCK_KEY)


def create_job(job_id: str):
    redis_client.hset(
        f"sync:job:{job_id}",
        mapping={
            "status": JobStatus.pending,
            "created_at": time.time(),
        },
    )
    redis_client.expire(f"sync:job:{job_id}", JOB_TTL_SECONDS)

def update_job(job_id: str, **fields):
    if "result" in fields:
        fields["result"] = json.dumps(fields["result"])

    redis_client.hset(f"sync:job:{job_id}", mapping=fields)


def get_job(job_id: str):
    data = redis_client.hgetall(f"sync:job:{job_id}")
    if not data:
        return None

    if "result" in data:
        data["result"] = json.loads(data["result"])

    return data


