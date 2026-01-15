FROM python:3.11-slim

# Install uv
ADD https://astral.sh/uv/install.sh /install_uv.sh
RUN sh /install_uv.sh && rm /install_uv.sh

WORKDIR /app

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock ./

# Install locked dependencies
RUN uv sync --system --no-cache

# Copy application code
COPY src ./src
COPY service_account.json .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
