import json
import time
from unittest.mock import MagicMock, patch

from src.jobs import JOB_TTL_SECONDS, JobStatus
from src.locks import (
    LOCK_KEY,
    LOCK_TTL,
    acquire_lock,
    create_job,
    get_job,
    release_lock,
    update_job,
)


class TestAcquireLock:
    """Tests for acquire_lock function."""

    @patch("src.locks.redis_client")
    def test_acquire_lock_success(self, mock_redis):
        """Test successful lock acquisition."""
        mock_redis.set.return_value = True

        result = acquire_lock()

        assert result is True
        mock_redis.set.assert_called_once_with(LOCK_KEY, "locked", nx=True, ex=LOCK_TTL)

    @patch("src.locks.redis_client")
    def test_acquire_lock_failure(self, mock_redis):
        """Test failed lock acquisition (lock already exists)."""
        mock_redis.set.return_value = False

        result = acquire_lock()

        assert result is False
        mock_redis.set.assert_called_once_with(LOCK_KEY, "locked", nx=True, ex=LOCK_TTL)


class TestReleaseLock:
    """Tests for release_lock function."""

    @patch("src.locks.redis_client")
    def test_release_lock(self, mock_redis):
        """Test lock release."""
        release_lock()

        mock_redis.delete.assert_called_once_with(LOCK_KEY)


class TestCreateJob:
    """Tests for create_job function."""

    @patch("src.locks.redis_client")
    def test_create_job(self, mock_redis):
        """Test job creation."""
        job_id = "test-job-123"
        mock_redis.hset = MagicMock()
        mock_redis.expire = MagicMock()

        create_job(job_id)

        # Verify hset was called with correct parameters
        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == f"sync:job:{job_id}"
        assert "status" in call_args[1]["mapping"]
        assert call_args[1]["mapping"]["status"] == JobStatus.pending
        assert "created_at" in call_args[1]["mapping"]

        # Verify expire was called
        mock_redis.expire.assert_called_once_with(f"sync:job:{job_id}", JOB_TTL_SECONDS)


class TestUpdateJob:
    """Tests for update_job function."""

    @patch("src.locks.redis_client")
    def test_update_job_basic_fields(self, mock_redis):
        """Test updating job with basic fields."""
        job_id = "test-job-123"
        mock_redis.hset = MagicMock()

        update_job(job_id, status=JobStatus.running, step="syncing")

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[0][0] == f"sync:job:{job_id}"
        assert call_args[1]["mapping"]["status"] == JobStatus.running
        assert call_args[1]["mapping"]["step"] == "syncing"

    @patch("src.locks.redis_client")
    def test_update_job_with_result(self, mock_redis):
        """Test updating job with result (should be JSON encoded)."""
        job_id = "test-job-123"
        mock_redis.hset = MagicMock()
        result = {"inserted": 10, "updated": 5, "deleted": 2}

        update_job(job_id, result=result)

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        assert call_args[1]["mapping"]["result"] == json.dumps(result)

    @patch("src.locks.redis_client")
    def test_update_job_multiple_fields(self, mock_redis):
        """Test updating job with multiple fields."""
        job_id = "test-job-123"
        mock_redis.hset = MagicMock()
        current_time = time.time()

        update_job(
            job_id,
            status=JobStatus.success,
            finished_at=current_time,
            step="completed",
            error=None,
        )

        mock_redis.hset.assert_called_once()
        call_args = mock_redis.hset.call_args
        mapping = call_args[1]["mapping"]
        assert mapping["status"] == JobStatus.success
        assert mapping["finished_at"] == current_time
        assert mapping["step"] == "completed"


class TestGetJob:
    """Tests for get_job function."""

    @patch("src.locks.redis_client")
    def test_get_job_success(self, mock_redis):
        """Test retrieving an existing job."""
        job_id = "test-job-123"
        mock_data = {
            "status": JobStatus.running,
            "created_at": "1704067200.0",
            "started_at": "1704067201.0",
            "step": "syncing products",
        }
        mock_redis.hgetall.return_value = mock_data

        result = get_job(job_id)

        assert result == mock_data
        mock_redis.hgetall.assert_called_once_with(f"sync:job:{job_id}")

    @patch("src.locks.redis_client")
    def test_get_job_not_found(self, mock_redis):
        """Test retrieving a non-existent job."""
        job_id = "test-job-123"
        mock_redis.hgetall.return_value = {}

        result = get_job(job_id)

        assert result is None

    @patch("src.locks.redis_client")
    def test_get_job_with_result(self, mock_redis):
        """Test retrieving job with JSON-encoded result."""
        job_id = "test-job-123"
        result_data = {"inserted": 10, "updated": 5, "deleted": 2}
        mock_data = {
            "status": JobStatus.success,
            "result": json.dumps(result_data),
        }
        mock_redis.hgetall.return_value = mock_data

        result = get_job(job_id)

        assert result["status"] == JobStatus.success
        assert result["result"] == result_data  # Should be decoded
        assert isinstance(result["result"], dict)

    @patch("src.locks.redis_client")
    def test_get_job_without_result(self, mock_redis):
        """Test retrieving job without result field."""
        job_id = "test-job-123"
        mock_data = {
            "status": JobStatus.running,
            "step": "syncing",
        }
        mock_redis.hgetall.return_value = mock_data

        result = get_job(job_id)

        assert result == mock_data
        assert "result" not in result
