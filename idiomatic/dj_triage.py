"""DJ-C2 curation-triage console backing: evidence loader + projections.

The committed census artifact (docs/research/dj_census/triage_evidence.json,
commission docs/commissions/CODEX_DJ_C2_CURATION_TRIAGE.md) is the read-only
EVIDENCE. This module loads it for the boot seed and recomputes the
per-language due-minutes projection under the owner's current verdicts.

Nothing here applies a disposition to any Anki collection — verdicts are
stored server-side only and executed later in an owner-present collection
window (the executor lane).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EVIDENCE_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "research"
    / "dj_census"
    / "triage_evidence.json"
)

PROPOSALS = frozenset(
    {"keep-active", "suspend-reference", "sample-hardest", "owner-review"}
)
VERDICTS = frozenset(
    {"accept-proposal", "keep-active", "suspend-reference", "sample-hardest", "defer"}
)
SCOPE_KINDS = frozenset({"lane", "first_level_subdeck", "dormant_summary"})

# The census keeps N=50 hardest cards on its sample-hardest proposals; the
# same N backs the estimate when the owner chooses sample-hardest on a row
# the census proposed differently for (no per-card sample evidence there).
DEFAULT_SAMPLE_N = 50


class TriageEvidenceError(ValueError):
    """The committed evidence does not satisfy the console seed contract."""


def load_evidence(path: Path | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and validate the census artifact; flatten rows for the seed.

    The census generator owns the detailed metric contract.  This loader
    checks the identity and fields needed to seed and project safely:
    unique subtree paths, known proposals/scope kinds, and that every
    applied projection scope is an emitted row (the projection recompute
    depends on that decomposition).
    """

    source = Path(path) if path is not None else EVIDENCE_PATH
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TriageEvidenceError(f"cannot load {source}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TriageEvidenceError("evidence root must be an object")
    subtrees = payload.get("subtrees")
    projections = payload.get("language_projections")
    src = payload.get("source")
    if not isinstance(subtrees, list) or not subtrees:
        raise TriageEvidenceError("evidence needs a nonempty subtrees array")
    if not isinstance(projections, list) or not isinstance(src, dict):
        raise TriageEvidenceError(
            "evidence needs language_projections array and source object"
        )
    as_of = src.get("as_of_local")
    if not isinstance(as_of, str) or not as_of:
        raise TriageEvidenceError("source.as_of_local must be a nonempty string")

    seen: set[str] = set()
    for index, row in enumerate(subtrees):
        if not isinstance(row, dict):
            raise TriageEvidenceError(f"subtrees[{index}] must be an object")
        subtree = row.get("subtree")
        if not isinstance(subtree, str) or not subtree:
            raise TriageEvidenceError(f"subtrees[{index}].subtree must be nonempty")
        if subtree in seen:
            raise TriageEvidenceError(f"duplicate subtree {subtree!r}")
        seen.add(subtree)
        for field in ("card_state", "study_depth", "difficulty_signal",
                      "proposal", "due_load_projection"):
            if not isinstance(row.get(field), dict):
                raise TriageEvidenceError(f"{subtree}: missing {field} object")
        disposition = row["proposal"].get("disposition")
        if disposition not in PROPOSALS:
            raise TriageEvidenceError(
                f"{subtree}: invalid proposed disposition {disposition!r}"
            )
        if row.get("scope_kind") not in SCOPE_KINDS:
            raise TriageEvidenceError(
                f"{subtree}: invalid scope_kind {row.get('scope_kind')!r}"
            )

    applied: set[str] = set()
    for projection in projections:
        scopes = projection.get("due_cards_by_applied_scope") or {}
        for scope in scopes:
            if scope not in seen:
                raise TriageEvidenceError(
                    f"applied scope {scope!r} is not an emitted subtree"
                )
            applied.add(scope)

    rows = [_flatten(row, applied, as_of) for row in subtrees]
    meta = {k: payload.get(k) for k in
            ("report", "source", "methods", "planning_constants",
             "language_projections")}
    return meta, rows


def _flatten(row: dict[str, Any], applied: set[str], as_of: str) -> dict[str, Any]:
    """One census subtree entry -> one flat dj_triage seed row."""
    parts = row["subtree"].split("::")
    card_state = row["card_state"]
    study = row["study_depth"]
    difficulty = row["difficulty_signal"]
    proposal = row["proposal"]
    load = row["due_load_projection"]
    return {
        "subtree": row["subtree"],
        "language": row["language"],
        "lane": parts[1] if len(parts) > 1 else parts[0],
        "scope_kind": row["scope_kind"],
        "parent_subtree": row.get("parent_subtree"),
        "applied_scope": row["subtree"] in applied,
        "card_count": row["card_count"],
        "due_now": card_state["due_now"],
        "new_reservoir": card_state["new_reservoir"],
        "suspended_cards": card_state.get("suspended_cards", 0),
        "provenance_dominant": (row.get("provenance") or {}).get("dominant"),
        "reps": study.get("reps", 0),
        "distinct_studied_cards": study.get("distinct_studied_cards", 0),
        "recent_reps": study.get("recent_reps", 0),
        "last_touch_date": study.get("last_touch_date"),
        "easy_rate_pct": difficulty.get("easy_rate_pct"),
        "again_rate_pct": difficulty.get("again_rate_pct"),
        "median_ivl_mature_days": difficulty.get("median_ivl_mature_days"),
        "due_minutes_before": load["due_minutes_before"],
        "due_cards_before": load["due_cards_before"],
        "due_minutes_after_proposal": load["due_minutes_after_if_this_row_applied"],
        "due_cards_after_proposal": load["due_cards_after_if_this_row_applied"],
        "proposal_disposition": proposal["disposition"],
        "sample_n": proposal.get("sample_n"),
        "rationale": row["rationale"],
        "evidence": row,
        "source_as_of": as_of,
    }


# ---- projection under current verdicts -------------------------------------

def resolve_disposition(
    row: dict[str, Any], by_subtree: dict[str, dict[str, Any]],
) -> str | None:
    """Effective disposition for one row under the owner's verdicts.

    Most-specific wins, mirroring the census projection rule: the row's own
    verdict; otherwise a concrete verdict on the parent lane row cascades
    down.  'accept-proposal' anywhere resolves to the ROW's own census
    proposal (the census already proposed per-scope, most-specific).
    None/'defer' means undecided — projected unchanged, exactly like the
    census treats owner-review.
    """
    verdict = row.get("owner_verdict")
    if verdict in (None, "defer"):
        parent = by_subtree.get(row.get("parent_subtree") or "")
        parent_verdict = parent.get("owner_verdict") if parent else None
        if parent_verdict in (None, "defer"):
            return None
        verdict = parent_verdict
    if verdict == "accept-proposal":
        return row["proposal_disposition"]
    return verdict


def _after_load(row: dict[str, Any], disposition: str | None) -> tuple[float, int]:
    """Projected (due minutes, due cards) for one applied scope."""
    if disposition in (None, "keep-active", "owner-review"):
        return row["due_minutes_before"], row["due_cards_before"]
    if disposition == "suspend-reference":
        return 0.0, 0
    if disposition == "sample-hardest":
        if row["proposal_disposition"] == "sample-hardest":
            # The census computed this from real per-card sample evidence.
            return row["due_minutes_after_proposal"], row["due_cards_after_proposal"]
        due = row["due_cards_before"]
        if not due:
            return 0.0, 0
        kept = min(row.get("sample_n") or DEFAULT_SAMPLE_N, due)
        return row["due_minutes_before"] * kept / due, kept
    raise ValueError(f"unknown disposition {disposition!r}")


def project_languages(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-language due-load minutes: before, under current verdicts, and
    if every census proposal were accepted.

    Only applied-scope rows count — the census's most-specific decomposition,
    which reproduces its language_projections exactly (validated in tests).
    Dormant summaries and overlapping lane views never double-count.
    """
    by_subtree = {row["subtree"]: row for row in rows}
    languages: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not row.get("applied_scope"):
            continue
        entry = languages.setdefault(
            row["language"],
            {
                "language": row["language"],
                "before_minutes": 0.0,
                "before_due_cards": 0,
                "current_minutes": 0.0,
                "current_due_cards": 0,
                "proposal_minutes": 0.0,
                "proposal_due_cards": 0,
                "applied_scopes": 0,
                "undecided_scopes": 0,
            },
        )
        disposition = resolve_disposition(row, by_subtree)
        current_minutes, current_cards = _after_load(row, disposition)
        proposal_minutes, proposal_cards = _after_load(
            row, row["proposal_disposition"]
        )
        entry["before_minutes"] += row["due_minutes_before"]
        entry["before_due_cards"] += row["due_cards_before"]
        entry["current_minutes"] += current_minutes
        entry["current_due_cards"] += current_cards
        entry["proposal_minutes"] += proposal_minutes
        entry["proposal_due_cards"] += proposal_cards
        entry["applied_scopes"] += 1
        if disposition is None:
            entry["undecided_scopes"] += 1
    projections = sorted(languages.values(), key=lambda e: e["language"])
    for entry in projections:
        for key in ("before_minutes", "current_minutes", "proposal_minutes"):
            entry[key] = round(entry[key], 3)
    return projections
