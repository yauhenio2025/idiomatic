"""Deterministic, network-free tests for the read-only legacy-estate audit."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pytest

from tools import legacy_estate_audit as audit


AUDITED_AT = "2026-08-08T11:02:53+08:00"


def _make_collection(path: Path) -> Path:
    path.parent.mkdir(parents=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE decks (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE notetypes (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE fields (ntid INTEGER, ord INTEGER, name TEXT);
        CREATE TABLE templates (ntid INTEGER, ord INTEGER, name TEXT);
        CREATE TABLE notes (
          id INTEGER PRIMARY KEY, mid INTEGER NOT NULL, tags TEXT NOT NULL,
          flds TEXT NOT NULL
        );
        CREATE TABLE cards (
          id INTEGER PRIMARY KEY, nid INTEGER NOT NULL, did INTEGER NOT NULL,
          ivl INTEGER NOT NULL, reps INTEGER NOT NULL, type INTEGER NOT NULL,
          queue INTEGER NOT NULL, odid INTEGER NOT NULL, odue INTEGER NOT NULL
        );
        CREATE TABLE revlog (id INTEGER PRIMARY KEY, cid INTEGER NOT NULL);
        """
    )
    decks = [
        (1, "EXCERCISES"),
        (2, "EXCERCISES\x1fES"),
        (3, "EXCERCISES\x1fES\x1fCONNECTING"),
        (4, "_tenses_old"),
        (5, "_tenses_old\x1ftenses_spanish_kolya"),
        (6, "_errors"),
        (7, "_errors\x1f_es_errors"),
        (8, "Empty"),
    ]
    connection.executemany("INSERT INTO decks VALUES (?,?)", decks)
    connection.executemany(
        "INSERT INTO notetypes VALUES (?,?)",
        [(10, "_Basic"), (11, "Basic-75519")],
    )
    connection.executemany(
        "INSERT INTO fields VALUES (?,?,?)",
        [(10, 0, "Front"), (10, 1, "Back"), (11, 0, "Front"), (11, 1, "Back")],
    )
    connection.executemany(
        "INSERT INTO templates VALUES (?,?,?)",
        [(10, 0, "Card 1"), (11, 0, "Card 1")],
    )
    connection.executemany(
        "INSERT INTO notes VALUES (?,?,?,?)",
        [
            (1, 10, "es", "Accordingly,\x1fEn consecuencia [sound:a.mp3]"),
            (2, 10, "es", "<b>Accordingly,</b>\x1fDe acuerdo"),
            (
                3,
                11,
                "es",
                "saber; _sp _present_subjunctive\x1fto know; sepa, sepas, sepa",
            ),
            (4, 10, "es", "Yo sabo\x1f"),
        ],
    )
    connection.executemany(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (101, 1, 3, 22, 5, 2, 2, 0, 0),
            (102, 2, 3, 0, 0, 0, 0, 0, 0),
            (103, 3, 5, 30, 10, 2, 2, 0, 0),
            (104, 4, 7, 2, 3, 2, 2, 0, 0),
        ],
    )
    connection.executemany(
        "INSERT INTO revlog VALUES (?,?)",
        [
            (1_700_000_000_000, 101),
            (1_700_000_001_000, 101),
            (1_700_000_002_000, 103),
            (1_700_000_003_000, 104),
            (1_700_000_004_000, 999),  # deleted card: cannot be deck-attributed
        ],
    )
    connection.commit()
    connection.close()
    return path


@pytest.fixture
def estate_copy(tmp_path: Path) -> tuple[Path, Path]:
    work_root = tmp_path / "legacy_estate_work"
    collection = _make_collection(work_root / "pull" / "collection.anki2")
    return work_root, collection


def _row(manifest: dict, path: str) -> dict:
    return next(row for row in manifest["rows"] if row["deck_path"] == path)


def _flag(row: dict, code: str, scope: str) -> dict:
    return next(
        flag for flag in row["quality_flags"] if flag["code"] == code and flag["scope"] == scope
    )


def _overlap(row: dict, kind: str, scope: str | None = None) -> list[dict]:
    return [
        value
        for value in row["overlap"]
        if value["kind"] == kind and (scope is None or value["scope"] == scope)
    ]


def _note(front: str, back: str) -> audit.NoteInfo:
    return audit.NoteInfo(
        mid=1,
        front=audit.normalize_text(front),
        back=audit.normalize_text(back),
        sound_tags=0,
        tag_langs=frozenset(),
    )


def _quality(note_info: dict[int, audit.NoteInfo], lang: str) -> dict[str, dict]:
    return {
        flag["code"]: flag
        for flag in audit._quality_flags(set(note_info), note_info, lang=lang, scope="direct")
    }


def test_manifest_has_hierarchy_history_audio_quality_overlap_and_verdicts(estate_copy):
    work_root, collection = estate_copy
    before = hashlib.sha256(collection.read_bytes()).hexdigest()
    manifest = audit.analyze_collection(
        collection,
        audited_at=AUDITED_AT,
        work_root=work_root,
    )
    after = hashlib.sha256(collection.read_bytes()).hexdigest()

    assert before == after == manifest["snapshot"]["source_sha256"]
    assert manifest["snapshot"]["quick_check"] == "ok"
    assert manifest["snapshot"]["audited_at"] == AUDITED_AT
    assert manifest["totals"] == {
        "deck_rows": 8,
        "top_level_decks": 4,
        "note_models": 2,
        "notes": 4,
        "cards": 4,
        "mature_cards": 2,
        "card_reps": 18,
        "review_rows": 5,
        "attributed_review_rows": 4,
        "orphaned_review_rows": 1,
        "last_review": "2023-11-14T22:13:24Z",
        "audio_notes": 1,
        "sound_tags": 1,
        "new_cards": 1,
        "learning_or_relearning_cards": 0,
        "review_state_cards": 3,
        "suspended_cards": 0,
        "filtered_deck_cards": 0,
    }

    root = _row(manifest, "EXCERCISES")
    assert root["parent_path"] is None and root["depth"] == 0
    assert root["lang"] == "es" and root["language_basis"] == "descendant-decks"
    assert root["direct_cards"] == 0
    assert root["subtree_notes"] == root["subtree_cards"] == 2
    assert root["subtree_mature"] == 1
    assert root["subtree_reps"] == 5 and root["subtree_reviews"] == 2
    assert root["subtree_audio_notes"] == root["subtree_sound_tags"] == 1
    assert root["subtree_last_review"] == "2023-11-14T22:13:21Z"
    assert root["proposed_verdict"] == "partial"
    assert "exercises_it_french_copy" in root["settled_facts"]

    connecting = _row(manifest, "EXCERCISES::ES::CONNECTING")
    assert _flag(connecting, "duplicate_front", "direct") == {
        "code": "duplicate_front",
        "scope": "direct",
        "count": 1,
        "details": "2 notes",
    }
    assert _flag(connecting, "conflicting_back", "direct")["count"] == 1
    roadmap = _overlap(connecting, "exercises2-roadmap")
    assert roadmap == [
        {
            "kind": "exercises2-roadmap",
            "status": "shipped",
            "scope": "subtree",
            "topic": "connecting",
            "details": "wave-1",
        }
    ]
    assert _overlap(connecting, "normalized-exercise-prompt", "direct")[0]["count"] == 2
    assert _overlap(connecting, "normalized-exercise-pair", "direct")[0]["count"] == 1

    tenses = _row(manifest, "_tenses_old::tenses_spanish_kolya")
    assert tenses["lang"] == "es"
    assert tenses["proposed_verdict"] == "already-covered"
    assert _overlap(tenses, "tenses-profiles") == [
        {
            "kind": "tenses-profiles",
            "status": "profiled",
            "scope": "subtree",
            "count": 1,
            "details": "top-60 verb×tense priors per language",
        }
    ]

    errors = _row(manifest, "_errors::_es_errors")
    assert errors["proposed_verdict"] == "import"
    assert _flag(errors, "empty_back", "direct")["count"] == 1
    assert _row(manifest, "Empty")["proposed_verdict"] == "skip"
    assert len(manifest["models"]) == 2
    assert {model["name"] for model in root["note_models"]} == {"_Basic"}


def test_manifest_and_markdown_are_deterministic_and_complete(estate_copy, tmp_path):
    work_root, collection = estate_copy
    first = audit.analyze_collection(collection, audited_at=AUDITED_AT, work_root=work_root)
    second = audit.analyze_collection(collection, audited_at=AUDITED_AT, work_root=work_root)
    assert audit.manifest_json(first) == audit.manifest_json(second)

    output = tmp_path / "artifacts"
    audit.write_artifacts(first, output)
    assert sorted(path.name for path in output.iterdir()) == [
        "DECKS.md",
        "MODELS.md",
        "SUMMARY.md",
        "manifest.json",
    ]
    loaded = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert len(loaded["rows"]) == 8
    decks = (output / "DECKS.md").read_text(encoding="utf-8")
    assert all(row["deck_path"] in decks for row in first["rows"])


def test_validation_refuses_outside_symlink_hardlink_and_active_wal(estate_copy, tmp_path):
    work_root, collection = estate_copy
    outside = _make_collection(tmp_path / "outside" / "collection.anki2")
    with pytest.raises(audit.AuditError, match="beneath"):
        audit.validate_collection_path(outside, work_root=work_root)

    symlink = work_root / "symlink.anki2"
    symlink.symlink_to(collection)
    with pytest.raises(audit.AuditError, match="symlink"):
        audit.validate_collection_path(symlink, work_root=work_root)

    hardlink = work_root / "hardlink.anki2"
    os.link(collection, hardlink)
    with pytest.raises(audit.AuditError, match="single-link"):
        audit.validate_collection_path(collection, work_root=work_root)
    hardlink.unlink()

    wal = Path(f"{collection}-wal")
    wal.write_bytes(b"active transaction state")
    with pytest.raises(audit.AuditError, match="non-empty SQLite sidecar"):
        audit.validate_collection_path(collection, work_root=work_root)


@pytest.mark.parametrize("value", ["2026-08-08", "not-a-date", ""])
def test_audited_at_requires_a_real_timezone(value):
    with pytest.raises(audit.AuditError, match="audited-at"):
        audit._parse_audited_at(value)


@pytest.mark.parametrize(
    ("path", "verdict"),
    [
        ("EXCERCISES::ES::CONNECTING", "already-covered"),
        ("EXCERCISES::ES::CONDITIONALS", "already-covered"),
        ("EXCERCISES::ES::TENSES", "import"),
        ("EXCERCISES::ES::FANCY_VOCAB", "import"),
        ("EXCERCISES::ES::COMMANDS", "partial"),
        ("EXCERCISES::ES::REFLEXIV", "partial"),
        ("EXCERCISES::PT::FALSE_FRIENDS", "skip"),
        ("EXCERCISES::ES", "partial"),
        ("EXCERCISES", "partial"),
    ],
)
def test_exercises_verdicts_follow_the_frozen_roadmap(path, verdict):
    accumulator = audit.DeckAccumulator(cards=1)
    assert audit._proposed_verdict(path, accumulator)[0] == verdict


def test_quality_flags_wrong_language_and_exact_front_back_are_conservative():
    for lang, markers in audit.WRONG_LANGUAGE_MARKERS.items():
        other_markers = set().union(
            *(
                candidate_markers
                for candidate, candidate_markers in audit.WRONG_LANGUAGE_MARKERS.items()
                if candidate != lang
            )
        )
        assert markers.isdisjoint(other_markers)

    notes = {
        1: _note("The media have no influence.", "Los medios no tienen influencia."),
        2: _note("The media have no influence.", "Os meios não têm influência."),
        3: _note("A platform", "Los tienen"),
        4: _note("Open source", "Open source"),
        5: _note("Internet", "Internet"),
    }
    flags = _quality(notes, "pt")

    assert flags["suspected_wrong_target_language_back"] == {
        "code": "suspected_wrong_target_language_back",
        "scope": "direct",
        "count": 1,
        "details": (
            "heuristic suspects by inferred back language: es=1; requires >=4 words, "
            ">=2 distinct markers, and no target-language marker"
        ),
    }
    assert flags["exact_front_back_suspect"]["count"] == 1
    assert ">=2 words" in flags["exact_front_back_suspect"]["details"]

    italian_paradigm = _quality(
        {
            1: _note(
                "accadere; _it_future",
                "to happen; esso, essa accadrà; essi, esse accadranno",
            )
        },
        "it",
    )
    assert "suspected_wrong_target_language_back" not in italian_paradigm


def test_quality_flags_only_the_documented_machine_english_patterns():
    notes = {
        1: _note("the Technological solutionism", "el solucionismo tecnológico"),
        2: _note("Recommend her that documentary!", "Recomiéndele ese documental."),
        3: _note(
            "The professor will explain her the theory",
            "La profesora le explicará la teoría.",
        ),
        4: _note(
            "The professor will explain the theory to her",
            "La profesora le explicará la teoría.",
        ),
        5: _note("Recommend that documentary to her!", "Recomiéndele ese documental."),
    }
    flag = _quality(notes, "es")["documented_machine_english_front_suspect"]

    assert flag["count"] == 3
    assert "explain-indirect-object=1" in flag["details"]
    assert "recommend-indirect-object=1" in flag["details"]
    assert "the-technological-solutionism=1" in flag["details"]


@pytest.mark.parametrize(
    ("lang", "front", "back", "safe_back"),
    [
        (
            "pt",
            "They have been championing the proposal for months.",
            "Os senhores têm defendido a proposta há meses.",
            "Eles têm defendido a proposta há meses.",
        ),
        (
            "es",
            "They've instructed us to publish the report.",
            "Nos ha pedido que publiquemos el informe.",
            "Nos han pedido que publiquemos el informe.",
        ),
    ],
)
def test_quality_flags_only_documented_subject_drift_patterns(lang, front, back, safe_back):
    assert _quality({1: _note(front, back)}, lang)["documented_subject_drift_suspect"]["count"] == 1
    assert "documented_subject_drift_suspect" not in _quality({1: _note(front, safe_back)}, lang)


@pytest.mark.parametrize(
    ("lang", "front", "back", "safe_back"),
    [
        ("es", "The nuclear fallout", "La caída nuclear", "La lluvia radiactiva"),
        ("fr", "to fail", "pour échouer", "échouer"),
        ("pt", "Accordingly,", "De acordo; assim sendo", "Por conseguinte"),
    ],
)
def test_quality_flags_only_documented_literal_translation_pairs(lang, front, back, safe_back):
    assert (
        _quality({1: _note(front, back)}, lang)["documented_literal_translation_trap"]["count"] == 1
    )
    assert "documented_literal_translation_trap" not in _quality({1: _note(front, safe_back)}, lang)


def test_grammar_content_index_and_overlap_are_exact_and_per_language(tmp_path):
    data_dir = tmp_path / "idiomatic" / "grammar" / "data"
    data_dir.mkdir(parents=True)
    for filenames in audit.GRAMMAR_BANK_FILES.values():
        for filename in filenames:
            (data_dir / filename).write_text("[]\n", encoding="utf-8")

    (data_dir / "es_verb_prep.json").write_text(
        json.dumps(
            [
                {
                    "en": "to depend on",
                    "trap": "metadata must not be indexed",
                    "example_es": "La plataforma procesa datos.",
                    "example_en": "The platform processes data.",
                }
            ]
        ),
        encoding="utf-8",
    )
    (data_dir / "es_muy_mucho.json").write_text(
        json.dumps(
            [
                {
                    "frame": "La afirmación es ___ difícil.",
                    "correct": "muy",
                    "rule_en": "Rule prose must not be indexed.",
                }
            ]
        ),
        encoding="utf-8",
    )
    (data_dir / "f2_es_pret_impf.json").write_text(
        json.dumps(
            [
                {
                    "sentence": "La autoridad supervisaba el proceso.",
                    "contrast_form": "La autoridad supervisó el proceso.",
                    "why": "Feedback must not be indexed.",
                }
            ]
        ),
        encoding="utf-8",
    )
    (data_dir / "pt_regencia_verbal.json").write_text(
        json.dumps(
            [
                {
                    "en": "to analyze",
                    "example_es": "A equipe analisou o relatório.",
                    "example_en": "The team analyzed the report.",
                }
            ]
        ),
        encoding="utf-8",
    )
    tenses_dir = tmp_path / "docs" / "research" / "tenses-profiles"
    tenses_dir.mkdir(parents=True)
    (tenses_dir / "tenses_priors.json").write_text('{"langs": {}}\n', encoding="utf-8")

    content = audit.load_content_index(tmp_path)
    assert audit.normalize_text("La afirmación es muy difícil.") in content.grammar_sentences["es"]
    assert (
        audit.normalize_text("Rule prose must not be indexed.") not in content.grammar_glosses["es"]
    )
    assert (
        audit.normalize_text("The platform processes data."),
        audit.normalize_text("La plataforma procesa datos."),
    ) in content.grammar_pairs["es"]

    notes = {
        1: _note("The platform processes data.", "La plataforma procesa datos."),
        2: _note("La afirmación es muy difícil.", "A grammar drill"),
        3: _note("La autoridad supervisaba el proceso.", "A bounded reading"),
        4: _note("A equipe analisou o relatório.", "The team analyzed the report."),
    }
    overlaps = audit._overlap_rows(
        deck_path="Grammar corpus",
        descendant_paths=("Grammar corpus",),
        lang="multi",
        direct_note_ids={1, 2},
        subtree_note_ids=set(notes),
        note_info=notes,
        content=content,
    )
    keyed = {(row["kind"], row["scope"], row.get("lang")): row["count"] for row in overlaps}
    assert keyed == {
        ("normalized-grammar-sentence", "direct", "es"): 2,
        ("normalized-grammar-gloss", "direct", "es"): 1,
        ("normalized-grammar-pair", "direct", "es"): 1,
        ("normalized-grammar-sentence", "subtree", "es"): 3,
        ("normalized-grammar-gloss", "subtree", "es"): 1,
        ("normalized-grammar-pair", "subtree", "es"): 1,
        ("normalized-grammar-sentence", "subtree", "pt"): 1,
        ("normalized-grammar-gloss", "subtree", "pt"): 1,
        ("normalized-grammar-pair", "subtree", "pt"): 1,
    }
