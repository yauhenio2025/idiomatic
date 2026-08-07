"""F4 interference cards: deterministic tests with synthetic private data.

The real pair banks are private operator data and deliberately never appear in
this repository.  Every linguistic-looking value below is an invented token or
phrase used only to exercise the compiler contract.
"""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import html
import json
from pathlib import Path
import sqlite3
import unicodedata
import zipfile

import httpx
import pytest

from idiomatic.grammar import f4 as f4_module
from idiomatic.grammar.apkg import build_grammar_apkg
from idiomatic.grammar.curriculum import topic_by_key, topics_for, unit_seed_rows
from idiomatic.grammar.f4 import (
    PAIR_FIELDS,
    TOPIC_BY_LANG,
    choose_candidates,
    closed_choice_order,
    compute_pair_key,
    pair_to_item,
    parse_pair_bank,
    production_signature,
)


# Literal values are intentional: changing production constants and this
# regression together must not make a frozen-model break pass unnoticed.
_FROZEN_MODEL_ID = 1_820_130_001
_FROZEN_MODEL_NAME = "Idiomatic Grammar Drill v1"
_FROZEN_FIELDS = [
    "ItemId",
    "Lang",
    "Topic",
    "TenseLabel",
    "Symbol",
    "Sentence",
    "Answer",
    "SentenceFull",
    "GlossEn",
    "Why",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]

_PAIR_FIELDS = [
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
]

_F4_TOPICS = {
    "es": (
        "es_interference_f4",
        "10 Interferencias",
        "Contrastes entre lenguas",
    ),
    "pt": (
        "pt_interference_f4",
        "10 Interferência",
        "Contrastes entre línguas",
    ),
    "fr": (
        "fr_interference_f4",
        "10 Interférences",
        "Contrastes entre langues",
    ),
    "it": (
        "it_interference_f4",
        "10 Interferenze",
        "Contrasti tra lingue",
    ),
}


def _pair(**overrides) -> dict:
    """One wholly invented ten-field private-bank row."""
    row = {
        "target_lang": "fr",
        "source_lang": "es",
        "concept_en": "synthetic marker",
        "correct_target": "névira",
        "false_form": "sóval",
        "source_form": "sovalén",
        "category": "interference_lexical",
        "why": "The invented target token differs from the invented source token.",
        "occurrences": 3,
        "attested": True,
    }
    row.update(overrides)
    return row


def _meta(rows: list[dict], **overrides) -> dict:
    target = rows[0]["target_lang"] if rows else "fr"
    by_source: dict[str, dict[str, int]] = {}
    for row in rows:
        counts = by_source.setdefault(
            row["source_lang"],
            {"pairs": 0, "attested": 0, "family_extensions": 0},
        )
        counts["pairs"] += 1
        if row["attested"]:
            counts["attested"] += 1
        else:
            counts["family_extensions"] += 1
    categories = {
        row["category"]: {
            "definition": "Synthetic category definition.",
            "registry_category_analogs": [row["category"]],
            "attested_registry_categories_observed": (
                [row["category"]] if row["attested"] else []
            ),
        }
        for row in rows
    }
    meta = {
        "schema_version": 1,
        "built": "2030-01-02",
        "target_lang": target,
        "target_variety": "Synthetic test variety",
        "commission_quota": "synthetic",
        "schema": list(_PAIR_FIELDS),
        "category_policy": "Synthetic categories do not alter source counts.",
        "category_vocabulary": categories,
        "provenance": ["synthetic test fixture"],
        "counts": {
            "pairs": len(rows),
            "attested": sum(row["attested"] for row in rows),
            "family_extensions": sum(not row["attested"] for row in rows),
            "represented_source_rows": sum(row["occurrences"] for row in rows),
            "by_source_lang": by_source,
        },
        "attestation_semantics": "Synthetic exact-pair semantics.",
        "occurrence_semantics": "Synthetic represented-row semantics.",
        "reviewed_projections": [],
        "source_audit_policy": "Synthetic source labels are illustrative only.",
        "validation_notes": ["All fixture forms are invented."],
    }
    meta.update(overrides)
    return meta


def _bank_text(rows: list[dict], *, meta_overrides: dict | None = None) -> str:
    meta = _meta(rows, **(meta_overrides or {}))
    return json.dumps([{"_meta": meta}, *rows], ensure_ascii=False)


def _db_pair(*, row_id: int = 11, **overrides) -> dict:
    row = _pair(**overrides)
    row.update(
        {
            "id": row_id,
            "schema_version": 1,
            "pair_key": compute_pair_key(
                1,
                row["target_lang"],
                row["false_form"],
                row["correct_target"],
            ),
            "personal_error_id": row_id + 1_000 if row["attested"] else None,
            "grammar_item_id": None,
            "needs_conversion": True,
            "status": "active",
        }
    )
    return row


def test_pair_field_contract_and_valid_bank_parse():
    assert list(PAIR_FIELDS) == _PAIR_FIELDS

    source = _pair()
    rows, errors = parse_pair_bank(_bank_text([source]))

    assert errors == []
    assert len(rows) == 1
    parsed = rows[0]
    for field in _PAIR_FIELDS:
        assert parsed[field] == source[field]
    assert parsed["schema_version"] == 1
    assert parsed["pair_key"] == compute_pair_key(
        1, source["target_lang"], source["false_form"], source["correct_target"]
    )
    assert parsed.get("projection_registry_id") is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_lang", None),
        ("source_lang", 7),
        ("concept_en", ["not", "text"]),
        ("correct_target", False),
        ("false_form", {"bad": "type"}),
        ("source_form", 4.2),
        ("category", None),
        ("why", ["bad"]),
        ("occurrences", True),  # bool is an int subclass in Python
        ("occurrences", 1.5),
        ("attested", 1),
    ],
)
def test_parse_rejects_wrong_pair_field_types(field: str, value):
    row = _pair()
    row[field] = value
    _, errors = parse_pair_bank(_bank_text([row]))
    assert errors


def test_parse_requires_exact_ten_pair_fields():
    missing = _pair()
    missing.pop("source_form")
    _, missing_errors = parse_pair_bank(_bank_text([missing]))
    assert missing_errors

    extra = _pair()
    extra["private_note"] = "must not be accepted"
    _, extra_errors = parse_pair_bank(_bank_text([extra]))
    assert extra_errors


@pytest.mark.parametrize(
    "row",
    [
        _pair(source_lang="fr"),
        _pair(attested=True, occurrences=0),
        _pair(attested=False, occurrences=1),
        _pair(correct_target="   "),
        _pair(false_form="\t"),
        _pair(correct_target="névira", false_form="ne\u0301vira"),
        _pair(correct_target="né___vira"),
        _pair(correct_target="névira / luméta"),
        _pair(correct_target="névira | luméta"),
    ],
    ids=[
        "same-language",
        "attested-zero",
        "extension-positive",
        "empty-answer",
        "empty-false-form",
        "nfc-equal-forms",
        "preexisting-blank",
        "slash-alternative",
        "pipe-alternative",
    ],
)
def test_parse_rejects_pair_invariant_violations(row: dict):
    _, errors = parse_pair_bank(_bank_text([row]))
    assert errors


def test_parse_requires_meta_header_first_and_consistent():
    row = _pair()

    for payload in (
        json.dumps([row], ensure_ascii=False),
        json.dumps([row, {"_meta": _meta([row])}], ensure_ascii=False),
        json.dumps([{"_meta": _meta([row])}, {"_meta": _meta([row])}], ensure_ascii=False),
        json.dumps({"_meta": _meta([row]), "rows": [row]}, ensure_ascii=False),
    ):
        _, errors = parse_pair_bank(payload)
        assert errors

    _, target_errors = parse_pair_bank(
        _bank_text([row], meta_overrides={"target_lang": "it"})
    )
    assert target_errors

    bad_counts = _meta([row])
    bad_counts["counts"] = {**bad_counts["counts"], "pairs": 99}
    _, count_errors = parse_pair_bank(
        json.dumps([{"_meta": bad_counts}, row], ensure_ascii=False)
    )
    assert count_errors

    bad_schema = _meta([row])
    bad_schema["schema"] = list(reversed(_PAIR_FIELDS))
    _, schema_errors = parse_pair_bank(
        json.dumps([{"_meta": bad_schema}, row], ensure_ascii=False)
    )
    assert schema_errors


def test_parse_rejects_duplicate_canonical_tuple_after_nfc():
    first = _pair(correct_target="mévori", false_form="sóval")
    second = _pair(
        correct_target="me\u0301vori",
        false_form="so\u0301val",
        source_form="another invented cue",
    )

    _, errors = parse_pair_bank(_bank_text([first, second]))
    assert errors
    assert any("duplicate" in error.lower() for error in errors)


def test_parse_preserves_decomposed_storage_while_identity_uses_nfc():
    decomposed_correct = "ne\u0301vira"
    decomposed_false = "so\u0301val"
    source = _pair(
        correct_target=decomposed_correct,
        false_form=decomposed_false,
    )

    rows, errors = parse_pair_bank(_bank_text([source]))

    assert errors == []
    assert rows[0]["correct_target"] == decomposed_correct
    assert rows[0]["false_form"] == decomposed_false
    assert rows[0]["pair_key"] == compute_pair_key(1, "fr", "sóval", "névira")


def test_parse_rejects_duplicate_keys_and_nonstandard_json_without_value_leakage():
    private_marker = "synthetic-secret-zorél"
    duplicate_key = (
        '[{"_meta":{"schema_version":1,"schema_version":1}},'
        f'{{"private":"{private_marker}"}}]'
    )
    _, duplicate_errors = parse_pair_bank(duplicate_key)
    assert duplicate_errors
    assert all(private_marker not in error for error in duplicate_errors)

    payload = _bank_text([_pair()]).replace('"occurrences": 3', '"occurrences": NaN')
    _, constant_errors = parse_pair_bank(payload)
    assert constant_errors
    assert all("névira" not in error and "sóval" not in error for error in constant_errors)


def test_parse_maps_a_declared_projection_without_copying_registry_text():
    row = _pair(
        target_lang="de",
        source_lang="ru",
        correct_target="Névor talim",
        false_form="Névora talim",
        source_form="Нэвор талим",
        category="adjective_ending",
    )
    projection = {
        "false_form": row["false_form"],
        "correct_target": row["correct_target"],
        "registry_id": 9_001_337,
        "reason": "Synthetic substring projection.",
    }

    rows, errors = parse_pair_bank(
        _bank_text([row], meta_overrides={"reviewed_projections": [projection]})
    )

    assert errors == []
    assert rows[0]["projection_registry_id"] == 9_001_337


def test_parse_rejects_unused_or_unattested_projection():
    row = _pair()
    unrelated = {
        "false_form": "zorélo",
        "correct_target": "zoréla",
        "registry_id": 9_001_338,
        "reason": "Synthetic unrelated projection.",
    }
    _, unused_errors = parse_pair_bank(
        _bank_text([row], meta_overrides={"reviewed_projections": [unrelated]})
    )
    assert unused_errors

    extension = _pair(attested=False, occurrences=0)
    matching = {
        "false_form": extension["false_form"],
        "correct_target": extension["correct_target"],
        "registry_id": 9_001_339,
        "reason": "Synthetic extension must not project.",
    }
    _, extension_errors = parse_pair_bank(
        _bank_text([extension], meta_overrides={"reviewed_projections": [matching]})
    )
    assert extension_errors


def test_pair_key_is_compact_utf8_sha256_and_nfc_stable():
    decomposed_false = "so\u0301val"
    decomposed_correct = "ne\u0301vira"
    expected_payload = json.dumps(
        [1, "fr", "sóval", "névira"],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    expected = hashlib.sha256(expected_payload).hexdigest()

    assert compute_pair_key(1, "fr", decomposed_false, decomposed_correct) == expected
    assert compute_pair_key(1, "fr", "sóval", "névira") == expected
    assert len(expected) == 64
    assert compute_pair_key(2, "fr", "sóval", "névira") != expected
    assert compute_pair_key(1, "fr", "sóvale", "névira") != expected


def test_production_signature_uses_tokens_and_extended_graphemes():
    # The first token contains a decomposed accent but is two graphemes, not
    # three code points. A same-shape distractor forces one visible grapheme.
    answer = "a\u0301b tor"
    signature = production_signature(answer, ["áb tor", "xy zem"])

    assert signature is not None
    assert "á" in unicodedata.normalize("NFC", signature)
    assert "2" in signature and "3" in signature
    assert "a\u0301" not in signature
    assert "___" not in signature


def test_production_signature_falls_back_for_duplicate_or_full_reveal():
    assert production_signature("mévori", ["mévori", "mévori"]) is None
    # Same length and common prefix; only the final grapheme distinguishes the
    # answers, so the complete target would have to be shown.
    assert production_signature("navor", ["navor", "navos"]) is None
    assert production_signature("x", ["x", "y"]) is None
    assert production_signature("névira", ["luméta"]) is None


def test_production_signature_distinguishes_shape_without_revealing_answer():
    signature = production_signature("luméta", ["luméta", "névira", "tal"])
    assert signature is not None
    assert "luméta" not in signature
    assert "6" in signature


def test_production_signature_uses_zero_prefix_when_shape_is_already_unique():
    signature = production_signature("zoréla", ["zoréla", "tal", "névor tim"])

    assert signature == "······ · 6 letters"


@pytest.mark.parametrize(
    "answer",
    [
        "👩\u200d💻zor",
        "ka\u200cza",
    ],
    ids=["zwj", "zwnj"],
)
def test_production_signature_accepts_joiners_in_extended_graphemes(answer: str):
    signature = production_signature(answer, [answer, "tal"])

    assert signature is not None
    assert answer not in signature
    assert "4 letters" in signature


@pytest.mark.parametrize("answer", ["\u200d", "\u200cword", "word\u200d"])
def test_production_signature_rejects_bare_or_dangling_joiners(answer: str):
    assert production_signature(answer, [answer, "tal"]) is None


def test_closed_choice_order_uses_pair_key_most_significant_bit():
    correct = "névira tal"
    false = "sóval tal"

    assert closed_choice_order("0" + "a" * 63, correct, false) == (correct, false)
    assert closed_choice_order("7" + "a" * 63, correct, false) == (correct, false)
    assert closed_choice_order("8" + "a" * 63, correct, false) == (false, correct)
    assert closed_choice_order("f" + "a" * 63, correct, false) == (false, correct)


def test_closed_choice_order_rejects_bad_identity_or_equal_candidates():
    with pytest.raises(ValueError, match="pair key"):
        closed_choice_order("not-a-digest", "névira", "sóval")
    with pytest.raises(ValueError, match="must differ"):
        closed_choice_order("0" * 64, "névira", "ne\u0301vira")


def _assert_item_contract(item: dict, row: dict) -> None:
    assert item["lang"] == row["target_lang"]
    assert item["topic"] == TOPIC_BY_LANG[row["target_lang"]]
    assert item["fmt"] == "f4"
    assert item["answer"] == row["correct_target"]
    assert item["gloss_en"] == row["concept_en"]
    assert item["why_en"] == row["why"]
    assert item["status"] == "verified"
    assert item["infinitive"] is None
    assert item["mood"] is None
    assert item["tense"] is None
    assert item["person"] is None
    assert item["sentence"].count("___") == 1
    assert f"[{row['source_lang'].upper()}]" in item["sentence"]
    assert f"[{row['target_lang'].upper()}]" in item["sentence"]
    assert row["source_form"] in item["sentence"]
    assert item["meta"]["pair_key"] == row["pair_key"]


def test_pair_mapping_shape_a_is_receiving_language_production():
    row = _db_pair(
        attested=False,
        occurrences=0,
        correct_target="névira",
        false_form="sóval",
        source_form="sovalén",
    )
    other = _db_pair(
        row_id=12,
        attested=False,
        occurrences=0,
        correct_target="luméta",
        false_form="dorim",
        source_form="dorimé",
    )

    item = pair_to_item(row, [row, other])

    _assert_item_contract(item, row)
    assert item["meta"]["shape"] == "A"
    assert row["correct_target"] not in item["sentence"]
    assert row["false_form"] not in item["sentence"]
    assert item["meta"]["signature"]


def test_pair_mapping_shape_b_intercepts_only_attested_recurrent_form():
    row = _db_pair(
        occurrences=12,
        correct_target="névira",
        false_form="sóval",
        source_form="sovalén",
    )
    other = _db_pair(
        row_id=12,
        correct_target="luméta",
        false_form="dorim",
        source_form="dorimé",
    )

    item = pair_to_item(row, [row, other])

    _assert_item_contract(item, row)
    assert item["meta"]["shape"] == "B"
    assert row["false_form"] in item["sentence"]
    assert row["correct_target"] not in item["sentence"]


def test_pair_mapping_shape_b_threshold_is_frozen_at_five_occurrences():
    assert f4_module.SHAPE_B_MIN_OCCURRENCES == 5
    decoy = _db_pair(
        row_id=30,
        occurrences=1,
        correct_target="luméta",
        false_form="dorim",
        source_form="dorimé",
    )
    below = _db_pair(
        row_id=31,
        occurrences=4,
        correct_target="névira",
        false_form="sóval",
        source_form="sovalén",
    )
    at_threshold = _db_pair(
        row_id=32,
        occurrences=5,
        correct_target="torima",
        false_form="torimo",
        source_form="torimé",
    )

    assert pair_to_item(below, [below, decoy])["meta"]["shape"] == "A"
    assert (
        pair_to_item(at_threshold, [at_threshold, decoy])["meta"]["shape"] == "B"
    )


def test_shape_c_category_vocabulary_is_frozen():
    expected = {
        "verb_prep_regime",
        "preposition_selection",
        "relative_pronoun",
        "negation",
        "word_order",
    }
    assert f4_module.CLOSED_CHOICE_CATEGORIES == expected

    for index, category in enumerate(sorted(expected), 1):
        row = _db_pair(
            row_id=100 + index,
            category=category,
            correct_target=f"navar ti lum{index}",
            false_form=f"navar su lum{index}",
            source_form=f"naver sur lum{index}",
        )
        assert pair_to_item(row, [row])["meta"]["shape"] == "C"


@pytest.mark.parametrize("first_nibble", ["0", "f"])
def test_pair_mapping_shape_c_has_two_unmarked_candidates(first_nibble: str):
    row = _db_pair(
        category="verb_prep_regime",
        correct_target="navar ti lum",
        false_form="navar su lum",
        source_form="naver sur lum",
    )
    row["pair_key"] = first_nibble + row["pair_key"][1:]

    item = pair_to_item(row, [row])

    _assert_item_contract(item, row)
    assert item["meta"]["shape"] == "C"
    assert row["correct_target"] in item["sentence"]
    assert row["false_form"] in item["sentence"]
    assert "choose:" in item["sentence"]
    expected = closed_choice_order(
        row["pair_key"], row["correct_target"], row["false_form"]
    )
    assert f"{expected[0]} / {expected[1]}" in item["sentence"]


def test_pair_mapping_routes_unsafe_production_signature_to_shape_c():
    row = _db_pair(correct_target="navor", false_form="sóval")
    collision = _db_pair(
        row_id=12,
        correct_target="navos",
        false_form="luméta",
        source_form="lumetén",
    )

    item = pair_to_item(row, [row, collision])

    assert item["meta"]["shape"] == "C"
    assert row["correct_target"] in item["sentence"]
    assert row["false_form"] in item["sentence"]


@pytest.mark.parametrize(
    ("attested", "occurrences", "expected_shape"),
    [(False, 0, "A"), (True, 5, "B")],
)
def test_pair_mapping_rejects_malformed_pair_key_for_production_shapes(
    attested: bool,
    occurrences: int,
    expected_shape: str,
):
    row = _db_pair(
        attested=attested,
        occurrences=occurrences,
        correct_target="zoréla",
        false_form="talim",
        source_form="talimé",
    )
    decoy = _db_pair(
        row_id=12,
        correct_target="névor tim",
        false_form="dorim",
        source_form="dorimé",
    )
    assert pair_to_item(row, [row, decoy])["meta"]["shape"] == expected_shape

    row["pair_key"] = "not-a-sha256-digest"
    with pytest.raises(ValueError, match="pair key"):
        pair_to_item(row, [row, decoy])


@pytest.mark.parametrize(
    "row",
    [
        _db_pair(
            row_id=61,
            attested=False,
            occurrences=0,
            concept_en="synthetic zoréla marker",
            correct_target="zoréla",
            false_form="talim",
            source_form="talimé",
        ),
        _db_pair(
            row_id=62,
            attested=True,
            occurrences=5,
            correct_target="luméta",
            false_form="mis-luméta",
            source_form="dorimé",
        ),
    ],
    ids=["shape-a-concept-leak", "shape-b-false-form-leak"],
)
def test_pair_mapping_routes_production_front_answer_leaks_to_shape_c(row: dict):
    decoy = _db_pair(
        row_id=63,
        correct_target="névor tim",
        false_form="sóval",
        source_form="soválen",
    )

    item = pair_to_item(row, [row, decoy])

    assert item["meta"]["shape"] == "C"
    assert item["meta"]["signature"] is None
    assert "choose:" in item["sentence"]
    assert row["correct_target"] in item["sentence"]
    assert row["false_form"] in item["sentence"]


def test_pair_mapping_carries_source_revision_metadata():
    revised_at = datetime(2030, 1, 2, 3, 4, 5, 678_901, tzinfo=UTC)
    row = _db_pair(
        attested=False,
        occurrences=0,
        correct_target="zoréla",
        false_form="talim",
        source_form="talimé",
    )
    row["updated_at"] = revised_at
    decoy = _db_pair(
        row_id=12,
        correct_target="névor tim",
        false_form="dorim",
        source_form="dorimé",
    )

    item = pair_to_item(row, [row, decoy])

    assert item["meta"]["source_revision"] == revised_at.isoformat()


def test_choose_candidates_filters_clean_rows_and_ranks_deterministically():
    extension = _db_pair(
        row_id=1,
        attested=False,
        occurrences=0,
        correct_target="extora",
        false_form="extoro",
    )
    recurrent = _db_pair(
        row_id=2,
        occurrences=8,
        correct_target="recuria",
        false_form="recurio",
    )
    dirty_linked = _db_pair(
        row_id=3,
        occurrences=3,
        correct_target="mudéra",
        false_form="mudéro",
    )
    dirty_linked["grammar_item_id"] = 903
    clean_linked = _db_pair(
        row_id=4,
        occurrences=99,
        correct_target="cleara",
        false_form="clearo",
    )
    clean_linked.update({"grammar_item_id": 904, "needs_conversion": False})
    retired = _db_pair(
        row_id=5,
        occurrences=100,
        correct_target="retira",
        false_form="retiro",
    )
    retired["status"] = "retired"

    rows = [extension, dirty_linked, clean_linked, retired, recurrent]

    assert [row["id"] for row in choose_candidates(rows, 10)] == [2, 3, 1]
    assert [row["id"] for row in choose_candidates(rows, 2)] == [2, 3]
    assert choose_candidates(rows, 0) == []
    assert choose_candidates(rows, -1) == []


def test_choose_candidates_is_idempotent_and_supports_pre_dirty_flag_rows():
    row = _db_pair(row_id=21, occurrences=2)
    assert [candidate["id"] for candidate in choose_candidates([row], 1)] == [21]

    row["needs_conversion"] = False
    row["grammar_item_id"] = 921
    assert choose_candidates([row], 1) == []

    legacy_unlinked = dict(row)
    legacy_unlinked.pop("needs_conversion")
    legacy_unlinked["grammar_item_id"] = None
    assert [candidate["id"] for candidate in choose_candidates([legacy_unlinked], 1)] == [
        21
    ]
    legacy_unlinked["grammar_item_id"] = 921
    assert choose_candidates([legacy_unlinked], 1) == []


def test_choose_candidates_uses_pair_key_then_id_as_stable_tiebreaks():
    later_key = _db_pair(row_id=1, occurrences=2)
    earlier_key = _db_pair(row_id=99, occurrences=2)
    later_key["pair_key"] = "f" * 64
    earlier_key["pair_key"] = "0" * 64

    selected = choose_candidates([later_key, earlier_key], 2)
    assert [row["id"] for row in selected] == [99, 1]


@pytest.mark.asyncio
async def test_ingest_staged_batches_good_payload_and_marks_corrupt(monkeypatch):
    good_rows = [
        _pair(
            correct_target="névira",
            false_form="sóval",
            source_form="sovalén",
            occurrences=4,
        ),
        _pair(
            correct_target="luméta",
            false_form="dorim",
            source_form="dorimé",
            occurrences=0,
            attested=False,
        ),
    ]
    staged = [
        {"id": 71, "payload": _bank_text(good_rows)},
        {"id": 72, "payload": "this is not a JSON bank"},
    ]
    upserted: list[list[dict]] = []
    marked: list[tuple[int, str]] = []

    async def fetch_staged():
        return staged

    async def upsert(rows: list[dict]):
        upserted.append(rows)
        return len(rows)

    async def mark(staging_id: int, *, note: str):
        marked.append((staging_id, note))

    monkeypatch.setattr(f4_module.db, "fetch_unprocessed_f4_staging", fetch_staged)
    monkeypatch.setattr(f4_module.db, "upsert_f4_pairs", upsert)
    monkeypatch.setattr(f4_module.db, "mark_f4_staging", mark)

    result = await f4_module.ingest_staged(batch_size=1)

    assert [len(batch) for batch in upserted] == [2]
    assert [row["correct_target"] for batch in upserted for row in batch] == [
        "névira",
        "luméta",
    ]
    assert marked[0][0] == 71 and "ok" in marked[0][1]
    assert marked[1][0] == 72 and "corrupt" in marked[1][1]
    assert result is not None
    assert result["ingested"] == 2
    assert result["upserted"] == 2


@pytest.mark.asyncio
async def test_ingest_staged_marks_attestation_poison_and_handles_empty(monkeypatch):
    row = _pair()
    marked: list[tuple[int, str]] = []

    async def fetch_poison():
        return [{"id": 81, "payload": _bank_text([row])}]

    async def reject_attestation(rows: list[dict]):
        assert len(rows) == 1
        raise ValueError("private values must not escape")

    async def mark(staging_id: int, *, note: str):
        marked.append((staging_id, note))

    monkeypatch.setattr(f4_module.db, "fetch_unprocessed_f4_staging", fetch_poison)
    monkeypatch.setattr(f4_module.db, "upsert_f4_pairs", reject_attestation)
    monkeypatch.setattr(f4_module.db, "mark_f4_staging", mark)

    result = await f4_module.ingest_staged()

    assert result == {"ingested": 0, "upserted": 0}
    assert marked == [(81, "corrupt: attestation validation failed")]
    assert "private values must not escape" not in marked[0][1]

    async def fetch_empty():
        return []

    monkeypatch.setattr(f4_module.db, "fetch_unprocessed_f4_staging", fetch_empty)
    assert await f4_module.ingest_staged() is None
    with pytest.raises(ValueError, match="positive"):
        await f4_module.ingest_staged(batch_size=0)


@pytest.mark.asyncio
async def test_convert_scans_past_collisions_until_n_successes(monkeypatch):
    rows = [
        _db_pair(
            row_id=1,
            occurrences=9,
            category="verb_prep_regime",
            correct_target="navar ti lum",
            false_form="navar su lum",
            source_form="naver sur lum",
        ),
        _db_pair(
            row_id=2,
            occurrences=8,
            category="verb_prep_regime",
            correct_target="telar di mon",
            false_form="telar a mon",
            source_form="teler à mon",
        ),
        _db_pair(
            row_id=3,
            occurrences=7,
            category="verb_prep_regime",
            correct_target="sivar de nor",
            false_form="sivar en nor",
            source_form="siver en nor",
        ),
    ]
    attempted: list[int] = []

    async def fetch_pairs(lang: str):
        assert lang == "fr"
        return rows

    async def upsert_item(pair_id: int, item: dict, *, batch: str):
        attempted.append(pair_id)
        assert item["fmt"] == "f4"
        assert item["lang"] == "fr"
        assert batch.startswith("f4-")
        return None if pair_id == 1 else 900 + pair_id

    monkeypatch.setattr(f4_module.db, "fetch_active_f4_pairs", fetch_pairs)
    monkeypatch.setattr(f4_module.db, "upsert_f4_grammar_item", upsert_item)

    result = await f4_module.convert("fr", 2)

    assert attempted == [1, 2, 3]
    assert result["converted"] == 2
    assert result["skipped"] == 1


@pytest.mark.asyncio
async def test_convert_rejects_unshipped_language_and_zero_is_a_noop(monkeypatch):
    with pytest.raises(ValueError, match="unsupported"):
        await f4_module.convert("de", 1)

    async def should_not_fetch(lang: str):
        raise AssertionError(f"unexpected fetch for {lang}")

    monkeypatch.setattr(f4_module.db, "fetch_active_f4_pairs", should_not_fetch)
    assert await f4_module.convert("fr", 0) == {
        "converted": 0,
        "skipped": 0,
        "examples": [],
    }


def test_f4_topics_are_final_four_language_units_and_german_is_absent():
    assert TOPIC_BY_LANG == {lang: values[0] for lang, values in _F4_TOPICS.items()}
    seeds = {row["key"]: row for row in unit_seed_rows()}

    for lang, (key, cluster, label) in _F4_TOPICS.items():
        topic = topic_by_key(key)
        assert topic is not None
        assert topics_for(lang)[-1] == topic
        assert (topic.lang, topic.key, topic.cluster) == (lang, key, cluster)
        assert topic.label == label
        assert topic.symbol == "⇄"
        assert topic.mood == topic.tense == ""
        assert topic.verify == "f4"
        assert topic.verbs == []

        seed = seeds[key]
        assert seed["lang"] == lang
        assert seed["cluster"] == cluster
        assert seed["label"] == label
        assert seed["symbol"] == "⇄"
        assert seed["status"] == "active"

    assert "de" not in TOPIC_BY_LANG
    assert topic_by_key("de_interference_f4") is None
    assert all(topic.verify != "f4" for topic in topics_for("de"))
    assert "de_interference_f4" not in seeds


def _render_plain(template: str, fields: dict[str, str]) -> str:
    for name, value in fields.items():
        template = template.replace("{{" + name + "}}", value)
    return template


def test_f4_apkg_keeps_frozen_model_guid_subdeck_and_all_shape_directions(
    tmp_path: Path,
):
    pairs = {
        "A": _db_pair(
            row_id=41,
            attested=False,
            occurrences=0,
            correct_target="zoréla",
            false_form="vorem",
            source_form="talimé",
        ),
        "B": _db_pair(
            row_id=42,
            attested=True,
            occurrences=8,
            correct_target="lumétara",
            false_form="dorim",
            source_form="dorimé",
        ),
        "C": _db_pair(
            row_id=43,
            attested=True,
            occurrences=3,
            category="verb_prep_regime",
            correct_target="navar ti lum",
            false_form="navar su lum",
            source_form="naver sur lum",
        ),
    }
    rows = list(pairs.values())
    item_ids = {"A": 901, "B": 902, "C": 903}
    items = []
    for shape, pair in pairs.items():
        item = {**pair_to_item(pair, rows), "id": item_ids[shape]}
        assert item["meta"]["shape"] == shape
        items.append(item)

    topic = topic_by_key(items[0]["topic"])
    assert topic is not None
    out = tmp_path / "synthetic-f4.apkg"

    count = build_grammar_apkg(
        out_path=out,
        lang="fr",
        items=items,
        topic_labels={topic.key: (topic.label, topic.symbol)},
        topic_clusters={topic.key: topic.cluster},
    )
    assert count == 3

    unpacked = tmp_path / "unpacked"
    with zipfile.ZipFile(out) as package:
        package.extract("collection.anki2", unpacked)
    with sqlite3.connect(unpacked / "collection.anki2") as con:
        note_rows = con.execute("SELECT guid, flds FROM notes").fetchall()
        models = json.loads(con.execute("SELECT models FROM col").fetchone()[0])
        decks = json.loads(con.execute("SELECT decks FROM col").fetchone()[0])

    assert len(note_rows) == 3
    fields_by_id: dict[int, dict[str, str]] = {}
    guid_by_id: dict[int, str] = {}
    for guid, field_blob in note_rows:
        values = field_blob.split("\x1f")
        assert len(values) == 14
        fields = dict(zip(_FROZEN_FIELDS, values, strict=True))
        item_id = int(fields["ItemId"])
        fields_by_id[item_id] = fields
        guid_by_id[item_id] = guid

    for item_id in item_ids.values():
        expected_guid = hashlib.sha1(
            f"idiomatic-grammar::fr::{item_id}".encode()
        ).hexdigest()[:16]
        assert guid_by_id[item_id] == expected_guid

    assert set(models) == {str(_FROZEN_MODEL_ID)}
    model = models[str(_FROZEN_MODEL_ID)]
    assert int(model["id"]) == _FROZEN_MODEL_ID
    assert model["name"] == _FROZEN_MODEL_NAME
    assert [field["name"] for field in model["flds"]] == _FROZEN_FIELDS
    assert len(model["tmpls"]) == 1
    assert any(
        deck["name"] == "FR French::2 Grammar::10 Interférences"
        for deck in decks.values()
    )

    template = model["tmpls"][0]
    assert "{{Sentence}}" in template["qfmt"]
    assert "{{Answer}}" not in template["qfmt"]
    assert "{{Answer}}" in template["afmt"]
    assert "{{SentenceFull}}" in template["afmt"]

    for shape, pair in pairs.items():
        fields = fields_by_id[item_ids[shape]]
        sentence = html.unescape(fields["Sentence"])
        assert fields["Lang"] == "fr"
        assert fields["Topic"] == "fr_interference_f4"
        assert fields["TenseLabel"] == "Contrastes entre langues"
        assert fields["Symbol"] == "⇄"
        assert pair["source_form"] in sentence
        assert sentence.count("___") == 1
        assert fields["Answer"] == pair["correct_target"]
        assert f"<b>{pair['correct_target']}</b>" in fields["SentenceFull"]
        assert fields["GlossEn"] == "synthetic marker"
        assert fields["Why"] == pair["why"]
        assert fields["Extra1"] == fields["Extra2"] == ""
        assert fields["Extra3"] == fields["Extra4"] == ""

        front = html.unescape(_render_plain(template["qfmt"], fields))
        back = html.unescape(_render_plain(template["afmt"], fields))
        assert "[ES]" in front and pair["source_form"] in front
        assert pair["correct_target"] in back
        assert pair["why"] in back
        if shape in {"A", "B"}:
            assert pair["correct_target"] not in front
        else:
            assert "choose:" in front
            assert pair["correct_target"] in front
            assert pair["false_form"] in front

    assert pairs["A"]["false_form"] not in fields_by_id[901]["Sentence"]
    assert pairs["B"]["false_form"] in fields_by_id[902]["Sentence"]


def test_private_f4_bank_files_are_absent_from_public_code_and_tests():
    repo = Path(__file__).resolve().parents[1]
    forbidden = [
        *sorted((repo / "idiomatic" / "grammar" / "data").rglob("f4_pairs_*.json")),
        *sorted((repo / "tests").rglob("f4_pairs_*.json")),
    ]
    assert forbidden == []


@pytest.mark.asyncio
async def test_admin_f4_upload_validates_then_stages_exactly_one_blob(monkeypatch):
    from idiomatic import api

    payload = _bank_text([_pair(attested=False, occurrences=0)])
    calls: list[tuple[str, int]] = []

    async def stage(body: str, n_rows: int) -> int:
        calls.append((body, n_rows))
        return 73

    monkeypatch.setattr(api.db, "stage_f4_pairs", stage)
    api.app.dependency_overrides[api.authed_admin] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            response = await client.post(
                "/admin/f4-pairs-upload",
                content=payload.encode("utf-8"),
            )
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)

    assert response.status_code == 200
    assert response.json() == {
        "staged": 1,
        "staging_id": 73,
        "target_lang": "fr",
        "note": "ingested by the cron container on its next tick",
    }
    assert calls == [(payload, 1)]


@pytest.mark.asyncio
async def test_admin_f4_upload_errors_do_not_echo_private_forms(monkeypatch):
    from idiomatic import api

    sentinel = "PRIVATE-SYNTHETIC-SENTINEL"
    invalid = _pair(
        source_lang="fr",
        source_form=sentinel,
        attested=False,
        occurrences=0,
    )

    async def must_not_stage(_body: str, _n_rows: int) -> int:
        raise AssertionError("invalid private bank must not be staged")

    monkeypatch.setattr(api.db, "stage_f4_pairs", must_not_stage)
    api.app.dependency_overrides[api.authed_admin] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            response = await client.post(
                "/admin/f4-pairs-upload",
                content=_bank_text([invalid]).encode("utf-8"),
            )
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)

    assert response.status_code == 400
    assert sentinel not in response.text
    assert response.json()["detail"]["n_errors"] >= 1


@pytest.mark.asyncio
async def test_admin_f4_convert_is_bounded_and_excludes_german(monkeypatch):
    from idiomatic import api

    calls: list[tuple[str, int]] = []

    async def convert(lang: str, n: int) -> dict:
        calls.append((lang, n))
        return {"converted": 2, "skipped": 0, "examples": []}

    monkeypatch.setattr(f4_module, "convert", convert)
    api.app.dependency_overrides[api.authed_admin] = lambda: None
    try:
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            valid = await client.post(
                "/admin/f4-convert", params={"lang": "fr", "n": 2}
            )
            german = await client.post(
                "/admin/f4-convert", params={"lang": "de", "n": 2}
            )
            oversized = await client.post(
                "/admin/f4-convert", params={"lang": "fr", "n": 201}
            )
    finally:
        api.app.dependency_overrides.pop(api.authed_admin, None)

    assert valid.status_code == 200
    assert valid.json()["converted"] == 2
    assert german.status_code == oversized.status_code == 400
    assert calls == [("fr", 2)]


@pytest.mark.asyncio
async def test_admin_f4_routes_require_admin_auth(monkeypatch):
    from types import SimpleNamespace

    from idiomatic import api

    monkeypatch.setattr(
        api, "get_settings", lambda: SimpleNamespace(admin_token="test-secret")
    )
    transport = httpx.ASGITransport(app=api.app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test",
    ) as client:
        response = await client.get("/admin/f4-pairs-status")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_f4_generation_mode_never_calls_the_llm(monkeypatch):
    from idiomatic.grammar import generate, service

    async def forbidden_generation(*_args, **_kwargs):
        raise AssertionError("F4 must not enter LLM generation")

    rebuilt: list[str] = []

    async def rebuild(lang: str) -> dict:
        rebuilt.append(lang)
        return {"lang": lang, "cards": 0}

    monkeypatch.setattr(generate, "generate_batch", forbidden_generation)
    monkeypatch.setattr(service, "rebuild_grammar_deck", rebuild)

    await service.run_generation("fr", 12, "fr_interference_f4")

    state = service.get_state()
    assert state["topics_total"] == state["topics_done"] == 0
    assert state["accepted"] == state["rejected"] == 0
    assert rebuilt == ["fr"]


@pytest.mark.asyncio
async def test_f4_items_ship_but_are_excluded_from_mixed_language_tts(
    monkeypatch, tmp_path: Path,
):
    from types import SimpleNamespace

    from idiomatic.grammar import service

    f4_item = {
        "id": 91,
        "lang": "fr",
        "topic": "fr_interference_f4",
        "fmt": "f4",
        "infinitive": None,
        "sentence": "[ES] talimé · [FR] ___  (····)",
        "answer": "zoréla",
        "gloss_en": "synthetic marker",
        "why_en": "Synthetic contrast.",
    }
    ordinary_item = {
        "id": 92,
        "lang": "fr",
        "topic": "fr_present",
        "fmt": "cloze",
        "infinitive": "synthétiser",
        "sentence": "Je ___ (synthétiser).",
        "answer": "synthétise",
        "gloss_en": "I synthesize.",
        "why_en": "Synthetic ordinary card.",
    }
    audio_calls: list[list[int]] = []
    packaged: list[list[int]] = []

    async def fetch_items(_lang: str, *, status: str) -> list[dict]:
        assert status == "verified"
        return [f4_item, ordinary_item]

    async def ensure_audio(items: list[dict], _lang: str) -> dict[int, str]:
        audio_calls.append([item["id"] for item in items])
        return {}

    def build(*, out_path: Path, items: list[dict], **_kwargs) -> int:
        packaged.append([item["id"] for item in items])
        out_path.write_bytes(b"synthetic package")
        return len(items)

    async def upsert_apkg(**_kwargs) -> int:
        return 501

    monkeypatch.setattr(service.db, "fetch_grammar_items", fetch_items)
    monkeypatch.setattr(service.db, "upsert_pool_apkg", upsert_apkg)
    monkeypatch.setattr(service.grammar_audio, "ensure_audio", ensure_audio)
    monkeypatch.setattr(service, "build_grammar_apkg", build)
    monkeypatch.setattr(
        service, "get_settings", lambda: SimpleNamespace(data_dir=str(tmp_path))
    )

    result = await service.rebuild_grammar_deck("fr")

    assert audio_calls == [[ordinary_item["id"]]]
    assert packaged == [[f4_item["id"], ordinary_item["id"]]]
    assert result == {"lang": "fr", "cards": 2, "apkg_id": 501, "with_audio": 0}
