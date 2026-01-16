import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.jobs import JobStatus
from src.main import app, run_sync_job


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_endpoint(self, client):
        """Test health check returns ok."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestStartSyncEndpoint:
    """Tests for /sync endpoint."""

    @patch("src.main.sync_products")
    @patch("src.main.create_job")
    def test_start_sync_creates_job(self, mock_create_job, mock_sync_products):
        """Test that starting sync creates a job and adds it to background tasks."""
        # Mock sync_products to return quickly without errors
        mock_sync_products.return_value = {"inserted": 0, "updated": 0, "deleted": 0}

        client = TestClient(app)
        response = client.post("/sync")

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"

        # Verify job was created
        mock_create_job.assert_called_once()
        # Verify the job_id in the response matches what was passed to create_job
        assert mock_create_job.call_args[0][0] == data["job_id"]


class TestSyncStatusEndpoint:
    """Tests for /sync/{job_id} endpoint."""

    @patch("src.main.get_job")
    def test_sync_status_success(self, mock_get_job):
        """Test retrieving sync status for existing job."""
        job_id = str(uuid.uuid4())
        mock_job = {
            "status": JobStatus.running,
            "created_at": str(time.time()),
            "started_at": str(time.time()),
            "step": "syncing products",
        }
        mock_get_job.return_value = mock_job

        client = TestClient(app)
        response = client.get(f"/sync/{job_id}")

        assert response.status_code == 200
        assert response.json() == mock_job
        mock_get_job.assert_called_once_with(job_id)

    @patch("src.main.get_job")
    def test_sync_status_not_found(self, mock_get_job):
        """Test retrieving sync status for non-existent job."""
        job_id = str(uuid.uuid4())
        mock_get_job.return_value = None

        client = TestClient(app)
        response = client.get(f"/sync/{job_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Job not found"}
        mock_get_job.assert_called_once_with(job_id)

    @patch("src.main.get_job")
    def test_sync_status_success_with_result(self, mock_get_job):
        """Test retrieving sync status with completed result."""
        job_id = str(uuid.uuid4())
        mock_job = {
            "status": JobStatus.success,
            "created_at": str(time.time()),
            "started_at": str(time.time()),
            "finished_at": str(time.time()),
            "step": "completed",
            "result": {
                "inserted": 10,
                "updated": 5,
                "deleted": 2,
            },
        }
        mock_get_job.return_value = mock_job

        client = TestClient(app)
        response = client.get(f"/sync/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == JobStatus.success
        assert data["result"]["inserted"] == 10


class TestRunSyncJob:
    """Tests for run_sync_job function."""

    @patch("src.main.sync_products")
    @patch("src.main.update_job")
    def test_run_sync_job_success(self, mock_update_job, mock_sync_products):
        """Test successful sync job execution."""
        job_id = str(uuid.uuid4())
        sync_result = {
            "inserted": 10,
            "updated": 5,
            "deleted": 2,
        }
        mock_sync_products.return_value = sync_result

        run_sync_job(job_id)

        # Verify job status updates
        assert mock_update_job.call_count >= 3  # At least: starting, syncing, completed

        # Check final update with success status
        final_call = mock_update_job.call_args_list[-1]
        assert final_call[1]["status"] == JobStatus.success
        assert final_call[1]["result"] == sync_result
        assert "finished_at" in final_call[1]

    @patch("src.main.sync_products")
    @patch("src.main.update_job")
    def test_run_sync_job_failure(self, mock_update_job, mock_sync_products):
        """Test sync job execution with error."""
        job_id = str(uuid.uuid4())
        error_message = "Database connection failed"
        mock_sync_products.side_effect = Exception(error_message)

        with pytest.raises(Exception, match=error_message):
            run_sync_job(job_id)

        # Verify job status was updated to failed
        final_call = mock_update_job.call_args_list[-1]
        assert final_call[1]["status"] == JobStatus.failed
        assert final_call[1]["error"] == error_message
        assert "finished_at" in final_call[1]

    @patch("src.main.sync_products")
    @patch("src.main.update_job")
    def test_run_sync_job_updates_step(self, mock_update_job, mock_sync_products):
        """Test that job step is updated during execution."""
        job_id = str(uuid.uuid4())
        mock_sync_products.return_value = {"inserted": 0, "updated": 0, "deleted": 0}

        run_sync_job(job_id)

        # Verify step updates
        calls = [call[1].get("step") for call in mock_update_job.call_args_list if "step" in call[1]]
        assert "starting" in calls
        assert "syncing products" in calls
        assert "completed" in calls
