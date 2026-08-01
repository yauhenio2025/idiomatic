"""Grammar-walks podcast rendering — season 1 delivery as plain MP3s.

Reuses the explainer parser/renderer (same TL:/[PAUSE] conventions,
same content-addressed clip cache, all ffmpeg off the event loop).
Per docs/commissions/unit-specs/PODCASTS_DESIGN.md the episodes ship
as numbered MP3s, NOT cards: a 12-18 minute lesson is not a
spaced-repetition item. Files land in
/data/staged_audio/grammar/podcasts/ and stream through the dashboard
audio route.

Cross-language episodes (lang: x) are skipped until their TL: lines
carry per-line language markers — a single voice would mispronounce
the mixed Romance examples.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import structlog

from ..settings import get_settings
from .explainers import ExplainerScript, _segments, _WORD, render_explainer

log = structlog.get_logger()

SOURCE_DIR = Path(__file__).parent / "data" / "podcasts"


def _lenient_frontmatter(lines: list[str]) -> dict[str, str]:
    """Podcast frontmatter is a superset of the explainer contract
    (series/episode/est_minutes/evidence_refs list) — read only the
    scalar keys we need, ignore the rest."""
    out: dict[str, str] = {}
    for line in lines:
        if ":" in line and not line.startswith((" ", "-", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


def parse_podcast(path: Path) -> tuple[ExplainerScript, int]:
    """Parse a podcast script into an ExplainerScript (for the shared
    renderer) + its episode number."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.name}: frontmatter must start with ---")
    closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    meta = _lenient_frontmatter(lines[1:closing])
    lang = meta.get("lang", "")
    slug = path.stem.split("_", 1)[1] if "_" in path.stem else path.stem
    segments = _segments(lines[closing + 1:], path=path, lang=lang,
                         first_line_no=closing + 2)
    word_count = sum(len(_WORD.findall(s.text)) for s in segments)
    script = ExplainerScript(
        path=path, lang=lang, slug=slug,
        title=meta.get("title", slug), takeaway="",
        fossil_evidence=(),
        est_seconds=int(float(meta.get("est_minutes", "15")) * 60),
        segments=segments, word_count=word_count,
    )
    return script, int(meta.get("episode", "0") or 0)


def podcast_stage_dir() -> Path:
    return Path(get_settings().data_dir) / "staged_audio" / "grammar" / "podcasts"


def episode_filename(episode: int, lang: str, slug: str) -> str:
    return f"ep{episode:02d}_{lang}_{slug}.mp3"


async def build_podcasts() -> dict[str, Any]:
    """Render every single-language episode; idempotent via the clip
    cache (re-runs only re-stitch). Returns build stats."""
    out_dir = podcast_stage_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    built: list[dict[str, Any]] = []
    skipped: list[str] = []
    errors: list[str] = []
    for path in sorted(SOURCE_DIR.glob("*.md")):
        try:
            script, episode = parse_podcast(path)
        except Exception as e:  # noqa: BLE001 — one bad script must not kill the run
            errors.append(f"{path.name}: parse: {repr(e)[:120]}")
            continue
        if script.lang == "x":
            skipped.append(f"{path.name} (cross-language; needs per-line "
                           "TL-xx markers)")
            continue
        try:
            rendered = await render_explainer(script, stage_dir=out_dir)
            final = out_dir / episode_filename(episode, script.lang, script.slug)
            rendered_path = rendered.path
            if rendered_path != final:
                shutil.copyfile(rendered_path, final)
            built.append({"episode": episode, "lang": script.lang,
                          "slug": script.slug, "file": final.name,
                          "minutes": round(rendered.duration_seconds / 60, 1)})
        except Exception as e:  # noqa: BLE001
            errors.append(f"{path.name}: render: {repr(e)[:160]}")
    log.info("podcasts.built", n=len(built), skipped=len(skipped),
             errors=len(errors))
    return {"built": sorted(built, key=lambda b: b["episode"]),
            "skipped": skipped, "errors": errors}


def list_episodes() -> list[dict[str, Any]]:
    out_dir = podcast_stage_dir()
    if not out_dir.exists():
        return []
    return [{"file": p.name, "mb": round(p.stat().st_size / 1e6, 1)}
            for p in sorted(out_dir.glob("ep*.mp3"))]
