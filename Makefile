.PHONY: help install install-dev run test test-cov lint format check clean docker-build docker-run docker-stop docker-logs sync

# Default target
help:
	@echo "Google Merchant Feed Service - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev     Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run             Run the service"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-cov        Run tests with coverage report"
	@echo "  make test-watch      Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            Run linter (ruff check)"
	@echo "  make format          Format code (ruff format)"
	@echo "  make check           Run both lint and format checks"
	@echo "  make fix             Auto-fix linting issues"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    Build Docker image"
	@echo "  make docker-run      Run Docker container"
	@echo "  make docker-stop     Stop Docker container"
	@echo "  make docker-logs     View Docker container logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make sync            Trigger manual product sync (requires running service)"
	@echo "  make clean           Clean cache and temporary files"
	@echo ""

# Installation
install:
	uv sync

install-dev:
	uv sync --extra dev

# Development
run:
	uv run uvicorn src.main:app --reload

# Testing
test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ --cov=src --cov-report=html --cov-report=term

test-watch:
	uv run pytest-watch tests/

# Code Quality
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

check: lint format
	@echo "✓ Linting and formatting checks complete"

fix:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

# Docker
docker-build:
	docker build -t google-merchant-feed-service:latest .

docker-run:
	docker run -d \
		--name merchant-feed-service \
		-p 8000:8000 \
		--env-file .env \
		google-merchant-feed-service:latest

docker-stop:
	docker stop merchant-feed-service || true
	docker rm merchant-feed-service || true

docker-logs:
	docker logs -f merchant-feed-service

# Utilities
sync:
	@echo "Triggering manual sync..."
	@curl -X POST http://localhost:8000/sync || echo "Error: Service may not be running"

clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .ruff_cache 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	@echo "✓ Cleaned cache and temporary files"
