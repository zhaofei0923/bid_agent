FROM python:3.12-slim

WORKDIR /app

# Use Tencent Cloud mirrors for both apt and pip (faster in China)
RUN sed -i 's|deb.debian.org|mirrors.tencent.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.tencent.com|g' /etc/apt/sources.list || true

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies (use Tencent Cloud mirror for speed in China)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i https://mirrors.tencent.com/pypi/simple/ \
    --trusted-host mirrors.tencent.com \
    -r requirements.txt

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
