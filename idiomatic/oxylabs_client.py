"""Oxylabs YouTube Downloader + Cloudflare R2 pickup.

Flow:
  1. submit_audio_job(video_id) → POST to data.oxylabs.io, returns job_id
  2. wait_for_done(job_id)      → polls status endpoint until done|faulted
  3. download_audio(video_id, job_id, dst) → boto3 get_object from R2

Replaces the yt-dlp path. Oxylabs handles the bot wall on their side; we
just pay per video. R2 is the cheapest S3-compatible bucket (no egress).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import quote, urlparse

import boto3
import httpx
import structlog
from botocore.config import Config
from tenacity import (
    retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter,
)

from .settings import get_settings

log = structlog.get_logger()

_OXY_BASE = "https://data.oxylabs.io/v1/queries"


class OxylabsTransient(Exception):
    """5xx / 429 / connection — tenacity retries."""


class OxylabsFatal(Exception):
    """4xx (other than 429), or terminal job state."""


class OxylabsPermanentVideoFailure(OxylabsFatal):
    """Oxylabs succeeded at the API layer but the specific video can't be
    downloaded (age/region/copyright restrictions, deleted, etc.). Distinct
    from OxylabsFatal so the worker can mark the video 'skipped' rather
    than 'failed' — retries would just re-hit the same wall."""


# ---- one R2 client per process ---------------------------------------------

_r2_client = None


def _r2():
    global _r2_client
    if _r2_client is not None:
        return _r2_client
    s = get_settings()
    if not (s.r2_access_key_id and s.r2_secret_access_key and s.r2_endpoint):
        raise RuntimeError("R2 credentials not configured (R2_ACCESS_KEY_ID/SECRET/ENDPOINT)")
    _r2_client = boto3.client(
        "s3",
        endpoint_url=s.r2_endpoint,
        aws_access_key_id=s.r2_access_key_id,
        aws_secret_access_key=s.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )
    return _r2_client


# ---- submit ----------------------------------------------------------------

def _r2_storage_url(prefix: str) -> str:
    """Oxylabs s3_compatible storage_url format:
        https://ACCESS_KEY:SECRET@<endpoint-host>/<bucket>/<prefix>/
    Credentials live inline; no separate fields.
    """
    s = get_settings()
    host = urlparse(s.r2_endpoint).netloc
    user = quote(s.r2_access_key_id, safe="")
    pwd = quote(s.r2_secret_access_key, safe="")
    return f"https://{user}:{pwd}@{host}/{s.r2_bucket}/{prefix.rstrip('/')}/"


@retry(
    retry=retry_if_exception_type(OxylabsTransient),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=2, max=20),
    reraise=True,
)
async def submit_audio_job(video_id: str) -> str:
    """POST to Oxylabs, return job_id. They'll push the .m4a to R2 under
    `oxylabs-pushes/<video_id>/`."""
    s = get_settings()
    if not (s.oxylabs_user and s.oxylabs_pass):
        raise RuntimeError("OXYLABS_USER / OXYLABS_PASS not set")

    prefix = f"oxylabs-pushes/{video_id}"
    payload = {
        "source": "youtube_download",
        "query": video_id,
        "context": [{"key": "download_type", "value": "audio"}],
        "storage_type": "s3_compatible",
        "storage_url": _r2_storage_url(prefix),
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(_OXY_BASE,
                              auth=(s.oxylabs_user, s.oxylabs_pass),
                              json=payload)

    if r.status_code in (429, 500, 502, 503, 504):
        raise OxylabsTransient(f"HTTP {r.status_code}: {r.text[:200]}")
    if r.status_code >= 400:
        raise OxylabsFatal(f"HTTP {r.status_code}: {r.text[:300]}")

    body = r.json()
    job_id = body.get("id")
    if not job_id:
        raise OxylabsFatal(f"no job id in response: {str(body)[:300]}")
    log.info("oxylabs.submitted", video_id=video_id, job_id=job_id)
    return str(job_id)


# ---- poll ------------------------------------------------------------------

async def wait_for_done(job_id: str) -> dict:
    """Poll until status is `done`; returns the final job-status JSON (it
    carries a duration_sec field the worker uses for the length window).
    Raises OxylabsFatal on `faulted` or timeout."""
    s = get_settings()
    url = f"{_OXY_BASE}/{job_id}"
    deadline = asyncio.get_event_loop().time() + s.oxylabs_max_wait_sec
    last = None
    while asyncio.get_event_loop().time() < deadline:
        # One flaky poll must not kill a job we've already paid for —
        # 429/5xx/network blips just mean "ask again next tick"; only a
        # definitive 4xx (job unknown/expired) is fatal.
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(url, auth=(s.oxylabs_user, s.oxylabs_pass))
        except httpx.HTTPError as e:
            log.warning("oxylabs.poll_transient", job_id=job_id,
                         err=f"{type(e).__name__}: {str(e)[:120]}")
            await asyncio.sleep(s.oxylabs_poll_interval_sec)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            log.warning("oxylabs.poll_transient", job_id=job_id,
                         err=f"HTTP {r.status_code}")
            await asyncio.sleep(s.oxylabs_poll_interval_sec)
            continue
        if r.status_code >= 400:
            raise OxylabsFatal(f"poll HTTP {r.status_code}: {r.text[:200]}")
        body = r.json()
        status = body.get("status")
        if status != last:
            log.info("oxylabs.status", job_id=job_id, status=status)
            last = status
        if status == "done":
            # Oxylabs marks a job "done" even when their downloader hit an
            # internal error for THIS specific video — the storage_url
            # comes back with an unresolved {{ extension }} placeholder and
            # the results endpoint reports a non-success status_code (e.g.
            # 11205). Nothing lands in R2. Detect this now and surface as
            # a permanent per-video failure so the worker skips it (not
            # retriable — resubmitting reproduces the same error, verified
            # empirically on Opera Mundi videos).
            storage_url = body.get("storage_url") or ""
            if "{{ extension }}" in storage_url or "%7B%7B" in storage_url:
                # Fetch the per-page results to include the exact
                # status_code in the error for observability.
                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        rr = await client.get(
                            f"{url}/results",
                            auth=(s.oxylabs_user, s.oxylabs_pass),
                        )
                    codes = [r.get("status_code") for r in
                              (rr.json().get("results") or [])
                              if isinstance(r, dict)]
                except Exception:
                    codes = []
                raise OxylabsPermanentVideoFailure(
                    f"job {job_id}: oxylabs couldn't download this video "
                    f"(unresolved storage_url; result codes={codes})"
                )
            return body
        if status == "faulted":
            raise OxylabsFatal(f"job {job_id} faulted: {r.text[:300]}")
        await asyncio.sleep(s.oxylabs_poll_interval_sec)
    raise OxylabsFatal(f"job {job_id} timeout after {s.oxylabs_max_wait_sec}s")


def duration_from_status(body: dict) -> int | None:
    """Pull duration_sec out of a job-status response, wherever it sits
    (top level or inside the context key/value list)."""
    dur = body.get("duration_sec")
    if dur is None:
        for kv in body.get("context") or []:
            if isinstance(kv, dict) and kv.get("key") == "duration_sec":
                dur = kv.get("value")
                break
    try:
        return int(float(dur)) if dur is not None else None
    except (TypeError, ValueError):
        return None


# ---- pickup ----------------------------------------------------------------

def _list_prefix(prefix: str) -> list[dict]:
    """[{'Key': ..., 'Size': ...}, ...] under the prefix."""
    s = get_settings()
    resp = _r2().list_objects_v2(Bucket=s.r2_bucket, Prefix=prefix)
    return [{"Key": o["Key"], "Size": o.get("Size", 0)}
            for o in resp.get("Contents", [])]


async def download_audio(video_id: str, job_id: str, dst_dir: Path) -> Path:
    """Pull the audio file Oxylabs pushed into R2. The extension Oxylabs picks
    varies (.aac, .m4a, …) so we list the prefix instead of guessing. Writes
    to `dst_dir/source.<ext>` preserving the original suffix (Gemini and
    ffmpeg both accept whatever Oxylabs returns)."""
    prefix = f"oxylabs-pushes/{video_id}/"
    objs = await asyncio.to_thread(_list_prefix, prefix)
    audio_objs = [o for o in objs if not o["Key"].endswith("/")]
    if not audio_objs:
        raise OxylabsFatal(f"no object under R2 prefix {prefix!r} after job {job_id}")
    # Pick the largest (in case the prefix has stragglers — metadata
    # sidecars, partial retries). Actually by Size this time.
    key = max(audio_objs, key=lambda o: o["Size"])["Key"]
    ext = Path(key).suffix or ".m4a"
    dst = dst_dir / f"source{ext}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    s = get_settings()

    def _get():
        obj = _r2().get_object(Bucket=s.r2_bucket, Key=key)
        with dst.open("wb") as f:
            for chunk in iter(lambda: obj["Body"].read(1 << 20), b""):
                f.write(chunk)

    await asyncio.to_thread(_get)
    log.info("oxylabs.downloaded", video_id=video_id, key=key,
             bytes=dst.stat().st_size)
    return dst


async def fetch_audio(video_id: str, dst_dir: Path) -> tuple[Path, int | None]:
    """R2-reuse-aware fetch. cleanup_r2 is deferred until a video is done,
    so a retry (or backfill) whose local work dir was wiped finds the
    previous job's object still in the bucket and downloads it directly —
    no second Oxylabs job paid for. Returns (path, duration_sec | None);
    duration is only known when a fresh job ran."""
    prefix = f"oxylabs-pushes/{video_id}/"
    objs = await asyncio.to_thread(_list_prefix, prefix)
    if any(not o["Key"].endswith("/") and o["Size"] > 0 for o in objs):
        log.info("oxylabs.r2_reuse", video_id=video_id)
        out = await download_audio(video_id, "r2-reuse", dst_dir)
        return out, None
    job_id = await submit_audio_job(video_id)
    status_body = await wait_for_done(job_id)
    out = await download_audio(video_id, job_id, dst_dir)
    return out, duration_from_status(status_body)


async def cleanup_r2(video_id: str) -> None:
    """Best-effort wipe of all objects under the per-video R2 prefix."""
    s = get_settings()
    prefix = f"oxylabs-pushes/{video_id}/"
    try:
        objs = await asyncio.to_thread(_list_prefix, prefix)
        for obj in objs:
            await asyncio.to_thread(
                _r2().delete_object, Bucket=s.r2_bucket, Key=obj["Key"],
            )
    except Exception as e:
        log.warning("oxylabs.cleanup_failed", prefix=prefix, err=str(e)[:200])
