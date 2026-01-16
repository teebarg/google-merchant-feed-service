from fastapi import FastAPI, HTTPException
from src.sync import sync_products
from src.scheduler import start_scheduler
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, HTTPException
import uuid
import time
from src.jobs import JobStatus
from src.locks import create_job, update_job, get_job


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


@app.get("/sync")
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
