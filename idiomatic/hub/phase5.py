"""Phase-5 manifest compiler + executor core for the Expression Hub.

Work package F3 (docs/commissions/HUB_BUILD_EXECUTION_COMMISSION.md).
This module holds every PURE piece — join normalization, C1/C2/server
joins, the checksummed manifest schema, conversion field plans, and
connection-level verification — so tests can exercise it without a
guarded collection copy. The scripts under
docs/research/anki_reorg_scripts/hub_phase5_*.py wire these functions to
validated copy paths, journals, and the anki API, following the estate
scripts' safety patterns.

Inputs and their meaning:
- C1 (sense resolution): dispositions over ARCHIVED collision bundles.
  Quarantined groups are owner-ratified exclusions (2026-08-09) — their
  members stay archived and untouched.
- C2 (schedule dossiers): every active fluency-lane Pool-v1 card with a
  health verdict. `adoptable` keeps its schedule through the supported
  in-place conversion; `fresh-trivial` (zero reps) converts in place too
  — there is no schedule to lose. Cards under the seven ambiguous
  normalized join keys are excluded from conversion and archived.
- Server extract: durable expression/example identities. Default source
  is the committed illustration-campaign export (produced by
  /admin/corpus-export); the C3 extract drops in with the same shape.

MANIFEST DOCTRINE: identity is never guessed. A Pool card joins a server
example only by exact equality of the estate-normalized bilingual pair;
anything unjoined is DEFERRED (left untouched, reported as a gap), never
converted, never archived.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html as html_lib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from . import apkg as hub_apkg
from . import identity

MANIFEST_SCHEMA_VERSION = 1
POOL_MODEL_ID = 1820114700

# Migration doc §5.1: old Pool-v1 field -> new Example-v1 field.
POOL_TO_EXAMPLE_FIELD_MAP = {
    "English": "English",
    "Target": "Target",
    "EnglishAudio": "EnglishAudio",
    "TargetAudio": "TargetAudio",
    "Idiom": "Expression",
    "IdiomEn": "GlossEN",
    "Source": "SourceHTML",
}
POOL_FIELDS_IN_ORDER = [
    "English", "Target", "EnglishAudio", "TargetAudio",
    "Idiom", "IdiomEn", "Source",
]


def pool_to_example_fmap() -> dict[int, int]:
    """Old field ordinal -> new field ordinal for models.change."""
    return {
        POOL_FIELDS_IN_ORDER.index(old): hub_apkg.EXAMPLE_FIELDS.index(new)
        for old, new in POOL_TO_EXAMPLE_FIELD_MAP.items()
    }


# --- estate join normalization (C2 methodology §"Join surfaces") -------------

_SOUND_RE = re.compile(r"\[sound:[^\]]*\]")
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_QUOTE_MAP = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "−": "-",
    " ": " ",
})


def normalize_join(text: str) -> str:
    """Estate normalization: strip [sound:]/HTML, unescape, NFKC,
    stabilize curly quotes/dashes, collapse whitespace, casefold —
    accents and punctuation preserved."""
    s = _SOUND_RE.sub(" ", text or "")
    s = _TAG_RE.sub(" ", s)
    s = html_lib.unescape(s)
    s = unicodedata.normalize("NFKC", s)
    s = s.translate(_QUOTE_MAP)
    s = _WS_RE.sub(" ", s).strip()
    return s.casefold()


# --- checksums ---------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_extract_sha256(directory: Path, pattern: str) -> str:
    """Deterministic checksum over a set of files: sha256 of the sorted
    (name, file-sha256) list."""
    rows = [(p.name, sha256_file(p))
            for p in sorted(directory.glob(pattern))]
    return sha256_bytes(json.dumps(rows, separators=(",", ":")).encode())


def manifest_content_sha256(manifest: dict) -> str:
    """Self-checksum over everything except the checksum field itself."""
    body = {k: v for k, v in manifest.items() if k != "content_sha256"}
    return sha256_bytes(json.dumps(
        body, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode())


class ExpectationError(RuntimeError):
    """An input's checksum does not match the recorded expectation."""


def check_expectations(expected: dict[str, str], actual: dict[str, str]) -> None:
    problems = []
    for name, want in expected.items():
        got = actual.get(name)
        if got != want:
            problems.append(f"{name}: expected {want[:16]}…, got "
                            f"{(got or 'MISSING')[:16]}…")
    extra = set(actual) - set(expected)
    if extra:
        problems.append(f"unexpected inputs: {sorted(extra)}")
    if problems:
        raise ExpectationError("input expectations not met: "
                               + "; ".join(problems))


# --- server extract ----------------------------------------------------------

def load_server_extract_from_illustration_inputs(directory: Path) -> dict:
    """Adapt the committed campaign export to the extract shape the C3
    file will use: {expressions: [{expression_id, lang, idiom,
    explanation_en, examples: [{example_id, en_text, target_text}]}]}."""
    expressions = []
    seen: set[int] = set()
    for path in sorted(directory.glob("*_illu_b*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            eid = int(row["expression_id"])
            if eid in seen:
                continue
            seen.add(eid)
            expressions.append({
                "expression_id": eid,
                "lang": row["lang"],
                "idiom": row["idiom"],
                "explanation_en": row.get("explanation_en") or "",
                "examples": [
                    {"example_id": int(e["example_id"]),
                     "en_text": e["en_text"],
                     "target_text": e["target_text"]}
                    for e in row.get("examples", [])
                ],
            })
    return {"kind": "illustration_prompts_input", "expressions": expressions}


def load_server_extract(path: Path) -> dict:
    """Load a C3-style extract file; enforce the drop-in shape."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "expressions" not in data:
        raise ValueError("server extract must be an object with 'expressions'")
    for row in data["expressions"]:
        for key in ("expression_id", "lang", "idiom", "examples"):
            if key not in row:
                raise ValueError(f"extract expression missing {key}: "
                                 f"{json.dumps(row)[:120]}")
        for ex in row["examples"]:
            for key in ("example_id", "en_text", "target_text"):
                if key not in ex:
                    raise ValueError(f"extract example missing {key}")
    return data


# --- manifest compilation ----------------------------------------------------

def _example_join_index(extract: dict) -> dict[tuple[str, str, str], dict]:
    """(lang, norm_target, norm_english) -> {expression_id, example_id,
    idiom, ...}. Ambiguous keys (two examples, same normalized pair) are
    dropped from the index and reported — identity is never guessed."""
    index: dict[tuple[str, str, str], dict] = {}
    ambiguous: set[tuple[str, str, str]] = set()
    for row in extract["expressions"]:
        for ex in row["examples"]:
            key = (row["lang"], normalize_join(ex["target_text"]),
                   normalize_join(ex["en_text"]))
            if key in index and index[key]["example_id"] != int(ex["example_id"]):
                ambiguous.add(key)
                continue
            index[key] = {
                "expression_id": int(row["expression_id"]),
                "example_id": int(ex["example_id"]),
                "idiom": row["idiom"],
                "explanation_en": row.get("explanation_en") or "",
                "target_text": ex["target_text"],
                "en_text": ex["en_text"],
            }
    for key in ambiguous:
        index.pop(key, None)
    return index


def compile_manifest(*, c1: dict, c2: dict, extract: dict,
                     input_checksums: dict[str, str]) -> dict:
    """Join C1 + C2 + server extract into the phase-5 manifest."""
    # C1: quarantined bundles are excluded evidence; everything else in
    # C1 is archived material that phase 5 must NOT touch (it already is
    # archived) — recorded for the quarantine/evidence sections only.
    c1_quarantine = []
    c1_archive_note_ids: set[int] = set()
    for group in c1["groups"]:
        member_notes = [int(m["note_id"]) for m in group["members"]]
        c1_archive_note_ids.update(member_notes)
        if group["disposition"] == "quarantine":
            c1_quarantine.append({
                "group_id": group["group_id"],
                "language": group["language"],
                "surface": (group.get("survivor") or {}).get(
                    "normalized_surface"),
                "member_note_ids": member_notes,
            })

    join_index = _example_join_index(extract)
    extract_by_expr = {int(r["expression_id"]): r
                       for r in extract["expressions"]}

    conversions: list[dict] = []
    deferred: list[dict] = []
    joinkey_quarantine: list[dict] = []
    claimed_examples: dict[int, dict] = {}

    def investment(card: dict) -> tuple:
        return (int(card.get("reps") or 0),
                int(card.get("revlog_rows") or 0),
                card.get("last_review_id") or 0)

    # Deterministic pass order: most-invested first, so a duplicate
    # example binding always keeps the most-invested donor (§4.2).
    for card in sorted(c2["cards"], key=investment, reverse=True):
        if int(card["model_id"]) != POOL_MODEL_ID:
            deferred.append({"card_id": int(card["card_id"]),
                             "reason": "non-pool-model"})
            continue
        if int(card.get("join_key_cardinality") or 1) > 1:
            joinkey_quarantine.append({
                "card_id": int(card["card_id"]),
                "note_id": int(card["note_id"]),
                "language": card["language"],
                "normalized_target": card["normalized_target"],
                "peers": card.get("join_key_peer_card_ids") or [],
                "reps": int(card.get("reps") or 0),
            })
            continue
        key = (card["language"], card["normalized_target"],
               card["normalized_english"])
        hit = join_index.get(key)
        if hit is None:
            deferred.append({
                "card_id": int(card["card_id"]),
                "note_id": int(card["note_id"]),
                "language": card["language"],
                "reason": "unjoined-bilingual-pair",
                "verdict": card["verdict"],
                "reps": int(card.get("reps") or 0),
                "normalized_target": card["normalized_target"],
            })
            continue
        prior = claimed_examples.get(hit["example_id"])
        if prior is not None:
            deferred.append({
                "card_id": int(card["card_id"]),
                "note_id": int(card["note_id"]),
                "language": card["language"],
                "reason": "duplicate-example-binding",
                "verdict": card["verdict"],
                "reps": int(card.get("reps") or 0),
                "example_id": hit["example_id"],
                "winner_card_id": prior["card_id"],
            })
            continue
        row = {
            "card_id": int(card["card_id"]),
            "note_id": int(card["note_id"]),
            "note_guid": card["note_guid"],
            "language": card["language"],
            "expression_id": hit["expression_id"],
            "example_id": hit["example_id"],
            "adoption": card["verdict"],  # adoptable | fresh-trivial
            "schedule_evidence": {
                k: card.get(k) for k in
                ("type", "queue", "due", "ivl", "factor", "reps",
                 "lapses", "left", "odue", "odid", "revlog_rows")
            },
        }
        claimed_examples[hit["example_id"]] = row
        conversions.append(row)

    # Hubs: one per expression with >= 1 conversion. The example grid is
    # the SERVER example set (design: canonical published set), not just
    # the converted members.
    hub_exprs = sorted({c["expression_id"] for c in conversions})
    hubs = []
    for expr_id in hub_exprs:
        src = extract_by_expr[expr_id]
        hubs.append({
            "expression_id": expr_id,
            "lang": src["lang"],
            "expression": src["idiom"],
            "usage_line_en": src.get("explanation_en") or "",
            "target_guid": identity.hub_guid(src["lang"], expr_id),
            "examples": [
                {"example_id": int(e["example_id"]),
                 "target_text": e["target_text"], "en_text": e["en_text"]}
                for e in src["examples"]
            ],
            # GlossEN + SourcesHTML are harvested from member note fields
            # at execution time (migration §5.1 fallback path); the C3
            # extract may enrich them later.
            "gloss_source": "member-IdiomEn",
            "sources_source": "member-Source",
        })

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "input_checksums": dict(input_checksums),
        "collection_source_sha256": c2.get("source_sha256"),
        "counts": {
            "c2_cards": len(c2["cards"]),
            "conversions": len(conversions),
            "conversions_adoptable": sum(
                1 for c in conversions if c["adoption"] == "adoptable"),
            "conversions_fresh_trivial": sum(
                1 for c in conversions if c["adoption"] == "fresh-trivial"),
            "adopted_reps": sum(
                int(c["schedule_evidence"]["reps"] or 0)
                for c in conversions),
            "hub_notes": len(hubs),
            "deferred": len(deferred),
            # The rehearsal's headline gap: studied (adoptable) cards that
            # cannot join a durable server example yet — mostly legacy-
            # generation sentences needing server-side example adoption
            # (a DB-write phase outside this executor's remit).
            "deferred_adoptable": sum(
                1 for g in deferred if g.get("verdict") == "adoptable"),
            "deferred_reps": sum(int(g.get("reps") or 0) for g in deferred),
            "joinkey_quarantine_cards": len(joinkey_quarantine),
            "c1_quarantine_groups": len(c1_quarantine),
            "c1_archive_notes": len(c1_archive_note_ids),
        },
        "conversions": conversions,
        "hubs": hubs,
        "quarantine": {
            "c1_groups": c1_quarantine,
            "join_key_cards": joinkey_quarantine,
        },
        "gaps": {
            "deferred_cards": deferred,
        },
        "c1_archive_note_ids": sorted(c1_archive_note_ids),
    }
    manifest["content_sha256"] = manifest_content_sha256(manifest)
    return manifest


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError("unsupported manifest schema_version")
    if manifest_content_sha256(manifest) != manifest.get("content_sha256"):
        raise ValueError("manifest content checksum mismatch")
    return manifest


# --- asset-coverage enrichment (C3) ------------------------------------------
# Assets are an ENRICHMENT LAYER, never a blocker: the manifest records
# per-example asset status (only `qa-passed` counts as an approved image);
# the phase-5 executor still leaves the Image field blank — bytes ship
# through the release builder against the recorded hashes.

def load_asset_coverage(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "examples" not in data:
        raise ValueError("asset coverage file has no 'examples'")
    by_example: dict[int, dict] = {}
    for row in data["examples"]:
        example_id = int(row["example_id"])
        entry = {"status": row["final_status"]}
        qa_hash = ((row.get("qa") or {}).get("content_hash") or {}).get("value")
        if qa_hash:
            entry["qa_sha1"] = qa_hash
        by_example[example_id] = entry
    return {
        "source_generated_at": data.get("generated_at"),
        "source_content_sha256": data.get("content_sha256"),
        "by_example": by_example,
    }


def apply_asset_coverage(manifest: dict, coverage: dict) -> dict:
    """Annotate hub examples with asset status and re-seal the manifest."""
    by_example = coverage["by_example"]
    qa_passed = missing = 0
    for hub in manifest["hubs"]:
        for example in hub["examples"]:
            info = by_example.get(int(example["example_id"]))
            if info is None:
                example["asset_status"] = "no-coverage-row"
                missing += 1
                continue
            example["asset_status"] = info["status"]
            if info["status"] == "qa-passed":
                example["asset_sha1"] = info.get("qa_sha1")
                qa_passed += 1
    manifest["asset_coverage"] = {
        "source_generated_at": coverage.get("source_generated_at"),
        "source_content_sha256": coverage.get("source_content_sha256"),
        "qa_passed_examples": qa_passed,
        "examples_missing_coverage": missing,
    }
    manifest["counts"]["asset_qa_passed_examples"] = qa_passed
    manifest["content_sha256"] = manifest_content_sha256(manifest)
    return manifest


# --- execution field plans ---------------------------------------------------

def example_field_fill(conversion: dict) -> dict[str, str]:
    """Fields to set AFTER the supported models.change move (the fmap
    itself carries the seven legacy fields)."""
    return {
        "ExpressionId": str(conversion["expression_id"]),
        "ExampleId": str(conversion["example_id"]),
        "Lang": conversion["language"],
        "Origin": "initial",
        # Image stays blank in phase 5; the release build injects the
        # QA-passed content-addressed asset reference (enrichment layer).
    }


def example_tags(conversion: dict) -> list[str]:
    return ["idiomatic::expression-example",
            f"lang::{conversion['language']}",
            f"expression::{conversion['expression_id']}",
            f"example::{conversion['example_id']}",
            "origin::initial"]


def hub_fields(hub: dict, *, gloss_en: str, sources_html: str) -> list[str]:
    """Ordered field values for a fresh hub note (model 1820180001)."""
    values = {
        "ExpressionId": str(hub["expression_id"]),
        "Lang": hub["lang"],
        "Expression": hub["expression"],
        "GlossEN": gloss_en,
        "UsageLineEN": hub.get("usage_line_en") or "",
        "KeySynonym": "",
        "FalseFriend": "",
        "ExamplesHTML": hub_apkg.build_examples_html([
            {"example_id": e["example_id"],
             "target_text": e["target_text"],
             "en_text": e["en_text"], "image_media": None}
            for e in hub["examples"]
        ]),
        "SourcesHTML": sources_html,
        "ContextAudio": "",
        "ExpressionAudio": "",
        "Extra1": "", "Extra2": "", "Extra3": "",
    }
    return [values[name] for name in hub_apkg.HUB_FIELDS]


def hub_tags(hub: dict) -> list[str]:
    return ["idiomatic::expression-hub", f"lang::{hub['lang']}",
            f"expression::{hub['expression_id']}", "hub-schema::1"]


# --- connection-level verification -------------------------------------------
# All functions take an open sqlite3 connection (read-only or not) so
# tests can run them against any temp collection.

def card_schedule_row(connection, card_id: int) -> tuple:
    return connection.execute(
        """SELECT id,nid,ord,type,queue,due,ivl,factor,reps,lapses,left,
                  odue,odid,flags,data FROM cards WHERE id=?""",
        (card_id,)).fetchone()


def verify_conversions(connection, manifest: dict,
                       before_rows: dict[int, tuple]) -> list[str]:
    """Adopted schedules must be byte-identical; mids must be the frozen
    example model; GUIDs retained."""
    problems = []
    for conv in manifest["conversions"]:
        cid = int(conv["card_id"])
        after = card_schedule_row(connection, cid)
        before = before_rows.get(cid)
        if after is None or before is None:
            problems.append(f"card {cid}: missing before/after row")
            continue
        if tuple(after) != tuple(before):
            problems.append(f"card {cid}: schedule row changed")
        note = connection.execute(
            "SELECT mid, guid FROM notes WHERE id=?",
            (int(conv["note_id"]),)).fetchone()
        if note is None:
            problems.append(f"note {conv['note_id']}: missing")
            continue
        if int(note[0]) != hub_apkg.EXAMPLE_MODEL_ID:
            problems.append(f"note {conv['note_id']}: mid {note[0]}")
        if note[1] != conv["note_guid"]:
            problems.append(f"note {conv['note_id']}: guid changed")
    return problems


def verify_expression_focus_purity(connection) -> list[str]:
    """Every card in a `2 Expression Focus` deck must be the hub model."""
    rows = connection.execute(
        """SELECT d.name, n.mid, COUNT(*) FROM cards c
             JOIN decks d ON d.id = c.did
             JOIN notes n ON n.id = c.nid
            WHERE d.name LIKE '%2 Expression Focus%'
            GROUP BY d.name, n.mid""").fetchall()
    return [f"{name}: {count} cards of model {mid}"
            for (name, mid, count) in rows
            if int(mid) != hub_apkg.HUB_MODEL_ID]


def verify_fluency_lane_models(connection, manifest: dict) -> list[str]:
    """Fluency lanes may contain only converted example notes plus the
    manifest's deferred Pool-v1 cards."""
    deferred = {int(g["card_id"]) for g in manifest["gaps"]["deferred_cards"]}
    problems = []
    rows = connection.execute(
        """SELECT c.id, n.mid FROM cards c
             JOIN decks d ON d.id = c.did
             JOIN notes n ON n.id = c.nid
            WHERE d.name LIKE '%1 Expressions%1 Fluency%'""").fetchall()
    for (cid, mid) in rows:
        if int(mid) == hub_apkg.EXAMPLE_MODEL_ID:
            continue
        if int(mid) == POOL_MODEL_ID and int(cid) in deferred:
            continue
        problems.append(f"card {cid}: unexpected model {mid} in fluency lane")
    return problems


def verify_no_quarantine_conversion(connection, manifest: dict) -> list[str]:
    """No C1 quarantine member note and no join-key card note may carry a
    target model."""
    problems = []
    note_ids = {int(n) for g in manifest["quarantine"]["c1_groups"]
                for n in g["member_note_ids"]}
    note_ids.update(int(c["note_id"])
                    for c in manifest["quarantine"]["join_key_cards"])
    for nid in sorted(note_ids):
        row = connection.execute(
            "SELECT mid FROM notes WHERE id=?", (nid,)).fetchone()
        if row and int(row[0]) in (hub_apkg.HUB_MODEL_ID,
                                   hub_apkg.EXAMPLE_MODEL_ID):
            problems.append(f"quarantined note {nid} carries target model")
    return problems


def verify_hub_guid_uniqueness(connection, manifest: dict) -> list[str]:
    problems = []
    for hub in manifest["hubs"]:
        count = connection.execute(
            "SELECT COUNT(*) FROM notes WHERE guid=?",
            (hub["target_guid"],)).fetchone()[0]
        if int(count) != 1:
            problems.append(
                f"hub guid {hub['target_guid']} resolves to {count} notes")
    return problems


def bindings_rows(connection, manifest: dict, profile_key: str) -> list[dict]:
    """Post-migration binding export (design §3.5 / migration phase 6):
    one row per target note with its card ids."""
    rows = []
    for conv in manifest["conversions"]:
        cards = connection.execute(
            "SELECT id, ord FROM cards WHERE nid=? ORDER BY ord",
            (int(conv["note_id"]),)).fetchall()
        rows.append({
            "profile_key": profile_key, "note_id": int(conv["note_id"]),
            "note_guid": conv["note_guid"], "card_kind": "fluency",
            "model_version": str(hub_apkg.EXAMPLE_MODEL_ID),
            "expression_id": conv["expression_id"],
            "example_id": conv["example_id"],
            "cards": [{"card_id": int(c[0]), "ord": int(c[1])}
                      for c in cards],
            "active": True,
        })
    for hub in manifest["hubs"]:
        note = connection.execute(
            "SELECT id FROM notes WHERE guid=?",
            (hub["target_guid"],)).fetchone()
        if note is None:
            continue
        cards = connection.execute(
            "SELECT id, ord FROM cards WHERE nid=? ORDER BY ord",
            (int(note[0]),)).fetchall()
        rows.append({
            "profile_key": profile_key, "note_id": int(note[0]),
            "note_guid": hub["target_guid"], "card_kind": "hub",
            "model_version": str(hub_apkg.HUB_MODEL_ID),
            "expression_id": hub["expression_id"], "example_id": None,
            "cards": [{"card_id": int(c[0]), "ord": int(c[1])}
                      for c in cards],
            "active": True,
        })
    return rows
