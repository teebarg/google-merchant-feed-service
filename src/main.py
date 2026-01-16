import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException

from src.jobs import JobStatus
from src.locks import create_job, get_job, update_job
from src.scheduler import start_scheduler
from src.sync import sync_products


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    start_scheduler()
    yield


app = FastAPI(title="Google Merchant Feed Service", lifespan=lifespan)

def run_sync_job(job_id: str):
    update_job(
        job_id,
        status=JobStatus.running,
        started_at=time.time(),
        step="starting",
    )

    try:
        update_job(job_id, step="syncing products")
        result = sync_products()

        update_job(
            job_id,
            status=JobStatus.success,
            finished_at=time.time(),
            step="completed",
            result=result,
        )

    except Exception as e:
        update_job(
            job_id,
            status=JobStatus.failed,
            finished_at=time.time(),
            error=str(e),
        )
        raise


@app.post("/sync")
def start_sync(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    create_job(job_id)
    background_tasks.add_task(run_sync_job, job_id)

    return {
        "job_id": job_id,
        "status": "started",
    }

@app.get("/sync/{job_id}")
def sync_status(job_id: str):
    job = get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job

@app.get("/")
def health():
    return {"status": "ok"}
