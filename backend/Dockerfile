FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright: install only system deps for Chromium (no browser binary download).
# The browser binary (~400MB) is installed at deploy time into a mounted volume
# to keep the Docker image small and avoid slow GHCR pulls.
RUN playwright install-deps chromium

# Application code
COPY . .

# Non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
