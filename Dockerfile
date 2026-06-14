# idiomatic worker image — Python + ffmpeg + yt-dlp.
# Kept slim: no Whisper, no GPU. Audio analysis runs through the Gemini
# 3.5 Flash API rather than locally.
FROM python:3.12-slim

# System deps: ffmpeg for audio slicing, ca-certificates + curl + unzip for
# Deno install. Deno is the JS runtime yt-dlp now requires for YouTube
# extraction (since the player-script change in late May 2026).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    unzip \
 && rm -rf /var/lib/apt/lists/*

# Install Deno (single binary)
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
 && /usr/local/bin/deno --version

# yt-dlp via pip is fine; pin a recent-ish version
RUN pip install --no-cache-dir uv yt-dlp

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

COPY . .

# Worker is the default entrypoint; cron overrides via Render config.
CMD ["uv", "run", "python", "-m", "idiomatic.worker"]
