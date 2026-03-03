FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright: install system deps (X11 libs, fonts, etc.)
RUN python -m playwright install-deps chromium

# Download Playwright-compatible Chromium.
# On GitHub Actions: default cdn.playwright.dev works fine.
# On China server: pass --build-arg to use npmmirror CDN.
# Use a fixed path so both root (build) and appuser (runtime) find the browser.
ARG PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=
ENV PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST=${PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST}
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright
RUN python -m playwright install chromium && \
    echo "Playwright Chromium installed successfully"

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
