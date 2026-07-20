# idiomatic image — Python + ffmpeg + the built dashboard SPA.
# Audio fetching is delegated to the Oxylabs YouTube Downloader API; the
# image no longer needs yt-dlp or a JS runtime (Deno) for bot-wall evasion.

# --- stage 1: build the dashboard -----------------------------------------
FROM node:22-slim AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- stage 2: the python service ------------------------------------------
FROM python:3.12-slim

# Only ffmpeg (for TTS concat + slicing the Oxylabs-supplied .m4a) and
# ca-certificates for outbound HTTPS.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

COPY . .
# The SPA the API serves at / (api.py looks for frontend/dist).
COPY --from=frontend /fe/dist ./frontend/dist

# Worker is the default entrypoint; cron overrides via Render config.
CMD ["uv", "run", "python", "-m", "idiomatic.worker"]
