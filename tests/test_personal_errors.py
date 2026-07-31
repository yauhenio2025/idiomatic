"""Registry JSONL validation — deterministic, no DB."""

import json

from idiomatic.personal_errors import parse_jsonl


def _line(**over):
    d = {"lang": "fr", "kind": "error", "wrong": "en Berlin",
         "right": "à Berlin", "category": "preposition_selection",
         "why": "cities take à", "occurrences": 11,
         "first_seen": "2019-06-04", "last_seen": "2024-03-01",
         "sources": ["xlsx", "teachee"], "confidence": "high"}
    d.update(over)
    return json.dumps(d, ensure_ascii=False)


def test_parse_good_line():
    rows, errors = parse_jsonl(_line())
    assert not errors and len(rows) == 1
    r = rows[0]
    assert r["right_form"] == "à Berlin"
    assert r["occurrences"] == 11
    assert str(r["first_seen"]) == "2019-06-04"
    assert r["sources"] == ["xlsx", "teachee"]


def test_parse_rejects_bad_rows():
    cases = [
        _line(lang="xx"),
        _line(kind="mistake"),
        _line(category="not_a_category"),
        _line(right=""),
        _line(kind="error", wrong=None),
        _line(confidence="ultra"),
        "not json at all",
    ]
    rows, errors = parse_jsonl("\n".join(cases))
    assert rows == []
    assert len(errors) == len(cases)
    assert all("line" in e for e in errors)


def test_parse_tolerates_gaps_and_defaults():
    ok = json.dumps({"lang": "it", "kind": "vocab_gap",
                     "right": "la scadenza", "category": "vocabulary"})
    rows, errors = parse_jsonl(ok + "\n\n" + _line())
    assert not errors and len(rows) == 2
    assert rows[0]["wrong"] is None
    assert rows[0]["occurrences"] == 1
    assert rows[0]["first_seen"] is None
