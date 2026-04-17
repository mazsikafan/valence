# ── Valence Diagnostics — production image ───────────────────────
# Slim Python base + only what ultralytics/opencv need to run headless.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production

# System deps for OpenCV, ReportLab, and video decoding (ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Application code
COPY app ./app

# Writable runtime dirs (mount persistent volumes at these paths in prod)
RUN mkdir -p /app/uploads /app/results /app/models /app/runs /app/data \
    && useradd --create-home --uid 1000 valence \
    && chown -R valence:valence /app
USER valence

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8765/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765", "--proxy-headers", "--forwarded-allow-ips=*"]
