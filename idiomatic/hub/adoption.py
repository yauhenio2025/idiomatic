"""Server-side example adoption (F4): durable identities for the studied
orphan/legacy Pool-v1 cards that phase 5 deferred.

Doctrine (same as C1): identity is never guessed. A deferred card is
resolved in exactly one of three ways —
  1. `existing-example`: its normalized bilingual pair now matches a
     fresh server example (rows minted after the campaign export);
  2. `adopt`: its expression surface matches exactly ONE server
     expression in its language (and that surface is not C1-quarantined)
     -> propose ONE new source-occurrence row + ONE new example row,
     INSERT-only, with deterministic retry keys;
  3. `defer`: anything ambiguous, glossless, quarantined, or unmatched.

Key recipes (versioned, aligned with design §3.2/§3.3 and the F1
backfill conventions in db/schema.sql):
  source_key  = "anki:v1:<profile_key>:<note_id>"
  stable_key  = "anki-adopt:v1:<profile_key>:<note_id>"
New example rows attach to their OWN adopted source-occurrence row
(video_id NULL) with ord=1 — never to an existing video occurrence,
whose (idiom_id, ord<=6) slots belong to the original six examples.
`position` is left NULL: the F1 boot backfill appends it after the
expression's existing examples deterministically.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import phase5

PLAN_SCHEMA_VERSION = 1
SOURCE_KEY_PREFIX = "anki:v1"
STABLE_KEY_PREFIX = "anki-adopt:v1"


def adoption_source_key(profile_key: str, note_id: int) -> str:
    return f"{SOURCE_KEY_PREFIX}:{profile_key}:{note_id}"


def adoption_stable_key(profile_key: str, note_id: int) -> str:
    return f"{STABLE_KEY_PREFIX}:{profile_key}:{note_id}"


# --- corpus indexes ----------------------------------------------------------

def corpus_indexes(corpus_rows: list[dict]) -> tuple[dict, dict]:
    """From /admin/corpus-export rows build:
    - sentence index: (lang, norm_tl, norm_en) -> row (ambiguous keys
      dropped, as in phase5);
    - surface index: (lang, norm_idiom_surface) -> set of expression_ids.
    """
    sentence: dict[tuple[str, str, str], dict] = {}
    ambiguous: set[tuple[str, str, str]] = set()
    surface: dict[tuple[str, str], set[int]] = {}
    for row in corpus_rows:
        lang = row["lang"]
        key = (lang, phase5.normalize_join(row["target_text"]),
               phase5.normalize_join(row["en_text"]))
        if key in sentence and \
                sentence[key]["example_id"] != int(row["example_id"]):
            ambiguous.add(key)
        else:
            sentence[key] = {
                "expression_id": int(row["expression_id"]),
                "example_id": int(row["example_id"]),
            }
        skey = (lang, phase5.normalize_join(row["idiom"]))
        surface.setdefault(skey, set()).add(int(row["expression_id"]))
    for key in ambiguous:
        sentence.pop(key, None)
    return sentence, surface


def c1_quarantined_surfaces(manifest: dict) -> set[tuple[str, str]]:
    out = set()
    for group in manifest["quarantine"]["c1_groups"]:
        surface_text = group.get("surface")
        if surface_text:
            out.add((group["language"], phase5.normalize_join(surface_text)))
    return out


# --- plan building -----------------------------------------------------------

def build_plan(*, deferred_cards: list[dict], note_fields: dict[int, dict],
               corpus_rows: list[dict], manifest: dict, c2_cards: dict[int, dict],
               profile_key: str, inputs: dict[str, str]) -> dict:
    """deferred_cards: manifest gap rows. note_fields: note_id -> dict of
    the Pool-v1 fields (Idiom, IdiomEn, Target, English) read from the
    collection copy. corpus_rows: fresh /admin/corpus-export rows.
    c2_cards: card_id -> C2 dossier row (for the C2-side normalized pair).

    JOIN PARITY RULE: the phase-5 compiler joins C2's own normalized card
    surfaces against phase5.normalize_join of server texts. The analyzer
    therefore (a) does its existing-example lookup with the C2 pair, and
    (b) only proposes an adoption when normalize_join(note field) equals
    the C2 normalization — proving the inserted server text will rejoin
    this exact card on recompile. Any divergence defers as
    `normalization-mismatch` (never guessed, never silently dropped)."""
    sentence_index, surface_index = corpus_indexes(corpus_rows)
    quarantined = c1_quarantined_surfaces(manifest)

    resolved_existing: list[dict] = []
    adoptions: list[dict] = []
    deferred: list[dict] = []
    proposed_pairs: dict[tuple[int, str, str], int] = {}

    def defer(card: dict, reason: str, detail: str = "") -> None:
        deferred.append({"card_id": int(card["card_id"]),
                         "note_id": int(card["note_id"]),
                         "language": card["language"],
                         "verdict": card.get("verdict"),
                         "reps": int(card.get("reps") or 0),
                         "reason": reason, "detail": detail})

    ordered = sorted(deferred_cards,
                     key=lambda c: (int(c.get("reps") or 0),
                                    int(c["card_id"])), reverse=True)
    for card in ordered:
        note = note_fields.get(int(card["note_id"]))
        if note is None:
            defer(card, "note-missing-in-copy")
            continue
        dossier = c2_cards.get(int(card["card_id"]))
        if dossier is None:
            defer(card, "missing-c2-dossier")
            continue
        lang = card["language"]
        c2_tl = dossier.get("normalized_target") or ""
        c2_en = dossier.get("normalized_english") or ""
        if not c2_tl or not c2_en:
            defer(card, "blank-sentence-side")
            continue

        hit = sentence_index.get((lang, c2_tl, c2_en))
        if hit is not None:
            resolved_existing.append({
                "card_id": int(card["card_id"]),
                "note_id": int(card["note_id"]),
                "language": lang,
                "expression_id": hit["expression_id"],
                "example_id": hit["example_id"],
                "verdict": card.get("verdict"),
                "reps": int(card.get("reps") or 0),
            })
            continue

        idiom_text = (note.get("Idiom") or "").strip()
        gloss = (note.get("IdiomEn") or "").strip()
        norm_surface = phase5.normalize_join(idiom_text)
        if not norm_surface:
            defer(card, "blank-expression-surface")
            continue
        if not gloss:
            defer(card, "missing-gloss")
            continue
        # Round-trip proof: the text we would INSERT must normalize (by
        # the compiler's server-side function) to the C2 key of this
        # card, or the adopted row could never rejoin its card.
        my_tl = phase5.normalize_join(note.get("Target") or "")
        my_en = phase5.normalize_join(note.get("English") or "")
        if my_tl != c2_tl or my_en != c2_en:
            defer(card, "normalization-mismatch",
                  f"tl_eq={my_tl == c2_tl} en_eq={my_en == c2_en}")
            continue
        if (lang, norm_surface) in quarantined:
            defer(card, "c1-quarantined-surface", idiom_text)
            continue
        candidates = surface_index.get((lang, norm_surface)) or set()
        if not candidates:
            defer(card, "no-expression-match", idiom_text)
            continue
        if len(candidates) > 1:
            defer(card, "ambiguous-expression-surface",
                  f"{idiom_text} -> {sorted(candidates)}")
            continue
        expression_id = next(iter(candidates))
        pair_key = (expression_id, c2_tl, c2_en)
        if pair_key in proposed_pairs:
            defer(card, "duplicate-proposed-pair",
                  f"winner card {proposed_pairs[pair_key]}")
            continue
        proposed_pairs[pair_key] = int(card["card_id"])
        adoptions.append({
            "card_id": int(card["card_id"]),
            "note_id": int(card["note_id"]),
            "language": lang,
            "expression_id": expression_id,
            "source_key": adoption_source_key(profile_key,
                                              int(card["note_id"])),
            "stable_key": adoption_stable_key(profile_key,
                                              int(card["note_id"])),
            "idiom_text": idiom_text,
            "english_gloss": gloss,
            "en_text": (note.get("English") or "").strip(),
            "target_text": (note.get("Target") or "").strip(),
            "verdict": card.get("verdict"),
            "reps": int(card.get("reps") or 0),
        })

    def lang_counter(rows: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["language"]] = counts.get(row["language"], 0) + 1
        return counts

    plan = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "profile_key": profile_key,
        "inputs": dict(inputs),
        "counts": {
            "deferred_input": len(deferred_cards),
            "resolved_existing": len(resolved_existing),
            "adoptions": len(adoptions),
            "adoption_reps": sum(a["reps"] for a in adoptions),
            "still_deferred": len(deferred),
            "by_lang_adoptions": lang_counter(adoptions),
            "by_lang_resolved": lang_counter(resolved_existing),
            "by_lang_deferred": lang_counter(deferred),
        },
        "resolved_existing": resolved_existing,
        "adoptions": adoptions,
        "deferred": deferred,
    }
    plan["content_sha256"] = phase5.manifest_content_sha256(plan)
    return plan


def load_plan(path: Path) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise ValueError("unsupported adoption plan schema_version")
    if phase5.manifest_content_sha256(plan) != plan.get("content_sha256"):
        raise ValueError("adoption plan content checksum mismatch")
    return plan


# --- applier SQL (INSERT-only, idempotent) -----------------------------------

INSERT_SOURCE_SQL = """
INSERT INTO expression_idioms
    (expression_id, video_id, lang, idiom_text, english_gloss,
     source_key, status)
VALUES ($1, NULL, $2, $3, $4, $5, 'active')
ON CONFLICT (expression_id, source_key) WHERE source_key IS NOT NULL
DO NOTHING
"""

SELECT_SOURCE_SQL = """
SELECT id FROM expression_idioms
 WHERE expression_id = $1 AND source_key = $2
"""

INSERT_EXAMPLE_SQL = """
INSERT INTO expression_examples
    (idiom_id, ord, en_text, target_text,
     expression_id, source_id, source_kind, stable_key, status)
VALUES ($1, 1, $2, $3, $4, $5, 'legacy_adopted', $6, 'published')
ON CONFLICT (stable_key) WHERE stable_key IS NOT NULL
DO NOTHING
"""

SELECT_RESULTS_SQL = """
SELECT ex.stable_key, ex.id AS example_id, ex.expression_id,
       ei.lang, ex.en_text, ex.target_text
  FROM expression_examples ex
  JOIN expression_idioms ei ON ei.id = ex.idiom_id
 WHERE ex.stable_key LIKE $1
 ORDER BY ex.id
"""


async def apply_plan(conn, plan: dict, *, batch_size: int = 500) -> dict:
    """INSERT-only application; safe to re-run (deterministic keys +
    ON CONFLICT DO NOTHING). `conn` is an asyncpg connection whose
    database already carries the F1 staging (probed by the caller)."""
    inserted_sources = inserted_examples = 0
    adoptions = plan["adoptions"]
    for start in range(0, len(adoptions), batch_size):
        batch = adoptions[start:start + batch_size]
        async with conn.transaction():
            for row in batch:
                status = await conn.execute(
                    INSERT_SOURCE_SQL, row["expression_id"],
                    row["language"], row["idiom_text"],
                    row["english_gloss"], row["source_key"])
                if status.endswith("1"):
                    inserted_sources += 1
                source_id = await conn.fetchval(
                    SELECT_SOURCE_SQL, row["expression_id"],
                    row["source_key"])
                if source_id is None:
                    raise RuntimeError(
                        f"source row missing after insert: "
                        f"{row['source_key']}")
                status = await conn.execute(
                    INSERT_EXAMPLE_SQL, source_id, row["en_text"],
                    row["target_text"], row["expression_id"], source_id,
                    row["stable_key"])
                if status.endswith("1"):
                    inserted_examples += 1
    return {"inserted_sources": inserted_sources,
            "inserted_examples": inserted_examples,
            "planned": len(adoptions)}


async def export_results(conn, profile_key: str) -> list[dict]:
    rows = await conn.fetch(SELECT_RESULTS_SQL,
                            f"{STABLE_KEY_PREFIX}:{profile_key}:%")
    return [dict(r) for r in rows]


# --- recompile merge ---------------------------------------------------------

def merge_adoption_results_into_extract(extract: dict,
                                        results: list[dict]) -> dict:
    """Append adopted examples to the server extract so the phase-5
    compiler joins the formerly deferred cards. Each adopted example
    rides under a synthetic single-example expression entry when its
    expression is absent from the extract, or is appended to the
    existing entry otherwise."""
    by_expr = {int(r["expression_id"]): r for r in extract["expressions"]}
    for row in results:
        entry = by_expr.get(int(row["expression_id"]))
        example = {"example_id": int(row["example_id"]),
                   "en_text": row["en_text"],
                   "target_text": row["target_text"]}
        if entry is None:
            entry = {"expression_id": int(row["expression_id"]),
                     "lang": row["lang"], "idiom": "",
                     "explanation_en": "", "examples": []}
            by_expr[int(row["expression_id"])] = entry
            extract["expressions"].append(entry)
        if all(int(e["example_id"]) != int(row["example_id"])
               for e in entry["examples"]):
            entry["examples"].append(example)
    return extract
