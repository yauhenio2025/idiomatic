"""Autopilot logic tests — pure functions only (no network, no DB):
provider registry policy, the struggle computer over a fixture
collection, and the generation planner's ladder/budget behavior."""

import sqlite3
import time

import pytest

from idiomatic import genmedia
from idiomatic.rescue_autopilot import compute_struggles, plan_generations


# --- registry policy --------------------------------------------------------

def test_autopilot_providers_are_chinese_models_only():
    ap = genmedia.autopilot_providers()
    assert ap, "autopilot needs at least one approved provider"
    for key in ap:
        assert not key.startswith("nano-"), \
            "user directive: Nano Banana is manual-only"
    assert genmedia.DEFAULT_PROVIDER in ap


def test_every_provider_has_cost_and_adapter():
    for key, info in genmedia.PROVIDERS.items():
        assert info["usd_per_image"] > 0
        assert info["api"] in genmedia._ADAPTERS, key
        assert genmedia.estimate_image_cost(key) == info["usd_per_image"]


# --- struggle computer ------------------------------------------------------

NOW_MS = 1_754_000_000_000  # fixed for determinism


def _mk_collection(path, reviews):
    """Minimal anki-shaped sqlite: notes/cards/revlog + notetypes."""
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE notes (id INTEGER PRIMARY KEY, flds TEXT, tags TEXT);
        CREATE TABLE cards (id INTEGER PRIMARY KEY, nid INTEGER);
        CREATE TABLE revlog (id INTEGER PRIMARY KEY, cid INTEGER, ease INTEGER);
    """)
    for i, (fields, tags, eases) in enumerate(reviews, 1):
        con.execute("INSERT INTO notes VALUES (?, ?, ?)",
                    (i, "\x1f".join(fields), tags))
        con.execute("INSERT INTO cards VALUES (?, ?)", (i, i))
        for j, ease in enumerate(eases):
            con.execute("INSERT INTO revlog VALUES (?, ?, ?)",
                        (NOW_MS - 86400_000 * 2 - i * 1000 - j, i, ease))
    con.commit()
    con.close()


POOL_FIELDS = ["He gave up.", "Ele desistiu.", "", "[sound:x.mp3]",
               "desistir de", "to give up", "src"]


def test_compute_struggles_thresholds_and_aggregation(tmp_path):
    p = str(tmp_path / "c.anki2")
    _mk_collection(p, [
        (POOL_FIELDS, "youtube pt fluency-pool", [1, 1, 1, 3]),   # 3 fails
        (POOL_FIELDS[:1] + ["Outro."] + POOL_FIELDS[2:], "youtube pt x",
         [1, 3]),                                                  # same idiom +1
        (["a"] * 22, "youtube it", [1, 1, 1, 1]),                  # 21-field: ignored
        (POOL_FIELDS, "youtube xx", [1, 1, 1]),                    # no lang tag
    ])
    out = compute_struggles(p, min_fails_14d=3, now_ms=NOW_MS)
    assert len(out) == 1
    s = out[0]
    assert (s["lang"], s["idiom"]) == ("pt", "desistir de")
    assert s["fails_14d"] == 4 and s["gloss"] == "to give up"
    assert "Ele desistiu." in s["failed_sentences"]


def test_compute_struggles_respects_threshold(tmp_path):
    p = str(tmp_path / "c.anki2")
    _mk_collection(p, [(POOL_FIELDS, "youtube pt", [1, 3, 3])])
    assert compute_struggles(p, min_fails_14d=3, now_ms=NOW_MS) == []
    assert len(compute_struggles(p, min_fails_14d=1, now_ms=NOW_MS)) == 1


# --- planner ----------------------------------------------------------------

def _item(id, strike=1, status="active", anchor="a hook", fails=5):
    return {"id": id, "lang": "pt", "idiom": f"idiom-{id}", "strike": strike,
            "status": status, "anchor": anchor,
            "struggle_snapshot": {"fails_14d": fails}}


def test_planner_glyph_and_comic_for_anchored_item():
    plan, notes = plan_generations([_item(1)], {}, 10.0, 0.05)
    assert [(s["item_id"], s["format"]) for s in plan] == \
        [(1, "glyph"), (1, "comic")]
    assert notes == []


def test_planner_skips_comic_without_anchor_and_notes_it():
    plan, notes = plan_generations([_item(1, anchor="")], {}, 10.0, 0.05)
    assert [s["format"] for s in plan] == ["glyph"]
    assert any("anchor" in n for n in notes)


def test_planner_budget_hard_stop():
    items = [_item(i) for i in range(1, 6)]
    plan, notes = plan_generations(items, {}, 0.12, 0.05)
    assert len(plan) == 2                       # 0.05 + 0.05 fits, third doesn't
    assert any("budget stop" in n for n in notes)


def test_planner_skips_existing_live_assets_and_retry_cap():
    have = {1: [{"format": "glyph", "status": "draft"},
                {"format": "comic", "status": "rejected"},
                {"format": "comic", "status": "rejected"},
                {"format": "comic", "status": "rejected"}]}
    plan, notes = plan_generations([_item(1)], have, 10.0, 0.05)
    assert plan == []                           # glyph live, comic capped
    assert any("retry cap" in n for n in notes)


def test_planner_only_strike1_gets_comic_and_candidates_skipped():
    plan, _ = plan_generations(
        [_item(1, strike=2), _item(2, status="candidate")], {}, 10.0, 0.05)
    assert [(s["item_id"], s["format"]) for s in plan] == [(1, "glyph")]
