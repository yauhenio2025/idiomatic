# idiomatic worker image — Python + ffmpeg.
# Audio fetching is delegated to the Oxylabs YouTube Downloader API; the
# image no longer needs yt-dlp or a JS runtime (Deno) for bot-wall evasion.
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

# Worker is the default entrypoint; cron overrides via Render config.
CMD ["uv", "run", "python", "-m", "idiomatic.worker"]
