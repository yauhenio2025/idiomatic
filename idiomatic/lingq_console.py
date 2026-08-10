"""Owner decision console for the LingQ dormant-value concepts.

The seven payloads below are aggregate-only distillations of
``docs/research/lingq/REPORT.md``, ``inventory.json``, and
``LINGQ_VALUE_PROPOSAL.md``.  They deliberately contain no row-level LingQ
terms, hints, fragments, IDs, or dates.

This is a decision surface only.  Saving a verdict never starts a build,
changes a collection, or commissions work automatically; the coordinator
reads the stored decisions and commissions any follow-up separately.
"""

from __future__ import annotations

import json
from typing import Any

from . import db

VERDICTS = frozenset(
    {"greenlight-pilot", "interested-later", "not-for-me", "defer"}
)

# Ranked in the order used by the proposal's scoring table.  C2/C3 and
# C4/C5/C6 have tied scores; the table order supplies the displayed tie-break.
CONCEPTS: tuple[dict[str, Any], ...] = (
    {
        "concept_key": "c1_second_encounter",
        "concept_id": "C1",
        "name": "Second Encounter",
        "pitch": (
            "Turn expressions the owner met in chosen native texts into "
            "production cards: the original fragment cues the first encounter, "
            "while a verified gloss and one constrained fresh example make the "
            "expression usable rather than merely recognizable."
        ),
        "sizing": [
            {
                "value": "5,455",
                "label": "never-drilled multiword candidates in active languages",
            },
            {
                "value": "DE 1,593 · FR 1,510 · IT 905 · PT 775 · ES 672",
                "label": "candidate split",
            },
            {
                "value": "97.6%",
                "label": "estate-wide fragment coverage",
            },
        ],
        "study_minutes_per_day": 3.0,
        "study_impact": "~3 min/day at 8 new expressions/day",
        "proposal_rank": 1,
        "proposal_score": 18,
        "recommended": True,
        "recommendation_reason": (
            "Recommended FR 60-card pilot: it combines the two strongest assets "
            "(attested expressions and episodic fragments), is uniquely personal, "
            "keeps generated surfaces small and verifiable, and tests C2's woven "
            "example mechanism at the same time."
        ),
    },
    {
        "concept_key": "c2_own_words_weaver",
        "concept_id": "C2",
        "name": "Own-Words Weaver",
        "pitch": (
            "Generate one-target production sentences whose content words stay "
            "inside the owner's lemmatized encounter lexicon plus a small "
            "high-frequency allowance, turning personalized generation into a "
            "mechanically testable constraint rather than a style guess."
        ),
        "sizing": [
            {"value": "34,065", "label": "terms across the five active languages"},
            {"value": "1,248", "label": "learned-tier terms for the first seed"},
            {"value": "826", "label": "durable-known conservative subset"},
        ],
        "study_minutes_per_day": 4.0,
        "study_impact": "~4 min/day at a capped 5 new cards/day",
        "proposal_rank": 2,
        "proposal_score": 16,
        "recommended": False,
        "recommendation_reason": None,
    },
    {
        "concept_key": "c3_reading_relics",
        "concept_id": "C3",
        "name": "Reading Relics",
        "pitch": (
            "Reuse LingQ's existing cloze-marked fragments as a capped stream of "
            "episodic recall cards, restoring the hidden surface form with a "
            "mechanical letter-and-term check and generating no target-language "
            "text beyond audio."
        ),
        "sizing": [
            {"value": "17,303", "label": "pre-clozed fragments in active languages"},
            {
                "value": "DE 9,796 · FR 2,596 · ES 2,522 · PT 2,243 · IT 146",
                "label": "active-language split",
            },
            {"value": "~$0", "label": "text-generation cost"},
        ],
        "study_minutes_per_day": 2.0,
        "study_impact": "~2 min/day as an owner-throttled drip",
        "proposal_rank": 3,
        "proposal_score": 16,
        "recommended": False,
        "recommendation_reason": None,
    },
    {
        "concept_key": "c5_polyglot_mirror",
        "concept_id": "C5",
        "name": "Polyglot Mirror",
        "pitch": (
            "Pair high-confidence equivalents from the owner's different language "
            "histories and drill sideways retrieval, using each side's attested "
            "fragment to strengthen language boundaries and explicitly surface "
            "valuable false-friend risks."
        ),
        "sizing": [
            {"value": "10 languages", "label": "one-brain encounter log"},
            {"value": "51,826", "label": "terms available for conservative matching"},
            {"value": "~300–800", "label": "estimated high-precision pairs"},
        ],
        "study_minutes_per_day": 1.0,
        "study_impact": "~1 min/day per language at 2–3 cards/day",
        "proposal_rank": 4,
        "proposal_score": 13,
        "recommended": False,
        "recommendation_reason": None,
    },
    {
        "concept_key": "c6_frontier_podcast",
        "concept_id": "C6",
        "name": "Frontier Podcast",
        "pitch": (
            "Weave a small frontier set into one weekly own-words narrative, "
            "re-encountering personal vocabulary in fresh listening context through "
            "the existing podcast machinery without adding a daily wall of cards."
        ),
        "sizing": [
            {"value": "15–20", "label": "frontier terms per weekly episode"},
            {"value": "4–5 min", "label": "episode length per language"},
            {"value": "1 episode", "label": "French pilot scope"},
        ],
        "study_minutes_per_day": 0.7,
        "study_impact": "5 min/week per language (~0.7 min/day averaged)",
        "proposal_rank": 5,
        "proposal_score": 13,
        "recommended": False,
        "recommendation_reason": None,
    },
    {
        "concept_key": "c4_morph_slot",
        "concept_id": "C4",
        "name": "Morph Slot",
        "pitch": (
            "Turn clozed fragments into one-form morphology drills: the lemma and "
            "sentence context ask for the inflected surface form, with restoration "
            "checked mechanically and the grammar explanation gated by existing "
            "morphology tables."
        ),
        "sizing": [
            {"value": "17,303", "label": "active-language cloze candidates shared with C3"},
            {"value": "9,796", "label": "German clozed fragments"},
            {"value": "7–10 sec", "label": "estimated review time"},
        ],
        "study_minutes_per_day": 1.0,
        "study_impact": "~1 min/day as a tiny capped drip (estimated)",
        "proposal_rank": 6,
        "proposal_score": 13,
        "recommended": False,
        "recommendation_reason": None,
    },
    {
        "concept_key": "c7_picture_idiom",
        "concept_id": "C7",
        "name": "Picture This Idiom",
        "pitch": (
            "Add a literal-scene image cue to the most concrete, imageable C1 "
            "expressions, making imagery a selective memory anchor while inheriting "
            "C1's attested text gates and requiring owner-reviewed image QA."
        ),
        "sizing": [
            {"value": "~10%", "label": "estimated imageable share of C1 candidates"},
            {"value": "60 cards", "label": "proposed image pilot"},
            {"value": "~$2.20", "label": "pilot images before retries"},
        ],
        "study_minutes_per_day": 0.0,
        "study_impact": "0 incremental minutes/day; this is a C1 card variant",
        "proposal_rank": 7,
        "proposal_score": 12,
        "recommended": False,
        "recommendation_reason": None,
    },
)

CONCEPT_KEYS = frozenset(row["concept_key"] for row in CONCEPTS)
_UNSET = object()


def _validate_definitions() -> None:
    if len(CONCEPTS) != 7 or len(CONCEPT_KEYS) != 7:
        raise RuntimeError("LingQ console must define exactly seven unique concepts")
    if sum(bool(row["recommended"]) for row in CONCEPTS) != 1:
        raise RuntimeError("LingQ console must define exactly one recommended pilot")
    if [row["proposal_rank"] for row in CONCEPTS] != list(range(1, 8)):
        raise RuntimeError("LingQ proposal ranks must be 1 through 7")


_validate_definitions()


def _seed_values(rows: tuple[dict[str, Any], ...] = CONCEPTS) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for row in rows:
        payload = {key: value for key, value in row.items() if key != "concept_key"}
        values.append(
            (row["concept_key"], json.dumps(payload, ensure_ascii=False))
        )
    return values


async def lingq_verdict_count() -> int:
    """Return the current number of seeded concept rows."""
    pool = await db.get_pool()
    return await pool.fetchval("SELECT COUNT(*) FROM lingq_verdicts") or 0


async def seed_lingq_verdicts(
    rows: tuple[dict[str, Any], ...] = CONCEPTS,
) -> None:
    """Upsert code-owned payloads without touching owner decision columns."""
    values = _seed_values(rows)
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO lingq_verdicts (concept_key, payload)
                VALUES ($1, $2::jsonb)
                ON CONFLICT (concept_key) DO UPDATE SET
                  payload = EXCLUDED.payload,
                  seeded_at = NOW()
                """,
                values,
            )


async def seed_lingq_verdicts_if_empty() -> bool:
    """Seed the seven concepts only while the table is empty."""
    if await lingq_verdict_count() > 0:
        return False
    await seed_lingq_verdicts()
    return True


def _payload_dict(value: Any, concept_key: str) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid payload for {concept_key}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"invalid payload for {concept_key}")
    return value


async def list_lingq_verdicts() -> list[dict[str, Any]]:
    """List concept payloads with the owner's stored decision fields."""
    pool = await db.get_pool()
    records = await pool.fetch(
        """
        SELECT concept_key, payload, owner_verdict, owner_note,
               verdicted_at, seeded_at
        FROM lingq_verdicts
        ORDER BY (payload->>'proposal_rank')::integer, concept_key
        """
    )
    rows: list[dict[str, Any]] = []
    for record in records:
        stored = dict(record)
        concept_key = stored["concept_key"]
        payload = _payload_dict(stored.pop("payload"), concept_key)
        rows.append({"concept_key": concept_key, **payload, **stored})
    return rows


def progress_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize completion without assigning meaning to the verdicts."""
    verdict_counts: dict[str, int] = {}
    for row in rows:
        key = row.get("owner_verdict") or "unverdicted"
        verdict_counts[key] = verdict_counts.get(key, 0) + 1
    remaining = verdict_counts.get("unverdicted", 0)
    return {
        "total": len(rows),
        "verdicted": len(rows) - remaining,
        "remaining": remaining,
        "verdict_counts": verdict_counts,
    }


async def save_lingq_verdict(
    concept_key: str,
    *,
    verdict: str | None | object = _UNSET,
    note: str | None | object = _UNSET,
) -> dict[str, Any]:
    """Store a verdict and/or note after validating the fixed vocabulary.

    ``None`` for verdict is treated as omitted, matching the existing triage
    endpoint.  A supplied empty note clears the note without changing the
    verdict or its timestamp.
    """
    key = str(concept_key or "").strip()
    if key not in CONCEPT_KEYS:
        raise ValueError("unknown concept_key")
    if verdict is None:
        verdict = _UNSET
    if verdict is not _UNSET and (
        not isinstance(verdict, str) or verdict not in VERDICTS
    ):
        raise ValueError(f"verdict must be one of {sorted(VERDICTS)}")
    if verdict is _UNSET and note is _UNSET:
        raise ValueError("nothing to set (need verdict and/or note)")

    sets: list[str] = []
    args: list[Any] = []
    if verdict is not _UNSET:
        args.append(verdict)
        sets.append(f"owner_verdict = ${len(args)}")
        sets.append("verdicted_at = NOW()")
    if note is not _UNSET:
        normalized_note = str(note or "") or None
        args.append(normalized_note)
        sets.append(f"owner_note = ${len(args)}")
    args.append(key)

    pool = await db.get_pool()
    record = await pool.fetchrow(
        f"UPDATE lingq_verdicts SET {', '.join(sets)} "
        f"WHERE concept_key = ${len(args)} RETURNING concept_key",
        *args,
    )
    if not record:
        raise LookupError("concept is known but has not been seeded")
    return {"ok": True, "concept_key": record["concept_key"]}
