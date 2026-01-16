# Google Merchant Feed Service

A production-ready microservice for synchronizing product data from PostgreSQL to Google Sheets in a Google Merchant Center-compliant format. Built with FastAPI, designed for reliability, scalability, and maintainability.

## Overview

This service acts as a dedicated integration layer between your e-commerce database and Google Merchant Center, ensuring product feeds remain synchronized without coupling your core application logic to external integrations. The service implements idempotent operations, distributed locking, and comprehensive job tracking to ensure data consistency and operational visibility.

### Architecture

```
┌─────────────┐      ┌──────────────────────┐      ┌──────────────┐      ┌──────────────────┐
│ PostgreSQL  │─────▶│  Feed Sync Service   │─────▶│ Google Sheets│─────▶│ Google Merchant  │
│  Database   │      │   (This Service)     │      │              │      │     Center       │
└─────────────┘      └──────────────────────┘      └──────────────┘      └──────────────────┘
                            │
                            ▼
                      ┌──────────┐
                      │  Redis   │
                      │ (Locks & │
                      │  Jobs)   │
                      └──────────┘
```

**Design Principles:**
- **Decoupled Integration**: Standalone service that can be deployed and scaled independently
- **Idempotent Operations**: Safe to re-run without data duplication
- **Distributed Locking**: Prevents concurrent sync operations using Redis
- **Job Tracking**: Full visibility into sync operations with status tracking
- **Scheduled Syncs**: Automatic periodic synchronization via APScheduler

## Features

### Core Capabilities

- **PostgreSQL → Google Sheets Synchronization**: Efficiently syncs product data with minimal API calls
- **Google Merchant Compliance**: Automatically formats data according to Google Merchant Center specifications
- **Idempotent Updates**: Smart diff-based updates that only modify changed rows
- **Automatic Cleanup**: Removes inactive products from the feed automatically
- **Inventory-Aware Availability**: Handles product availability based on inventory status
- **Service Account Authentication**: Secure, token-free authentication using Google Service Accounts
- **Distributed Locking**: Redis-based locking prevents race conditions in distributed deployments
- **Job Status Tracking**: Real-time visibility into sync job execution and results

### Operational Features

- **RESTful API**: Clean HTTP endpoints for manual triggers and status checks
- **Background Processing**: Non-blocking sync operations with job tracking
- **Health Checks**: Built-in health endpoint for monitoring and load balancers
- **Error Handling**: Comprehensive error handling with detailed job status reporting
- **Scheduled Syncs**: Configurable automatic synchronization (default: every 5 hours)

## Prerequisites

- **Python 3.11+**
- **PostgreSQL** database with product data
- **Redis** instance for distributed locking and job tracking
- **Google Cloud Project** with:
  - Service Account with Google Sheets API enabled
  - Service Account JSON key file
  - Google Sheets spreadsheet created and shared with service account email
- **Docker** (optional, for containerized deployment)

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd google-merchant-feed-service
   ```

2. **Install dependencies using uv**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install project dependencies
   uv sync
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   REDIS_URL=redis://localhost:6379/0
   SPREADSHEET_ID=your_google_sheet_id
   SHEET_NAME=Sheet1
   GOOGLE_SERVICE_ACCOUNT_B64=<base64_encoded_service_account_json>
   ```

4. **Prepare Google Service Account**
   ```bash
   # Encode your service account JSON file
   cat service_account.json | base64 > service_account_b64.txt
   # Copy the contents to GOOGLE_SERVICE_ACCOUNT_B64 in .env
   ```

5. **Run the service**
   ```bash
   uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t google-merchant-feed-service .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name merchant-feed-service \
     -p 8000:8000 \
     -e DATABASE_URL=postgresql://... \
     -e REDIS_URL=redis://... \
     -e SPREADSHEET_ID=... \
     -e SHEET_NAME=Sheet1 \
     -e GOOGLE_SERVICE_ACCOUNT_B64=... \
     google-merchant-feed-service
   ```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `REDIS_URL` | Redis connection URL | Yes | - |
| `SPREADSHEET_ID` | Google Sheets spreadsheet ID | Yes | - |
| `SHEET_NAME` | Name of the worksheet to sync | No | `Sheet1` |
| `GOOGLE_SERVICE_ACCOUNT_B64` | Base64-encoded service account JSON | Yes | - |

### Database Schema Requirements

The service expects the following PostgreSQL schema:

```sql
-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    is_new BOOLEAN DEFAULT FALSE
);

-- Product variants table
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    price DECIMAL(10, 2),
    old_price DECIMAL(10, 2),
    color VARCHAR,
    size VARCHAR,
    age VARCHAR
);

-- Product images table
CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    image VARCHAR NOT NULL,
    "order" INTEGER DEFAULT 0
);
```

### Google Sheets Setup

1. Create a new Google Sheets spreadsheet
2. Create a service account in Google Cloud Console
3. Enable Google Sheets API for your project
4. Download the service account JSON key
5. Share the spreadsheet with the service account email (found in the JSON file)
6. Ensure the first row contains the required headers (see `EXPECTED_HEADERS` in `src/sync.py`)

## API Reference

### Endpoints

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

#### `POST /sync`
Trigger a manual product synchronization job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started"
}
```

#### `GET /sync/{job_id}`
Get the status of a synchronization job.

**Response (Success):**
```json
{
  "status": "success",
  "created_at": "1704067200.0",
  "started_at": "1704067201.0",
  "finished_at": "1704067205.0",
  "step": "completed",
  "result": {
    "inserted": 10,
    "updated": 5,
    "deleted": 2
  }
}
```

**Response (Running):**
```json
{
  "status": "running",
  "created_at": "1704067200.0",
  "started_at": "1704067201.0",
  "step": "syncing products"
}
```

**Response (Failed):**
```json
{
  "status": "failed",
  "created_at": "1704067200.0",
  "started_at": "1704067201.0",
  "finished_at": "1704067202.0",
  "error": "Connection timeout"
}
```

## Architecture Details

### Synchronization Flow

1. **Lock Acquisition**: Attempts to acquire a distributed lock via Redis (5-minute TTL)
2. **Data Fetching**: Retrieves active products from PostgreSQL with variants and images
3. **Data Mapping**: Transforms database records to Google Merchant-compliant format
4. **Diff Calculation**: Compares existing sheet data with fetched products
5. **Batch Operations**:
   - Inserts new products
   - Updates modified products
   - Deletes inactive products
6. **Lock Release**: Releases the distributed lock

### Job Tracking

Jobs are stored in Redis with the following structure:
- Key: `sync:job:{job_id}`
- TTL: 6 hours
- Fields: `status`, `created_at`, `started_at`, `finished_at`, `step`, `result`, `error`

### Scheduled Syncs

The service automatically runs synchronization every 5 hours using APScheduler. The scheduler starts when the application starts and runs in the background.

## Development

### Project Structure

```
google-merchant-feed-service/
├── src/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── sync.py          # Core synchronization logic
│   ├── db.py            # PostgreSQL database operations
│   ├── sheets.py        # Google Sheets API integration
│   ├── scheduler.py     # Background job scheduler
│   ├── locks.py         # Redis-based locking and job tracking
│   └── jobs.py          # Job status definitions
├── tests/
│   ├── test_sync.py
│   └── test_mapping.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

The project uses `ruff` for linting and formatting:

```bash
# Check code style
uv run ruff check src/

# Format code
uv run ruff format src/
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
uv run pre-commit install
```

## Monitoring and Observability

### Health Checks

Monitor the service health using the `/` endpoint. Integrate with your monitoring solution:

```bash
curl http://localhost:8000/
```

### Job Status Monitoring

Track sync jobs by polling the `/sync/{job_id}` endpoint. Consider implementing:
- Alerting on failed jobs
- Metrics collection for sync duration and volume
- Dashboard visualization of sync statistics

### Logging

The service logs important events. Configure your logging infrastructure to capture:
- Job start/completion events
- Error messages and stack traces
- Lock acquisition/release events

## Troubleshooting

### Common Issues

**Issue: "Job not found"**
- Jobs expire after 6 hours. Check that you're using the correct job ID and that the job was created recently.

**Issue: "Locked" status**
- Another sync operation is in progress. Wait for it to complete or check for stale locks in Redis.

**Issue: Google Sheets API errors**
- Verify service account has access to the spreadsheet
- Check that Google Sheets API is enabled in your Google Cloud project
- Ensure `GOOGLE_SERVICE_ACCOUNT_B64` is correctly base64-encoded

**Issue: Database connection errors**
- Verify `DATABASE_URL` is correct and accessible
- Check network connectivity and firewall rules
- Ensure database user has necessary permissions

**Issue: Redis connection errors**
- Verify `REDIS_URL` is correct
- Check Redis server is running and accessible
- Ensure network connectivity

## Performance Considerations

- **Batch Operations**: The service uses batch inserts/updates to minimize API calls
- **Connection Pooling**: Database connections are managed efficiently
- **Lock TTL**: 5-minute lock timeout prevents indefinite blocking
- **Job Cleanup**: Jobs automatically expire after 6 hours to prevent Redis memory bloat

## Security

- **Service Account Authentication**: Uses Google Service Accounts (no user credentials)
- **Environment Variables**: Sensitive data stored in environment variables, not code
- **Base64 Encoding**: Service account keys are base64-encoded for easier deployment
- **Connection Strings**: Use secure connection strings with proper authentication

## License

MIT
