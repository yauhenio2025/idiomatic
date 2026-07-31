"""Teacher-attested personal errors converted into F3 grammar cards.

F3 is deliberately a small, deterministic pipeline: candidate filtering,
ranking, and field mapping are pure functions, while the database operations
are thin wrappers.  No generated text and no network verification are
involved; every source pair has already been attested by a teacher.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from typing import Any

import structlog

from .. import db

log = structlog.get_logger()


TOPIC_BY_LANG = {
    "fr": "fr_mes_erreurs",
    "pt": "pt_meus_erros",
    "es": "es_mis_errores",
    "it": "it_miei_errori",
    "de": "de_meine_fehler",
}

_FORBIDDEN_BRACKETS = "[]{}<>"
_SHORT_ANNOTATION = re.compile(r"\(\s*(?:\?|[^\W\d_]{1,3})\s*\)", re.UNICODE)


def _text(value: Any) -> str:
    """Trim source whitespace without changing spelling, case, or accents."""
    return " ".join(value.strip().split()) if isinstance(value, str) else ""


def _balanced_parentheses(value: str) -> bool:
    depth = 0
    for char in value:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _has_usable_text(value: str) -> bool:
    """Reject extraction markup while retaining genuine one-word errors."""
    if not value or not any(char.isalnum() for char in value):
        return False
    if any(char in value for char in _FORBIDDEN_BRACKETS):
        return False
    if "___" in value or value.startswith("#"):
        return False
    if any(marker in value for marker in ("->", "=>", "→")):
        return False
    if any(unicodedata.category(char) == "Cc" for char in value):
        return False
    if not _balanced_parentheses(value) or _SHORT_ANNOTATION.search(value):
        return False
    return True


def is_suitable_pair(wrong: Any, right: Any) -> bool:
    """Whether an attested pair can stand alone as an F3 challenge.

    A single word is intentionally sufficient: derivations, false friends,
    spelling errors, and closed-class substitutions are all useful cards.
    Only empty/equal pairs and obvious extraction/annotation fragments are
    discarded.
    """
    wrong_text = _text(wrong)
    right_text = _text(right)
    if not (_has_usable_text(wrong_text) and _has_usable_text(right_text)):
        return False
    return unicodedata.normalize("NFC", wrong_text) != unicodedata.normalize(
        "NFC", right_text
    )


def _last_seen_key(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value or "")


def _occurrences(row: Mapping[str, Any]) -> int:
    value = row.get("occurrences", 1)
    return value if isinstance(value, int) and value > 0 else 1


def _eligible(row: Mapping[str, Any]) -> bool:
    return (
        row.get("kind") == "error"
        and row.get("status") == "active"
        and row.get("confidence") == "high"
        and row.get("f3_item_id") is None
        and is_suitable_pair(row.get("wrong"), row.get("right_form"))
    )


def choose_candidates(rows: Sequence[Mapping[str, Any]], n: int) -> list[dict[str, Any]]:
    """Filter and rank source rows, then choose at most ``n``.

    Ranking mirrors the database contract: recurrence count first, recency
    second, and source id as a deterministic final tie-break.  Duplicate
    wrong phrases are collapsed because ``grammar_items`` is unique on
    ``(lang, sentence)`` even when the registry contains several proposed
    corrections for the same attested wording.
    """
    if n <= 0:
        return []
    eligible = [dict(row) for row in rows if _eligible(row)]
    eligible.sort(
        key=lambda row: (
            _occurrences(row),
            _last_seen_key(row.get("last_seen")),
            -int(row.get("id") or 0),
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    seen_wrong: set[tuple[str, str]] = set()
    for row in eligible:
        key = (
            str(row.get("lang") or ""),
            unicodedata.normalize("NFC", _text(row.get("wrong"))).casefold(),
        )
        if key in seen_wrong:
            continue
        seen_wrong.add(key)
        selected.append(row)
        if len(selected) == n:
            break
    return selected


def candidate_to_item(row: Mapping[str, Any]) -> dict[str, Any]:
    """Map one registry row into the frozen grammar-item field vocabulary."""
    lang = str(row.get("lang") or "")
    try:
        topic = TOPIC_BY_LANG[lang]
    except KeyError as exc:
        raise ValueError(f"unsupported F3 language: {lang!r}") from exc
    wrong = _text(row.get("wrong"))
    right = _text(row.get("right_form"))
    if not is_suitable_pair(wrong, right):
        raise ValueError("unsuitable F3 error pair")
    return {
        "lang": lang,
        "topic": topic,
        "fmt": "f3",
        "infinitive": None,
        "mood": None,
        "tense": None,
        "person": None,
        "sentence": wrong,
        "answer": right,
        "gloss_en": _text(row.get("gloss_en")) or _text(row.get("category")),
        "why_en": _text(row.get("why")),
        "status": "verified",
        # Presentation glosses are optional/free text, so they are not a
        # reliable classifier for pairing an F3 card with an explainer.
        # Preserve the registry's controlled fields behind the frozen model.
        "meta": {
            "source_category": _text(row.get("category")),
            "source_subcategory": _text(row.get("subcategory")),
            "source_unit_hint": _text(row.get("unit_hint")),
        },
    }


async def _select_candidate_batch(
    lang: str, n: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return insertable candidates plus ranked sentence collisions seen."""
    if lang not in TOPIC_BY_LANG:
        raise ValueError(f"unsupported F3 language: {lang!r}")
    if n <= 0:
        return [], []
    rows = await db.fetch_f3_candidates(lang)
    ranked = choose_candidates(rows, len(rows))
    candidates: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []
    for row in ranked:
        if row.get("sentence_collision"):
            collisions.append(row)
            continue
        candidates.append(row)
        if len(candidates) == n:
            break
    return candidates, collisions


async def select_candidates(lang: str, n: int) -> list[dict[str, Any]]:
    """Read and choose the next teacher-attested, insertable errors."""
    candidates, _ = await _select_candidate_batch(lang, n)
    return candidates


def _batch_id() -> str:
    now = datetime.now(timezone.utc)
    return f"f3-{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"


async def convert(lang: str, n: int) -> dict[str, Any]:
    """Convert up to ``n`` candidates and atomically link their source rows."""
    candidates, known_collisions = await _select_candidate_batch(lang, n)
    batch = _batch_id()
    converted = 0
    skipped = len(known_collisions)
    examples: list[dict[str, str]] = []

    for candidate in known_collisions:
        log.warning(
            "grammar.f3.skipped",
            lang=lang,
            personal_error_id=candidate.get("id"),
            reason="sentence_collision",
        )

    for candidate in candidates:
        item = candidate_to_item(candidate)
        item_id = await db.insert_f3_grammar_item(
            int(candidate["id"]), item, batch=batch
        )
        if item_id is None:
            skipped += 1
            log.warning(
                "grammar.f3.skipped",
                lang=lang,
                personal_error_id=candidate.get("id"),
                reason="collision_or_already_converted",
            )
            continue
        converted += 1
        if len(examples) < 3:
            examples.append({"wrong": item["sentence"], "right": item["answer"]})

    log.info(
        "grammar.f3.converted",
        lang=lang,
        requested=n,
        candidates=len(candidates),
        known_collisions=len(known_collisions),
        converted=converted,
        skipped=skipped,
    )
    return {"converted": converted, "skipped": skipped, "examples": examples}
