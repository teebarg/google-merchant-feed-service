from enum import Enum

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


JOB_TTL_SECONDS = 60 * 60 * 6  # 6 hours
