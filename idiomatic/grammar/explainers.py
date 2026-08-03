"""Authored grammar-radio explainers: source parsing, TTS, and card mapping.

The Markdown files are the source of truth.  Rendered line clips and stitched
lessons are persistent runtime data under ``staged_audio/grammar/<lang>/``;
only a completely rendered lesson is published to its ``grammar_items`` row.

The commission intentionally overrides three values from the earlier design
note: pauses are 1.5 seconds, the takeaway is the card answer, and explainers
are persisted as ``fmt='explainer'`` rows.  The design's content-addressed
audio, frozen-model, and slug-stable identity requirements still apply.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import re
import subprocess
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import structlog

from .. import db, gemini
from ..pipeline.audio import EN_VOICE, LANG_VOICE, concat_mp3s, silence_mp3
from ..settings import get_settings

log = structlog.get_logger()

SOURCE_DIR = Path(__file__).parent / "data" / "explainers"
SUPPORTED_LANGS = frozenset({"fr", "pt", "es", "de"})
EXPECTED_COUNTS = {"fr": 4, "pt": 3, "es": 3, "de": 2}

PAUSE_MS = 1_500
BETWEEN_SPEECH_MS = 200
# v2: per-clip loudness leveling to LEVEL_TARGET_LUFS before stitching.
# The final-file loudnorm in concat_mp3s is GLOBAL — it cannot equalize the
# EN vs target-language voice gap inside one file (user report 2026-08-03:
# French examples much quieter than English narration).
RENDERER_REVISION = "grammar-radio-v2-pause1500-gap200-lvl16"
LEVEL_TARGET_LUFS = -16.0
LEVEL_REVISION = "lvl16v1"


@dataclass(frozen=True)
class ExplainerUnit:
    topic: str
    cluster: str
    label: str = "Grammar radio"
    symbol: str = "🎧"


# Topic keys are deliberately localized, stable ASCII identifiers.  These
# units do not live in curriculum.topics_for(): authored notes must never be
# offered to the generated target-size/top-up loop.
EXPLAINER_UNITS: dict[str, ExplainerUnit] = {
    "fr": ExplainerUnit("fr_ecoute", "0 Écoute"),
    "pt": ExplainerUnit("pt_escuta", "0 Escuta"),
    "es": ExplainerUnit("es_escucha", "0 Escucha"),
    "de": ExplainerUnit("de_hoeren", "0 Hören"),
    # Italian has no authored explainer scripts yet, but the podcast
    # season (grammar/podcasts.py) routes Italian episodes through the
    # same renderer — and future it explainers land here.
    "it": ExplainerUnit("it_ascolto", "0 Ascolto"),
}


@dataclass(frozen=True)
class FossilEvidence:
    ref: str
    count: int | float | str


@dataclass(frozen=True)
class Segment:
    kind: Literal["speech", "pause", "chime", "music", "think"]
    text: str
    lang: str | None
    line_no: int


@dataclass(frozen=True)
class VoiceRoute:
    lang: str
    voice: str


@dataclass(frozen=True)
class ExplainerScript:
    path: Path
    lang: str
    slug: str
    title: str
    takeaway: str
    fossil_evidence: tuple[FossilEvidence, ...]
    est_seconds: int
    segments: tuple[Segment, ...]
    word_count: int


@dataclass(frozen=True)
class RenderedExplainer:
    script: ExplainerScript
    path: Path
    media_filename: str
    duration_seconds: float
    constituent_keys: tuple[str, ...]


class ExplainerSourceError(ValueError):
    """A Markdown source does not satisfy the explainer source contract."""


class ExplainerBuildError(RuntimeError):
    """A lesson could not be rendered completely and must not be published."""


_TOP_LEVEL_FIELD = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$")
_EVIDENCE_ITEM = re.compile(r"^  -\s+([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$")
_EVIDENCE_FIELD = re.compile(r"^    ([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?$")
_CONTROL_PREFIX = re.compile(r"^[A-Z][A-Z0-9_-]{1,15}\s*:")
_TL_LIKE_PREFIX = re.compile(r"(?i)^t(?:arget)?l+\s*:")
_WORD = re.compile(r"[^\W_]+(?:[’'\-][^\W_]+)*", re.UNICODE)


def _scalar(raw: str, *, line_no: int) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in "\"'":
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ExplainerSourceError(
                f"frontmatter line {line_no}: invalid quoted value"
            ) from exc
        if not isinstance(parsed, str):
            raise ExplainerSourceError(
                f"frontmatter line {line_no}: quoted scalar must be text"
            )
        return parsed
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)", value):
        return float(value)
    if value in {"null", "Null", "NULL", "~"}:
        return None
    return value


def _parse_frontmatter(lines: Sequence[str], *, first_line_no: int = 2) -> dict[str, Any]:
    """Parse the deliberately small YAML subset used by canonical sources.

    Keeping the parser local avoids making production depend on an incidental
    transitive PyYAML install.  Scalars plus the list-of-mappings evidence
    shape are the entire source format; malformed indentation fails loudly.
    """
    metadata: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        line_no = first_line_no + i
        if not line.strip():
            i += 1
            continue
        match = _TOP_LEVEL_FIELD.fullmatch(line)
        if not match:
            raise ExplainerSourceError(
                f"frontmatter line {line_no}: unsupported YAML shape"
            )
        key, raw = match.groups()
        if key in metadata:
            raise ExplainerSourceError(f"frontmatter line {line_no}: duplicate {key!r}")
        if key != "fossil_evidence":
            metadata[key] = _scalar(raw or "", line_no=line_no)
            i += 1
            continue
        if (raw or "").strip():
            raise ExplainerSourceError(
                f"frontmatter line {line_no}: fossil_evidence must be a list"
            )

        evidence: list[dict[str, Any]] = []
        i += 1
        current: dict[str, Any] | None = None
        while i < len(lines):
            nested = lines[i]
            nested_no = first_line_no + i
            if not nested.strip():
                i += 1
                continue
            item_match = _EVIDENCE_ITEM.fullmatch(nested)
            field_match = _EVIDENCE_FIELD.fullmatch(nested)
            if item_match:
                if current is not None:
                    evidence.append(current)
                current = {}
                field, item_raw = item_match.groups()
                current[field] = _scalar(item_raw or "", line_no=nested_no)
                i += 1
                continue
            if field_match:
                if current is None:
                    raise ExplainerSourceError(
                        f"frontmatter line {nested_no}: evidence field before list item"
                    )
                field, field_raw = field_match.groups()
                if field in current:
                    raise ExplainerSourceError(
                        f"frontmatter line {nested_no}: duplicate evidence {field!r}"
                    )
                current[field] = _scalar(field_raw or "", line_no=nested_no)
                i += 1
                continue
            if nested.startswith(" "):
                raise ExplainerSourceError(
                    f"frontmatter line {nested_no}: bad evidence indentation"
                )
            break
        if current is not None:
            evidence.append(current)
        metadata[key] = evidence
    return metadata


def _source_error(path: Path, message: str) -> ExplainerSourceError:
    return ExplainerSourceError(f"{path.name}: {message}")


def _segments(body_lines: Sequence[str], *, path: Path, lang: str,
              first_line_no: int) -> tuple[Segment, ...]:
    headings = [i for i, line in enumerate(body_lines) if line.strip() == "## SCRIPT"]
    if len(headings) != 1:
        raise _source_error(path, "expected exactly one ## SCRIPT heading")
    heading = headings[0]
    if any(line.strip() for line in body_lines[:heading]):
        raise _source_error(path, "content before ## SCRIPT is not allowed")

    rendered: list[Segment] = []
    for offset, physical in enumerate(body_lines[heading + 1 :], heading + 1):
        line_no = first_line_no + offset
        line = physical.strip()
        if not line:
            continue
        if line == "[PAUSE]":
            rendered.append(Segment("pause", "", None, line_no))
            continue
        if line.startswith("[PAUSE:") and line.endswith("]"):
            ms_raw = line[len("[PAUSE:"):-1]
            if not ms_raw.isdigit() or not 200 <= int(ms_raw) <= 15000:
                raise _source_error(
                    path, f"line {line_no}: [PAUSE:ms] wants 200-15000, got {ms_raw!r}")
            rendered.append(Segment("pause", ms_raw, None, line_no))
            continue
        if line == "[CHIME]":
            rendered.append(Segment("chime", "", None, line_no))
            continue
        if line.startswith("[MUSIC:") and line.endswith("]"):
            asset = line[len("[MUSIC:"):-1]
            if asset not in ("intro", "outro"):
                raise _source_error(
                    path, f"line {line_no}: [MUSIC:x] wants intro|outro, got {asset!r}")
            rendered.append(Segment("music", asset, None, line_no))
            continue
        if line.startswith("[THINK:") and line.endswith("]"):
            ms_raw = line[len("[THINK:"):-1]
            if not ms_raw.isdigit() or not 2000 <= int(ms_raw) <= 20000:
                raise _source_error(
                    path, f"line {line_no}: [THINK:ms] wants 2000-20000, got {ms_raw!r}")
            rendered.append(Segment("think", ms_raw, None, line_no))
            continue
        if line.startswith("TL:"):
            text = line[3:].strip()
            if not text:
                raise _source_error(path, f"line {line_no}: empty TL segment")
            rendered.append(Segment("speech", text, lang, line_no))
            continue
        if (_CONTROL_PREFIX.match(line) or _TL_LIKE_PREFIX.match(line)
                or line.startswith("[")):
            raise _source_error(
                path, f"line {line_no}: unsupported control prefix in {line!r}"
            )
        rendered.append(Segment("speech", line, "en", line_no))
    if not rendered:
        raise _source_error(path, "script has no rendered segments")
    return tuple(rendered)


def _validate_metadata(path: Path, metadata: Mapping[str, Any]) -> tuple[
    str, str, str, str, tuple[FossilEvidence, ...], int
]:
    required = {"lang", "slug", "title", "takeaway", "fossil_evidence", "est_seconds"}
    missing = sorted(key for key in required if key not in metadata)
    if missing:
        raise _source_error(path, f"missing frontmatter fields: {', '.join(missing)}")

    lang = metadata["lang"]
    slug = metadata["slug"]
    title = metadata["title"]
    takeaway = metadata["takeaway"]
    est_seconds = metadata["est_seconds"]
    if not isinstance(lang, str) or lang not in SUPPORTED_LANGS:
        raise _source_error(path, f"unsupported lang {lang!r}")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise _source_error(path, f"invalid slug {slug!r}")
    if path.name != f"{lang}_{slug}.md":
        raise _source_error(path, f"filename must be {lang}_{slug}.md")
    if not isinstance(title, str) or not title.strip():
        raise _source_error(path, "title must be nonempty text")
    if not isinstance(takeaway, str) or not takeaway.strip() or "\n" in takeaway:
        raise _source_error(path, "takeaway must be one nonempty line")
    if not isinstance(est_seconds, int) or est_seconds <= 0:
        raise _source_error(path, "est_seconds must be a positive integer")

    raw_evidence = metadata["fossil_evidence"]
    if not isinstance(raw_evidence, list) or not raw_evidence:
        raise _source_error(path, "fossil_evidence must be a nonempty list")
    evidence: list[FossilEvidence] = []
    for index, item in enumerate(raw_evidence, 1):
        if not isinstance(item, dict):
            raise _source_error(path, f"evidence item {index} must be a mapping")
        ref = item.get("ref")
        count = item.get("count")
        if not isinstance(ref, str) or not ref.strip():
            raise _source_error(path, f"evidence item {index} has no profile reference")
        if isinstance(count, bool) or not isinstance(count, (int, float, str)):
            raise _source_error(path, f"evidence item {index} has no count/quantity")
        if isinstance(count, str) and (not count.strip() or not re.search(r"\d", count)):
            raise _source_error(path, f"evidence item {index} has no explicit quantity")
        evidence.append(FossilEvidence(ref.strip(), count))
    return lang, slug, title.strip(), takeaway.strip(), tuple(evidence), est_seconds


def parse_explainer(path: Path, *, validate_contract: bool = True) -> ExplainerScript:
    """Parse one YAML-frontmatter Markdown explainer into routed segments."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise _source_error(path, "frontmatter must start with ---")
    try:
        closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise _source_error(path, "frontmatter has no closing ---") from exc

    metadata = _parse_frontmatter(lines[1:closing])
    lang, slug, title, takeaway, evidence, est_seconds = _validate_metadata(path, metadata)
    segments = _segments(
        lines[closing + 1 :], path=path, lang=lang, first_line_no=closing + 2
    )
    word_count = sum(len(_WORD.findall(segment.text)) for segment in segments)

    if validate_contract:
        pauses = [i for i, segment in enumerate(segments) if segment.kind == "pause"]
        if len(pauses) != 3:
            raise _source_error(path, f"expected 3 [PAUSE] lines, found {len(pauses)}")
        for start in pauses:
            following = segments[start + 1 : start + 3]
            direct_answer = bool(
                following
                and following[0].kind == "speech"
                and following[0].lang == lang
            )
            labelled_answer = bool(
                len(following) == 2
                and following[0].kind == "speech"
                and following[0].lang == "en"
                and following[0].text == "Answer:"
                and following[1].kind == "speech"
                and following[1].lang == lang
            )
            if not (direct_answer or labelled_answer):
                raise _source_error(
                    path,
                    "each [PAUSE] must be followed by TL: answer, optionally after Answer:",
                )
        if not 300 <= word_count <= 450:
            raise _source_error(path, f"spoken word count {word_count} is outside 300..450")

    return ExplainerScript(
        path=path,
        lang=lang,
        slug=slug,
        title=title,
        takeaway=takeaway,
        fossil_evidence=evidence,
        est_seconds=est_seconds,
        segments=segments,
        word_count=word_count,
    )


def load_explainers(lang: str | None = None, *, source_dir: Path = SOURCE_DIR,
                    require_expected: bool = True) -> list[ExplainerScript]:
    """Load canonical sources, optionally restricted to one language."""
    if lang is not None and lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be fr|pt|es|de")
    paths = sorted(Path(source_dir).glob(f"{lang}_*.md" if lang else "*.md"))
    scripts = [parse_explainer(path) for path in paths]
    identities = [(script.lang, script.slug) for script in scripts]
    if len(identities) != len(set(identities)):
        raise ExplainerSourceError("duplicate (lang, slug) explainer source")
    if require_expected:
        actual = {
            code: sum(script.lang == code for script in scripts)
            for code in (SUPPORTED_LANGS if lang is None else (lang,))
        }
        expected = {
            code: EXPECTED_COUNTS[code]
            for code in (SUPPORTED_LANGS if lang is None else (lang,))
        }
        if actual != expected:
            raise ExplainerSourceError(
                f"explainer source split is {actual}, expected {expected}"
            )
    return scripts


def route_segment(segment: Segment, target_lang: str) -> VoiceRoute | None:
    """Return the explicit language/voice route for one parsed segment."""
    if target_lang not in EXPLAINER_UNITS:
        raise ValueError("target_lang must be fr|pt|es|de")
    if segment.kind in ("pause", "chime", "music", "think"):
        return None
    if segment.lang == "en":
        return VoiceRoute("en", EN_VOICE)
    if segment.lang != target_lang:
        raise ValueError(
            f"segment language {segment.lang!r} does not match target {target_lang!r}"
        )
    return VoiceRoute(target_lang, LANG_VOICE[target_lang])


def _voice_fingerprint(route: VoiceRoute, settings: Any) -> dict[str, str]:
    """Settings that can change bytes for the same text and routing.

    The fallback is included because an ElevenLabs outage can send the same
    configured request to Gemini.  A later model/voice correction therefore
    cannot accidentally reuse a clip made anywhere in the provider chain.
    """
    use_eleven = (
        getattr(settings, "tts_provider", "gemini") == "elevenlabs"
        and bool(getattr(settings, "elevenlabs_api_key", None))
    )
    if use_eleven:
        primary = "elevenlabs"
        model = str(getattr(settings, "elevenlabs_model", ""))
        voice = gemini.ELEVEN_LANG_VOICE.get(route.lang, "")
    else:
        primary = "gemini"
        model = str(getattr(settings, "gemini_tts_model", ""))
        voice = route.voice
    return {
        "primary": primary,
        "model": model,
        "voice": voice,
        "lang": route.lang,
        "gemini_fallback_model": str(getattr(settings, "gemini_tts_model", "")),
        "gemini_fallback_voice": route.voice,
        "eleven_fallback_model": str(getattr(settings, "elevenlabs_model", "")),
        "eleven_fallback_voice": gemini.ELEVEN_LANG_VOICE.get(route.lang, ""),
    }


def segment_cache_key(script: ExplainerScript, segment: Segment, settings: Any) -> str:
    route = route_segment(segment, script.lang)
    if route is None:
        return f"pause:{PAUSE_MS}"
    payload = {
        "route": _voice_fingerprint(route, settings),
        "text": segment.text,
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return f"{script.slug}_{route.lang}_{digest}"


ASSETS_DIR = Path(__file__).parent / "data" / "audio_assets"


def _think_mp3(work_dir: Path, ms: int) -> Path:
    """Quiet thinking-music of exactly ms, looped from the bed asset
    with gentle fades — fills exercise gaps instead of dead air."""
    out = work_dir / f"think_{ms}_v1.mp3"
    if out.exists() and out.stat().st_size > 500:
        return out
    seconds = ms / 1000
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-stream_loop", "-1", "-i", str(ASSETS_DIR / "thinking_bed.mp3"),
         "-t", f"{seconds:.3f}",
         "-af", (f"afade=t=in:d=0.4,"
                 f"afade=t=out:st={max(seconds - 0.8, 0):.3f}:d=0.8"),
         "-c:a", "libmp3lame", "-q:a", "5", str(out)],
        check=True,
    )
    return out


def _chime_mp3(work_dir: Path) -> Path:
    """A soft two-tone section chime (E5->A5 with decay), generated once
    per work dir — no licensed assets needed. v1: bump the constituent
    key if the recipe changes."""
    out = work_dir / "chime_v1.mp3"
    if out.exists() and out.stat().st_size > 500:
        return out
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", ("aevalsrc=0.28*sin(659.25*2*PI*t)*exp(-3*t)"
                "+0.22*sin(880*2*PI*t)*exp(-2.2*(t-0.25))*gt(t\,0.25)"
                ":d=1.6:s=44100"),
         "-af", "afade=t=out:st=1.2:d=0.4",
         "-c:a", "libmp3lame", "-q:a", "4", str(out)],
        check=True,
    )
    return out


_EBUR_INTEGRATED = re.compile(r"I:\s*(-?[\d.]+)\s*LUFS")
_MEAN_VOLUME = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")


def _measured_loudness(clip: Path) -> float | None:
    """Integrated LUFS via ebur128; volumedetect mean as the short-clip
    fallback (R128 integration is unstable under ~3 s, and many TL clips
    are one word long)."""
    result = subprocess.run(
        ["ffmpeg", "-i", str(clip), "-af", "ebur128=framelog=quiet",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    values = _EBUR_INTEGRATED.findall(result.stderr)
    if values:
        integrated = float(values[-1])
        if -70.0 < integrated < 0.0:
            return integrated
    result = subprocess.run(
        ["ffmpeg", "-i", str(clip), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    values = _MEAN_VOLUME.findall(result.stderr)
    if values:
        # mean_volume tracks speech LUFS within ~2 dB — close enough for
        # inter-voice leveling.
        return float(values[-1])
    return None


def leveled_speech_clip(clip: Path) -> Path:
    """Static-gain level one cached speech clip to LEVEL_TARGET_LUFS.

    Plain volume gain + a safety limiter, deliberately NOT loudnorm: static
    gain preserves the voice's natural dynamics and behaves on one-word
    clips. Output is cached beside the raw clip (idempotent); an
    unmeasurable clip ships unleveled rather than failing the build.
    """
    out = clip.with_name(f"{clip.stem}_{LEVEL_REVISION}.mp3")
    if out.exists() and out.stat().st_size > 0:
        return out
    measured = _measured_loudness(clip)
    if measured is None:
        log.warning("grammar.level.unmeasurable", clip=clip.name)
        return clip
    gain = max(-12.0, min(12.0, LEVEL_TARGET_LUFS - measured))
    temporary = out.with_name(f".{out.stem}.building.mp3")
    temporary.unlink(missing_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip),
             "-af", f"volume={gain:.2f}dB,alimiter=limit=0.97:level=false",
             "-c:a", "libmp3lame", "-q:a", "4", str(temporary)],
            check=True,
        )
        temporary.replace(out)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return out


def _probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


async def render_explainer(
    script: ExplainerScript,
    *,
    stage_dir: Path | None = None,
    settings: Any | None = None,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    silence_fn: Callable[[Path, int], Path] = silence_mp3,
    concat_fn: Callable[[list[Path], Path], Path] = concat_mp3s,
    probe_fn: Callable[[Path], float] = _probe_duration,
    level_fn: Callable[[Path], Path] = leveled_speech_clip,
) -> RenderedExplainer:
    """Render one explainer, reusing unchanged per-line clips.

    Network TTS runs concurrently (bounded inside ``gemini.synthesize``).
    Every local ffmpeg/ffprobe boundary is explicitly moved off the event
    loop; this function is safe to call from the web-process background task.
    Dependencies are injectable so tests need no network or database.
    """
    settings = settings or get_settings()
    if stage_dir is None:
        stage_dir = (
            Path(settings.data_dir) / "staged_audio" / "grammar" / script.lang
            / "explainers"
        )
    stage_dir = Path(stage_dir)
    work_dir = stage_dir / "_work"
    work_dir.mkdir(parents=True, exist_ok=True)
    synthesize_fn = synthesize_fn or gemini.synthesize

    paths_by_index: dict[int, Path] = {}
    keys_by_index: dict[int, str] = {}
    pending: dict[Path, tuple[str, VoiceRoute]] = {}
    for index, segment in enumerate(script.segments):
        if segment.kind in ("pause", "chime", "music", "think"):
            continue
        route = route_segment(segment, script.lang)
        assert route is not None
        key = segment_cache_key(script, segment, settings)
        clip = work_dir / f"{key}.mp3"
        keys_by_index[index] = key
        paths_by_index[index] = clip
        if not (
            clip.exists() and clip.stat().st_size > 0
            and not gemini.silence_marker(clip).exists()
        ):
            # Repeated physical lines (notably "Answer:") intentionally map
            # to one task and one cached clip, while remaining repeated in the
            # later ordered piece list.
            pending[clip] = (segment.text, route)

    async def synthesize_one(path: Path, text: str, route: VoiceRoute) -> None:
        await synthesize_fn(text, voice=route.voice, out=path, lang=route.lang)

    await asyncio.gather(
        *(synthesize_one(path, text, route) for path, (text, route) in pending.items())
    )

    failed = [
        path.name for path in set(paths_by_index.values())
        if not path.exists() or path.stat().st_size <= 0
        or gemini.silence_marker(path).exists()
    ]
    if failed:
        raise ExplainerBuildError(
            f"{script.lang}/{script.slug}: incomplete TTS segments: {', '.join(sorted(failed))}"
        )

    # Level every speech clip to one loudness target before stitching —
    # per-voice output levels differ (EN narrator vs TL voice) and the
    # global loudnorm in concat can't fix imbalance inside the file.
    # Dedupe first: a repeated physical line maps to one cached clip.
    unique_clips = {path: path for path in paths_by_index.values()}
    leveled_list = await asyncio.gather(
        *(asyncio.to_thread(level_fn, path) for path in unique_clips)
    )
    leveled = dict(zip(unique_clips, leveled_list, strict=True))
    paths_by_index = {index: leveled[path]
                      for index, path in paths_by_index.items()}

    pause_lengths = {
        int(segment.text) if segment.text else PAUSE_MS
        for segment in script.segments if segment.kind == "pause"
    }
    needs_gap = any(
        left.kind == right.kind == "speech"
        for left, right in zip(script.segments, script.segments[1:])
    )
    pause_paths = {
        ms: await asyncio.to_thread(silence_fn, work_dir, ms)
        for ms in sorted(pause_lengths)
    }
    gap_path = (
        await asyncio.to_thread(silence_fn, work_dir, BETWEEN_SPEECH_MS)
        if needs_gap else None
    )
    chime_path = (
        await asyncio.to_thread(_chime_mp3, work_dir)
        if any(s.kind == "chime" for s in script.segments) else None
    )
    music_paths = {
        asset: ASSETS_DIR / f"theme_{asset}.mp3"
        for asset in {s.text for s in script.segments if s.kind == "music"}
    }
    for asset, ap in music_paths.items():
        if not ap.exists():
            raise ExplainerBuildError(f"missing music asset {ap.name}")
    think_lengths = {int(s.text) for s in script.segments if s.kind == "think"}
    think_paths = {
        ms: await asyncio.to_thread(_think_mp3, work_dir, ms)
        for ms in sorted(think_lengths)
    }

    pieces: list[Path] = []
    constituent_keys: list[str] = []
    previous: Segment | None = None
    for index, segment in enumerate(script.segments):
        if segment.kind == "pause":
            ms = int(segment.text) if segment.text else PAUSE_MS
            pieces.append(pause_paths[ms])
            constituent_keys.append(f"pause:{ms}")
        elif segment.kind == "chime":
            assert chime_path is not None
            pieces.append(chime_path)
            constituent_keys.append("chime:v1")
        elif segment.kind == "music":
            pieces.append(music_paths[segment.text])
            constituent_keys.append(f"music:{segment.text}:v1")
        elif segment.kind == "think":
            ms = int(segment.text)
            pieces.append(think_paths[ms])
            constituent_keys.append(f"think:{ms}:v1")
        else:
            if previous is not None and previous.kind == "speech":
                assert gap_path is not None
                pieces.append(gap_path)
                constituent_keys.append(f"gap:{BETWEEN_SPEECH_MS}")
            pieces.append(paths_by_index[index])
            constituent_keys.append(keys_by_index[index])
        previous = segment

    final_payload = {
        "renderer": RENDERER_REVISION,
        "lang": script.lang,
        "slug": script.slug,
        "constituents": constituent_keys,
    }
    final_hash = hashlib.sha256(
        json.dumps(final_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    filename = f"idg_explainer_{script.lang}_{script.slug}_{final_hash}.mp3"
    final = stage_dir / filename

    duration: float | None = None
    if final.exists() and final.stat().st_size > 0:
        try:
            duration = await asyncio.to_thread(probe_fn, final)
            if duration <= 0:
                raise ValueError("nonpositive duration")
        except (subprocess.CalledProcessError, ValueError) as exc:
            # A process interruption cannot leave a final file (we publish by
            # atomic replace), but disk damage/manual copies can.  A corrupt
            # content-addressed cache entry must heal instead of poisoning
            # every future rebuild of the slug.
            log.warning(
                "grammar.explainer.cached_audio_invalid",
                lang=script.lang,
                slug=script.slug,
                err=repr(exc)[:200],
            )
            final.unlink(missing_ok=True)
            duration = None
    if duration is None:
        temporary = stage_dir / f".{filename}.building.mp3"
        temporary.unlink(missing_ok=True)
        try:
            await asyncio.to_thread(concat_fn, pieces, temporary)
            duration = await asyncio.to_thread(probe_fn, temporary)
            if duration <= 0:
                raise ExplainerBuildError(
                    f"{script.lang}/{script.slug}: ffprobe returned nonpositive duration"
                )
            temporary.replace(final)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    if duration <= 0:
        raise ExplainerBuildError(
            f"{script.lang}/{script.slug}: cached output has nonpositive duration"
        )
    difference = abs(duration - script.est_seconds)
    if difference > max(60.0, script.est_seconds * 0.5):
        log.warning(
            "grammar.explainer.duration_mismatch",
            lang=script.lang,
            slug=script.slug,
            actual=round(duration, 1),
            estimated=script.est_seconds,
        )
    return RenderedExplainer(
        script=script,
        path=final,
        media_filename=filename,
        duration_seconds=duration,
        constituent_keys=tuple(constituent_keys),
    )


def evidence_summary(evidence: Iterable[FossilEvidence]) -> str:
    parts = [f"{item.count} ({item.ref})" for item in evidence]
    return "Fossil evidence: " + "; ".join(parts)


def explainer_to_item(rendered: RenderedExplainer) -> dict[str, Any]:
    """Map one complete render to raw (not pre-escaped) grammar-item fields."""
    script = rendered.script
    return {
        "lang": script.lang,
        "topic": EXPLAINER_UNITS[script.lang].topic,
        "fmt": "explainer",
        "infinitive": None,
        "mood": None,
        "tense": None,
        "person": None,
        "sentence": script.title,
        "answer": script.takeaway,
        "gloss_en": "",
        "why_en": evidence_summary(script.fossil_evidence),
        "status": "verified",
        "meta": {
            "slug": script.slug,
            "audio_filename": rendered.media_filename,
            "duration_seconds": round(rendered.duration_seconds, 3),
            "renderer_revision": RENDERER_REVISION,
        },
    }


def _metadata(item: Mapping[str, Any]) -> dict[str, Any]:
    value = item.get("meta")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def prebuilt_audio_map(items: Sequence[Mapping[str, Any]], audio_dir: Path) -> dict[int, str]:
    """Map completed explainer rows to media paths relative to audio_dir."""
    result: dict[int, str] = {}
    for item in items:
        if item.get("fmt") != "explainer":
            continue
        metadata = _metadata(item)
        filename = metadata.get("audio_filename")
        slug = metadata.get("slug")
        if not isinstance(filename, str) or Path(filename).name != filename:
            continue
        lang = item.get("lang")
        if not isinstance(lang, str) or not isinstance(slug, str):
            continue
        expected_name = re.compile(
            rf"idg_explainer_{re.escape(lang)}_{re.escape(slug)}_[0-9a-f]{{12}}\.mp3"
        )
        if not expected_name.fullmatch(filename):
            continue
        path = Path(audio_dir) / "explainers" / filename
        if (path.exists() and path.stat().st_size > 0
                and not gemini.silence_marker(path).exists()):
            result[int(item["id"])] = f"explainers/{filename}"
    return result


# F3 rows retain their controlled registry category/unit hint in metadata.
# Where it is covered by a commissioned lesson, give the production card the
# same browsing tag as its explanation.  Avoidance-only de/passiv normally has
# no correction card; its unit-hint entry only covers an explicitly linked one.
_FOSSIL_BY_UNIT_HINT: dict[tuple[str, str], str] = {
    ("fr", "fr_quantites_de"): "beaucoup-de",
    ("fr", "fr_prep_lieux"): "prep-lieux",
    ("fr", "fr_an_annee"): "an-annee",
    ("fr", "fr_ordre_mots"): "ordre-adverbes",
    ("pt", "pt_futuro_subjuntivo"): "futuro-subjuntivo",
    ("pt", "pt_gender_core"): "genero-ma-agem",
    ("pt", "pt_regencia_verbal"): "regencia",
    ("es", "es_interferencia"): "interferencia-pt",
    ("es", "es_light_verbs"): "light-verbs",
    ("es", "es_muy_mucho"): "muy-mucho",
    ("de", "de_adj_endings"): "adjektivendungen",
    ("de", "de_passiv"): "passiv",
}

_FOSSIL_BY_CATEGORY: dict[tuple[str, str], str] = {
    # Controlled personal_errors categories.
    ("fr", "article_quantifier"): "beaucoup-de",
    ("fr", "preposition_selection"): "prep-lieux",
    ("fr", "word_order"): "ordre-adverbes",
    ("fr", "negation"): "ordre-adverbes",
    ("pt", "subjunctive"): "futuro-subjuntivo",
    ("pt", "gender"): "genero-ma-agem",
    ("pt", "verb_prep_regime"): "regencia",
    ("es", "interference_lexical"): "interferencia-pt",
    ("es", "interference_morphological"): "interferencia-pt",
    ("es", "light_verb_collocation"): "light-verbs",
    ("de", "adjective_ending"): "adjektivendungen",
    # Legacy/profile labels retained for old fixtures and imported rows.
    ("fr", "quantifier_de"): "beaucoup-de",
    ("fr", "prep_place"): "prep-lieux",
    ("fr", "an_vs_annee"): "an-annee",
    ("fr", "adverb_placement"): "ordre-adverbes",
    ("pt", "fut_subjunctive"): "futuro-subjuntivo",
    ("es", "interference"): "interferencia-pt",
    ("es", "light_verb"): "light-verbs",
    ("es", "muy_mucho"): "muy-mucho",
    ("de", "adj_endings"): "adjektivendungen",
    ("de", "gender+adj_endings"): "adjektivendungen",
    ("de", "adj_morphology"): "adjektivendungen",
}


def fossil_tags_for_item(item: Mapping[str, Any]) -> tuple[str, ...]:
    if item.get("fmt") != "f3":
        return ()
    lang = str(item.get("lang") or "")
    metadata = _metadata(item)
    unit_hint = str(metadata.get("source_unit_hint") or "")
    category = str(
        metadata.get("source_category") or item.get("gloss_en") or ""
    )
    slug = (
        _FOSSIL_BY_UNIT_HINT.get((lang, unit_hint))
        or _FOSSIL_BY_CATEGORY.get((lang, category))
    )
    if not slug:
        return ()
    return (f"idiomatic-fossil::{item['lang']}::{slug}",)


async def build_language(
    lang: str,
    *,
    source_dir: Path = SOURCE_DIR,
    stage_dir: Path | None = None,
    settings: Any | None = None,
    synthesize_fn: Callable[..., Awaitable[None]] | None = None,
    upsert_fn: Callable[..., Awaitable[int]] | None = None,
    silence_fn: Callable[[Path, int], Path] = silence_mp3,
    concat_fn: Callable[[list[Path], Path], Path] = concat_mp3s,
    probe_fn: Callable[[Path], float] = _probe_duration,
) -> dict[str, Any]:
    """Render and upsert every canonical explainer for one language.

    Scripts are handled independently: a degraded TTS segment leaves that
    slug's previous complete row/media untouched while the other lessons can
    still publish.  Deck rebuilding is intentionally not part of this call.
    """
    if lang not in SUPPORTED_LANGS:
        raise ValueError("lang must be fr|pt|es|de")
    settings = settings or get_settings()
    scripts = load_explainers(lang, source_dir=source_dir)
    if stage_dir is None:
        stage_dir = (
            Path(settings.data_dir) / "staged_audio" / "grammar" / lang / "explainers"
        )
    upsert_fn = upsert_fn or db.upsert_explainer_item
    batch = f"explainer-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    built: list[dict[str, Any]] = []
    errors: list[str] = []

    for script in scripts:
        try:
            rendered = await render_explainer(
                script,
                stage_dir=stage_dir,
                settings=settings,
                synthesize_fn=synthesize_fn,
                silence_fn=silence_fn,
                concat_fn=concat_fn,
                probe_fn=probe_fn,
            )
            item = explainer_to_item(rendered)
            item_id = await upsert_fn(item, batch=batch)
            built.append(
                {
                    "slug": script.slug,
                    "item_id": item_id,
                    "media": rendered.media_filename,
                    "duration_seconds": round(rendered.duration_seconds, 1),
                }
            )
        except Exception as exc:  # noqa: BLE001 - one source must not hide the others
            log.exception("grammar.explainer.failed", lang=lang, slug=script.slug)
            errors.append(f"{script.slug}: {exc}")

    result = {
        "lang": lang,
        "scripts": len(scripts),
        "built": built,
        "built_count": len(built),
        "failed": errors,
    }
    log.info("grammar.explainers.done", **result)
    return result
