"""Private cross-language interference pairs compiled into F4 cards.

The reviewed pair banks are operator data, not package data.  The web process
strictly validates one uploaded JSON array and stages it with a single database
write.  Cron reparses the payload, verifies attestation against
``personal_errors``, and upserts the private ``f4_pairs`` rows.  Conversion is
deterministic: it selects dirty rows and maps them into ordinary verified
``grammar_items`` without an LLM or a second Anki model.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

import regex
import structlog

from .. import db

log = structlog.get_logger()


SCHEMA_VERSION = 1
PAIR_FIELDS = (
    "target_lang",
    "source_lang",
    "concept_en",
    "correct_target",
    "false_form",
    "source_form",
    "category",
    "why",
    "occurrences",
    "attested",
)

# German remains ingestible/data-ready, but its single reviewed pair does not
# warrant a public one-card curriculum cluster.  Conversion is therefore
# intentionally limited to these four receiving languages.
TOPIC_BY_LANG = {
    "es": "es_interference_f4",
    "pt": "pt_interference_f4",
    "fr": "fr_interference_f4",
    "it": "it_interference_f4",
}
TARGET_LANGS = frozenset({*TOPIC_BY_LANG, "de"})
SOURCE_LANGS = frozenset({"de", "en", "es", "fr", "it", "pt", "ru"})

# The design names these structural families as closed same-frame choices.
# Other categories first attempt certified production and fall back to C when
# no non-revealing whole-bank signature exists.
CLOSED_CHOICE_CATEGORIES = frozenset(
    {
        "verb_prep_regime",
        "preposition_selection",
        "relative_pronoun",
        "negation",
        "word_order",
    }
)
SHAPE_B_MIN_OCCURRENCES = 5

_PAIR_KEY_RE = re.compile(r"[0-9a-f]{64}\Z")
_GRAPHEME_RE = regex.compile(r"\X", regex.VERSION1)
_NON_ATOMIC_MARKERS = ("/", "|", "→", "=>", "->")


class _DuplicateJSONKey(ValueError):
    pass


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value}")


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def compute_pair_key(
    schema_version: int,
    target_lang: str,
    false_form: str,
    correct_target: str,
) -> str:
    """Return the frozen SHA-256 identity for a reviewed pair.

    Stored strings are never normalized or rewritten.  NFC is used only for
    this comparison/identity copy, exactly as specified by the commissioned
    bank design.
    """
    if type(schema_version) is not int or schema_version <= 0:
        raise ValueError("schema_version must be a positive integer")
    if not all(isinstance(value, str) for value in
               (target_lang, false_form, correct_target)):
        raise ValueError("pair-key fields must be strings")
    payload = json.dumps(
        [
            schema_version,
            _nfc(target_lang),
            _nfc(false_form),
            _nfc(correct_target),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _has_control(value: str) -> bool:
    joiners = {"\u200c", "\u200d"}
    for index, char in enumerate(value):
        category = unicodedata.category(char)
        if category in {"Cc", "Cs"}:
            return True
        # ZWNJ/ZWJ are valid members of extended grapheme clusters. Other
        # invisible format controls (notably bidi overrides) are not suitable
        # for a card prompt.
        if category == "Cf":
            if char not in joiners:
                return True
            # A bare/dangling joiner is invisible content, not a valid answer
            # grapheme. Embedded joiners remain available for emoji and
            # joining-script sequences handled by regex's Unicode \X.
            if (index == 0 or index == len(value) - 1
                    or value[index - 1] in joiners
                    or value[index + 1] in joiners):
                return True
    return False


def _nonempty_text(value: str) -> bool:
    return bool(value.strip()) and not _has_control(value)


def _atomic_answer(value: str) -> bool:
    return not any(marker in value for marker in _NON_ATOMIC_MARKERS)


def _projection_map(meta: Mapping[str, Any], errors: list[str]) -> dict[tuple[str, str], int]:
    raw = meta.get("reviewed_projections")
    if not isinstance(raw, list):
        errors.append("meta: reviewed_projections must be a list")
        return {}

    projections: dict[tuple[str, str], int] = {}
    expected = {"false_form", "correct_target", "registry_id", "reason"}
    for index, projection in enumerate(raw, 1):
        prefix = f"meta projection {index}"
        if not isinstance(projection, dict) or set(projection) != expected:
            errors.append(f"{prefix}: fields must be false_form, correct_target, "
                          "registry_id, reason")
            continue
        if (not isinstance(projection["false_form"], str)
                or not _nonempty_text(projection["false_form"])
                or not isinstance(projection["correct_target"], str)
                or not _nonempty_text(projection["correct_target"])
                or not isinstance(projection["reason"], str)
                or not _nonempty_text(projection["reason"])):
            errors.append(f"{prefix}: forms and reason must be non-empty strings")
            continue
        registry_id = projection["registry_id"]
        if type(registry_id) is not int or registry_id <= 0:
            errors.append(f"{prefix}: registry_id must be a positive integer")
            continue
        key = (_nfc(projection["false_form"]),
               _nfc(projection["correct_target"]))
        if key in projections:
            errors.append(f"{prefix}: duplicate reviewed projection")
            continue
        projections[key] = registry_id
    return projections


def _actual_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, dict[str, int]] = {}
    for row in rows:
        source = str(row["source_lang"])
        counts = by_source.setdefault(
            source, {"pairs": 0, "attested": 0, "family_extensions": 0}
        )
        counts["pairs"] += 1
        if row["attested"]:
            counts["attested"] += 1
        else:
            counts["family_extensions"] += 1
    return {
        "pairs": len(rows),
        "attested": sum(bool(row["attested"]) for row in rows),
        "family_extensions": sum(not bool(row["attested"]) for row in rows),
        "represented_source_rows": sum(int(row["occurrences"]) for row in rows),
        "by_source_lang": by_source,
    }


def parse_pair_bank(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Strictly parse one private F4 JSON-array bank.

    Errors identify only structural positions/fields, never pair values.  The
    returned rows retain all ten source fields byte-for-byte and add only the
    operational schema version, pair key, and optional projection registry id.
    """
    errors: list[str] = []
    try:
        raw = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError) as exc:
        return [], [f"bad JSON ({type(exc).__name__})"]

    if not isinstance(raw, list) or len(raw) < 2:
        return [], ["bank must be a JSON array with one meta header and rows"]
    if not isinstance(raw[0], dict) or set(raw[0]) != {"_meta"}:
        return [], ["item 0 must be exactly one _meta header"]
    meta = raw[0]["_meta"]
    if not isinstance(meta, dict):
        return [], ["meta header must be an object"]

    schema_version = meta.get("schema_version")
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION:
        errors.append(f"meta: schema_version must be {SCHEMA_VERSION}")
    if meta.get("schema") != list(PAIR_FIELDS):
        errors.append("meta: schema does not match the frozen ten-field order")
    target_lang = meta.get("target_lang")
    if not isinstance(target_lang, str) or target_lang not in TARGET_LANGS:
        errors.append("meta: unsupported target_lang")
    category_vocabulary = meta.get("category_vocabulary")
    if not isinstance(category_vocabulary, dict):
        errors.append("meta: category_vocabulary must be an object")
        category_vocabulary = {}
    projections = _projection_map(meta, errors)

    parsed: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    used_projections: set[tuple[str, str]] = set()
    string_fields = PAIR_FIELDS[:8]
    expected_fields = set(PAIR_FIELDS)

    for index, value in enumerate(raw[1:], 1):
        prefix = f"item {index}"
        if not isinstance(value, dict) or set(value) != expected_fields:
            errors.append(f"{prefix}: pair must contain exactly the ten fields")
            continue
        bad_type = False
        for field in string_fields:
            if not isinstance(value[field], str):
                errors.append(f"{prefix}: {field} must be a string")
                bad_type = True
        if type(value["occurrences"]) is not int:
            errors.append(f"{prefix}: occurrences must be an integer")
            bad_type = True
        if type(value["attested"]) is not bool:
            errors.append(f"{prefix}: attested must be a boolean")
            bad_type = True
        if bad_type:
            continue

        row = dict(value)
        for field in string_fields:
            if not _nonempty_text(row[field]):
                errors.append(f"{prefix}: {field} must be non-empty text")
        if any("___" in row[field] for field in string_fields):
            errors.append(f"{prefix}: bank text must not contain a card blank")
        if (not _atomic_answer(row["correct_target"])
                or not _atomic_answer(row["false_form"])):
            errors.append(f"{prefix}: pair forms must each be atomic")
        if row["target_lang"] not in TARGET_LANGS:
            errors.append(f"{prefix}: unsupported target_lang")
        if row["source_lang"] not in SOURCE_LANGS:
            errors.append(f"{prefix}: unsupported source_lang")
        if row["target_lang"] == row["source_lang"]:
            errors.append(f"{prefix}: source and target languages must differ")
        if isinstance(target_lang, str) and row["target_lang"] != target_lang:
            errors.append(f"{prefix}: target_lang differs from meta")
        if row["category"] not in category_vocabulary:
            errors.append(f"{prefix}: category is absent from meta vocabulary")
        if _nfc(row["false_form"]) == _nfc(row["correct_target"]):
            errors.append(f"{prefix}: false and correct forms are identical")
        if (row["attested"] and row["occurrences"] < 1) or (
            not row["attested"] and row["occurrences"] != 0
        ):
            errors.append(f"{prefix}: attestation/occurrence invariant failed")

        try:
            key = compute_pair_key(
                schema_version,
                row["target_lang"],
                row["false_form"],
                row["correct_target"],
            )
        except ValueError:
            # The meta error already states why schema_version is unusable.
            continue
        if key in seen_keys:
            errors.append(f"{prefix}: duplicate canonical pair tuple")
        seen_keys.add(key)

        projection_key = (_nfc(row["false_form"]),
                          _nfc(row["correct_target"]))
        projection_id = projections.get(projection_key)
        if projection_id is not None:
            if not row["attested"]:
                errors.append(f"{prefix}: an unattested row cannot use a projection")
            used_projections.add(projection_key)

        row["schema_version"] = schema_version
        row["pair_key"] = key
        row["projection_registry_id"] = projection_id
        parsed.append(row)

    unused_projections = set(projections) - used_projections
    if unused_projections:
        errors.append("meta: a reviewed projection does not match an attested row")

    if not errors:
        expected_counts = meta.get("counts")
        if expected_counts != _actual_counts(parsed):
            errors.append("meta: counts do not match bank rows")

    return (parsed if not errors else []), errors


def _graphemes(value: str) -> tuple[str, ...]:
    return tuple(_GRAPHEME_RE.findall(_nfc(value)))


def _token_graphemes(value: str) -> tuple[tuple[str, ...], ...]:
    # str.split() follows Python's Unicode whitespace definition and collapses
    # whitespace only on the comparison copy; stored source strings are intact.
    return tuple(_graphemes(token) for token in _nfc(value).split())


def _masked_prefix(tokens: Sequence[Sequence[str]], revealed: int) -> str:
    remaining = revealed
    masked: list[str] = []
    for token in tokens:
        visible = min(remaining, len(token))
        masked.append("".join(token[:visible]) + "·" * (len(token) - visible))
        remaining -= visible
    return " ".join(masked)


def production_signature(answer: str, bank_answers: Sequence[str]) -> str | None:
    """Return a non-revealing, whole-bank-unique production signature.

    The signature fixes token count and extended-grapheme lengths, then reveals
    the shortest left-to-right prefix that leaves exactly one matching bank row.
    Requiring the final grapheme would disclose the complete answer, so that
    case (and duplicate answers) returns ``None`` for Shape-C fallback.
    """
    if not isinstance(answer, str) or not _nonempty_text(answer):
        return None
    answer_nfc = _nfc(answer)
    tokens = _token_graphemes(answer_nfc)
    if not tokens or any(not token for token in tokens):
        return None
    flattened = tuple(grapheme for token in tokens for grapheme in token)
    lengths = tuple(len(token) for token in tokens)

    candidates: list[tuple[tuple[int, ...], tuple[str, ...]]] = []
    for candidate in bank_answers:
        if not isinstance(candidate, str) or not _nonempty_text(candidate):
            continue
        candidate_tokens = _token_graphemes(candidate)
        candidate_flat = tuple(g for token in candidate_tokens for g in token)
        candidates.append((tuple(len(token) for token in candidate_tokens),
                           candidate_flat))
    if not any(shape == lengths and flat == flattened for shape, flat in candidates):
        return None

    for revealed in range(0, len(flattened)):
        matches = sum(
            shape == lengths and flat[:revealed] == flattened[:revealed]
            for shape, flat in candidates
        )
        if matches == 1:
            mask = _masked_prefix(tokens, revealed)
            if len(lengths) == 1:
                dimensions = f"{lengths[0]} letters"
            else:
                dimensions = (
                    f"{len(lengths)} words · "
                    f"{'+'.join(str(length) for length in lengths)} letters"
                )
            return f"{mask} · {dimensions}"
    return None


def closed_choice_order(
    pair_key: str, correct_target: str, false_form: str,
) -> tuple[str, str]:
    """Order Shape-C candidates using the SHA-256 digest's highest bit."""
    if not isinstance(pair_key, str) or not _PAIR_KEY_RE.fullmatch(pair_key):
        raise ValueError("invalid F4 pair key")
    if _nfc(correct_target) == _nfc(false_form):
        raise ValueError("closed-choice candidates must differ")
    if int(pair_key[0], 16) < 8:
        return correct_target, false_form
    return false_form, correct_target


def _eligible(row: Mapping[str, Any]) -> bool:
    if row.get("target_lang") not in TOPIC_BY_LANG or row.get("status") != "active":
        return False
    if "needs_conversion" in row:
        return row.get("needs_conversion") is True
    return row.get("grammar_item_id") is None


def _revision_token(value: Any) -> str | None:
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    return isoformat() if callable(isoformat) else str(value)


def _shape_c_sentence(row: Mapping[str, Any]) -> str:
    first, second = closed_choice_order(
        row["pair_key"], row["correct_target"], row["false_form"]
    )
    return (
        f"[{row['source_lang'].upper()}] {row['source_form']} ⇄ "
        f"[{row['target_lang'].upper()}] ___\nchoose: {first} / {second}"
    )


def choose_candidates(
    rows: Sequence[Mapping[str, Any]], n: int,
) -> list[dict[str, Any]]:
    """Choose dirty cards: attested first, then recurrence, deterministically."""
    if n <= 0:
        return []
    eligible = [dict(row) for row in rows if _eligible(row)]
    eligible.sort(
        key=lambda row: (
            0 if row.get("attested") is True else 1,
            -int(row.get("occurrences") or 0),
            str(row.get("pair_key") or ""),
            int(row.get("id") or 0),
        )
    )
    return eligible[:n]


def pair_to_item(
    row: Mapping[str, Any], all_target_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compile one reviewed pair into the frozen grammar-item vocabulary."""
    target_lang = row.get("target_lang")
    try:
        topic = TOPIC_BY_LANG[str(target_lang)]
    except KeyError as exc:
        raise ValueError(f"unsupported F4 conversion language: {target_lang!r}") from exc

    required_text = (
        "source_lang", "source_form", "concept_en", "correct_target",
        "false_form", "category", "why", "pair_key",
    )
    if any(not isinstance(row.get(field), str) or not _nonempty_text(row[field])
           for field in required_text):
        raise ValueError("invalid F4 pair row")
    if not _PAIR_KEY_RE.fullmatch(row["pair_key"]):
        raise ValueError("invalid F4 pair key")
    if _nfc(row["correct_target"]) == _nfc(row["false_form"]):
        raise ValueError("F4 candidates must differ")

    answers = [
        str(candidate["correct_target"])
        for candidate in all_target_rows
        if candidate.get("target_lang") == target_lang
        and candidate.get("status", "active") == "active"
        and isinstance(candidate.get("correct_target"), str)
    ]
    signature = production_signature(row["correct_target"], answers)
    if row["category"] in CLOSED_CHOICE_CATEGORIES or signature is None:
        shape = "C"
        sentence = _shape_c_sentence(row)
        signature_meta: str | None = None
    elif row.get("attested") is True and int(row.get("occurrences") or 0) >= (
        SHAPE_B_MIN_OCCURRENCES
    ):
        shape = "B"
        sentence = (
            f"[{row['source_lang'].upper()}] {row['source_form']} · you said "
            f"[{target_lang.upper()}] {row['false_form']} → "
            f"[{target_lang.upper()}] ___  ({signature})"
        )
        signature_meta = signature
    else:
        shape = "A"
        sentence = (
            f"[{row['source_lang'].upper()}] {row['source_form']} · "
            f"“{row['concept_en']}” → [{target_lang.upper()}] ___  ({signature})"
        )
        signature_meta = signature

    # The signature itself must be the only target-language clue on a
    # production front. A full answer that appears through an unexpected false
    # form or assembly collision makes this a closed choice instead. A source
    # cue/concept that itself equals the answer is the design's legitimate
    # cross-language homograph exception.
    if shape in {"A", "B"}:
        answer_nfc = _nfc(row["correct_target"])
        front_nfc = _nfc(sentence)
        # Count only exact, visible homographs as legitimate occurrences.  A
        # broad substring exemption would let an unrelated leak in the false
        # form, signature text, or fixed prompt wording hide behind one valid
        # source-language homograph.
        homograph_fields = (
            ("source_form", "concept_en") if shape == "A"
            else ("source_form",)
        )
        allowed_occurrences = sum(
            _nfc(row[field]).count(answer_nfc)
            for field in homograph_fields
            if _nfc(row[field]) == answer_nfc
        )
        if front_nfc.count(answer_nfc) > allowed_occurrences:
            shape = "C"
            sentence = _shape_c_sentence(row)
            signature_meta = None

    if sentence.count("___") != 1:
        raise ValueError("F4 sentence must contain exactly one blank")
    return {
        "lang": target_lang,
        "topic": topic,
        "fmt": "f4",
        "infinitive": None,
        "mood": None,
        "tense": None,
        "person": None,
        "sentence": sentence,
        "answer": row["correct_target"],
        "gloss_en": row["concept_en"],
        "why_en": row["why"],
        "status": "verified",
        "meta": {
            "pair_key": row["pair_key"],
            "shape": shape,
            "signature": signature_meta,
            "source_lang": row["source_lang"],
            "source_form": row["source_form"],
            "false_form": row["false_form"],
            "category": row["category"],
            "attested": row.get("attested") is True,
            "occurrences": int(row.get("occurrences") or 0),
            # Every accepted upload updates this version on every active row in
            # the receiving-language bank. The DB helper compares it under its
            # row lock so a stale whole-bank signature can never be marked clean.
            "source_revision": _revision_token(row.get("updated_at")),
        },
    }


async def ingest_staged(batch_size: int = 500) -> dict[str, Any] | None:
    """Cron-side parse, attestation verification, and batched pair upsert."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    staged = await db.fetch_unprocessed_f4_staging()
    if not staged:
        return None

    ingested = upserted = 0
    for staged_row in staged:
        rows, errors = parse_pair_bank(staged_row["payload"])
        if errors:
            await db.mark_f4_staging(
                staged_row["id"], note=f"corrupt: {len(errors)} validation errors"
            )
            log.warning(
                "grammar.f4.ingest_corrupt",
                staging_id=staged_row["id"],
                n_errors=len(errors),
            )
            continue
        try:
            # One reviewed target bank is one atomic unit. upsert_f4_pairs
            # validates every attestation before its first write and owns the
            # transaction; splitting here could commit a prefix and then erase
            # the staging payload after a later deterministic failure.
            upserted += await db.upsert_f4_pairs(rows)
        except ValueError:
            # Registry mismatches are deterministic poison payloads.  Do not
            # include the exception text: even a reviewed form must not leak to
            # logs. Unexpected database exceptions still propagate for retry.
            await db.mark_f4_staging(
                staged_row["id"], note="corrupt: attestation validation failed"
            )
            log.warning(
                "grammar.f4.ingest_attestation_failed",
                staging_id=staged_row["id"],
            )
            continue
        ingested += len(rows)
        await db.mark_f4_staging(
            staged_row["id"], note=f"ok: {len(rows)} rows"
        )
    log.info("grammar.f4.ingested", rows=ingested, upserted=upserted)
    return {"ingested": ingested, "upserted": upserted}


def _batch_id() -> str:
    now = datetime.now(timezone.utc)
    return f"f4-{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"


async def convert(lang: str, n: int) -> dict[str, Any]:
    """Compile up to ``n`` dirty pairs, scanning past mapping/DB collisions."""
    if lang not in TOPIC_BY_LANG:
        raise ValueError(f"unsupported F4 language: {lang!r}")
    if n <= 0:
        return {"converted": 0, "skipped": 0, "examples": []}

    rows = await db.fetch_active_f4_pairs(lang)
    candidates = choose_candidates(rows, len(rows))
    batch = _batch_id()
    converted = skipped = 0
    examples: list[dict[str, Any]] = []

    for candidate in candidates:
        if converted >= n:
            break
        try:
            item = pair_to_item(candidate, rows)
        except ValueError:
            skipped += 1
            log.warning(
                "grammar.f4.skipped",
                pair_key=candidate.get("pair_key"),
                reason="mapping_failed",
            )
            continue
        item_id = await db.upsert_f4_grammar_item(
            int(candidate["id"]), item, batch=batch
        )
        if item_id is None:
            skipped += 1
            log.warning(
                "grammar.f4.skipped",
                pair_key=candidate.get("pair_key"),
                reason="collision_or_no_longer_dirty",
            )
            continue
        converted += 1
        if len(examples) < 3:
            examples.append(
                {
                    "pair_key": candidate["pair_key"],
                    "item_id": item_id,
                    "shape": item["meta"]["shape"],
                }
            )

    log.info(
        "grammar.f4.converted",
        lang=lang,
        requested=n,
        candidates=len(candidates),
        converted=converted,
        skipped=skipped,
    )
    return {"converted": converted, "skipped": skipped, "examples": examples}
