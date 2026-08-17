"""Batch course generation: unit registries, DE plan schema, selector.

All selector tests run on synthetic fixture chapters — the sealed corpus
is machine-local book content and never enters the repo or the suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from idiomatic.anki_tree import anki_root
from idiomatic.grammar import course
from tools import course_select
from tools.course_build_pilot import PILOT_ROOT, resolve_deck_root


# ---------------------------------------------------------------------------
# Course unit registries
# ---------------------------------------------------------------------------


class TestDeUnitsRegistry:
    def test_covers_all_21_chapters_uniquely(self) -> None:
        assert len(course.DE_UNITS) == 21
        chapters = [chapter for chapter, _label in course.DE_UNITS.values()]
        assert sorted(chapters) == list(range(1, 22))

    def test_labels_are_deck_segments(self) -> None:
        labels = [label for _chapter, label in course.DE_UNITS.values()]
        assert len(set(labels)) == 21
        for label in labels:
            assert label.strip() == label and label
            assert "::" not in label

    def test_kasus_is_the_shipped_pilot(self) -> None:
        assert course.DE_UNITS["kasus"] == (2, "Kasus (cases)")

    def test_unit_keys_are_valid_unit_slugs(self) -> None:
        import re
        for key in course.DE_UNITS:
            assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key)

    def test_de_unit_helper(self) -> None:
        assert course.de_unit("praepositionen") == \
            (18, "Präpositionen (prepositions)")
        with pytest.raises(ValueError, match="unknown DE course unit"):
            course.de_unit("nope")


ROMANCE_REGISTRIES = {
    "fr": (
        course.FR_UNITS,
        list(range(1, 18)),
        ("subjonctif", (11, "Subjonctif & modaux (subjunctive, modal verbs, exclamatives)")),
    ),
    "es": (
        course.ES_UNITS,
        [1, 2, 3, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
         19, 20, 23, 24, 26, 27, 28, 30, 32],
        ("ser-estar", (23, "Ser, estar & haber (B&B 33-34)")),
    ),
    "it": (
        course.IT_UNITS,
        list(range(1, 22)),
        ("tempi-modi", (14, "Tempi & modi: congiuntivo, condizionale, passato (M&R 15)")),
    ),
    "pt": (
        course.PT_UNITS,
        [1, 2, 4, 5, 6, 7, 8, 10, 11, 13, 14, 15, 17, 18, 19, 20,
         21, 22, 23, 24, 25, 26, 27, 28],
        ("infinitivo", (19, "Infinitivo (incl. infinitivo pessoal)")),
    ),
}


class TestRomanceUnitsRegistry:
    @pytest.mark.parametrize(
        ("lang", "registry", "chapters", "anchor"),
        [(lang, *values) for lang, values in ROMANCE_REGISTRIES.items()],
    )
    def test_registry_matches_curated_workbook_chapter_order(
        self,
        lang: str,
        registry: dict[str, tuple[int, str]],
        chapters: list[int],
        anchor: tuple[str, tuple[int, str]],
    ) -> None:
        assert list(chapter for chapter, _label in registry.values()) == chapters
        assert registry[anchor[0]] == anchor[1]
        assert course.COURSE_UNITS[lang] is registry

    @pytest.mark.parametrize(
        "registry", [values[0] for values in ROMANCE_REGISTRIES.values()]
    )
    def test_keys_and_labels_obey_course_contract(
        self, registry: dict[str, tuple[int, str]]
    ) -> None:
        import re

        labels = [label for _chapter, label in registry.values()]
        assert len(labels) == len(set(labels))
        assert all(label and label.strip() == label and "::" not in label
                   for label in labels)
        assert all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key)
                   for key in registry)

    def test_course_unit_helper(self) -> None:
        assert course.course_unit("fr", "prepositions") == \
            (13, "Prépositions (prepositions)")
        assert course.course_unit("pt", "ser-estar") == \
            (23, "Ser, estar & ficar")
        with pytest.raises(ValueError, match="unknown ES course unit"):
            course.course_unit("es", "nope")
        with pytest.raises(ValueError, match="unknown course language"):
            course.course_unit("xx", "nope")


# ---------------------------------------------------------------------------
# Plan schema
# ---------------------------------------------------------------------------


def _plan_block(block: int = 1, card_seq: int = 2, **overrides: object) -> dict:
    raw: dict = {
        "block": block,
        "card_seq": card_seq,
        "exercise_sets": ["3"],
        "max_items": None,
        "hammer_refs": ["18.1.1"],
        "note": "fixture block",
    }
    raw.update(overrides)
    return raw


def _plan_dict(blocks: list[dict] | None = None, **overrides: object) -> dict:
    raw: dict = {
        "lang": "de",
        "unit": "praepositionen",
        "chapter": 18,
        "unit_label": "Präpositionen (prepositions)",
        "blocks": blocks if blocks is not None else [_plan_block()],
    }
    raw.update(overrides)
    return raw


def _write_plan(tmp_path: Path, data: dict, *,
                name: str = "de_praepositionen.plan.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class TestLoadPlan:
    def test_happy_path(self, tmp_path: Path) -> None:
        plan = course_select.load_plan(_write_plan(tmp_path, _plan_dict(
            blocks=[
                _plan_block(1, 2, exercise_sets=["3", "5:key"], max_items=14),
                _plan_block(2, 4, exercise_sets=[5]),
            ]
        )))
        assert plan.unit == "praepositionen"
        assert plan.chapter == 18
        assert plan.unit_label == "Präpositionen (prepositions)"
        assert plan.blocks[0].sets == ((3, "html"), (5, "key"))
        assert plan.blocks[0].max_items == 14
        assert plan.blocks[1].sets == ((5, "html"),)
        assert plan.blocks[1].max_items is None

    def test_rejects_unknown_unit(self, tmp_path: Path) -> None:
        data = _plan_dict(unit="foo")
        with pytest.raises(course_select.PlanError,
                           match="unknown DE course unit"):
            course_select.load_plan(
                _write_plan(tmp_path, data, name="de_foo.plan.json")
            )

    def test_spanish_plan_uses_spanish_registry(self, tmp_path: Path) -> None:
        data = _plan_dict(
            lang="es",
            unit="sustantivos",
            chapter=1,
            unit_label="Sustantivos (nouns; B&B 1-2)",
            blocks=[_plan_block(1, 1, hammer_refs=["1.2"])],
        )
        plan = course_select.load_plan(
            _write_plan(tmp_path, data, name="es_sustantivos.plan.json")
        )
        assert plan.lang == "es"
        assert plan.unit == "sustantivos"
        assert plan.chapter == 1

    def test_rejects_language_filename_mismatch(self, tmp_path: Path) -> None:
        with pytest.raises(course_select.PlanError,
                           match="lang field must match"):
            course_select.load_plan(
                _write_plan(tmp_path, _plan_dict(),
                            name="es_praepositionen.plan.json")
            )

    def test_rejects_chapter_mismatch(self, tmp_path: Path) -> None:
        with pytest.raises(course_select.PlanError,
                           match="chapter must be 18"):
            course_select.load_plan(
                _write_plan(tmp_path, _plan_dict(chapter=17))
            )

    def test_rejects_unit_label_mismatch(self, tmp_path: Path) -> None:
        with pytest.raises(course_select.PlanError, match="unit_label"):
            course_select.load_plan(
                _write_plan(tmp_path, _plan_dict(unit_label="Prepositions"))
            )

    def test_rejects_duplicate_or_descending_blocks(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(course_select.PlanError,
                           match="unique ascending"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(1, 2), _plan_block(1, 3)]
            )))
        with pytest.raises(course_select.PlanError,
                           match="unique ascending"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(2, 2), _plan_block(1, 3)]
            )))

    def test_rejects_bad_card_seq(self, tmp_path: Path) -> None:
        with pytest.raises(course_select.PlanError,
                           match="card_seq must be an integer >= 1"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(1, 0)]
            )))
        with pytest.raises(course_select.PlanError,
                           match="duplicate card_seq"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(1, 2), _plan_block(2, 2)]
            )))

    def test_rejects_bad_set_token(self, tmp_path: Path) -> None:
        with pytest.raises(course_select.PlanError,
                           match="invalid exercise set"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(1, 2, exercise_sets=["x7"])]
            )))

    def test_rejects_empty_sets_and_bad_refs(self, tmp_path: Path) -> None:
        with pytest.raises(course_select.PlanError,
                           match="exercise_sets must be nonempty"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(1, 2, exercise_sets=[])]
            )))
        with pytest.raises(course_select.PlanError, match="hammer_refs"):
            course_select.load_plan(_write_plan(tmp_path, _plan_dict(
                blocks=[_plan_block(1, 2, hammer_refs=["not-a-ref"])]
            )))


# ---------------------------------------------------------------------------
# Selector end-to-end on a synthetic fixture chapter
# ---------------------------------------------------------------------------


def _item(no: object, **overrides: object) -> dict:
    raw: dict = {
        "item_no": str(no),
        "prompt": "Er wohnt an___ d___ Ecke.",
        "full_solution_html": "Er wohnt <mark>an der</mark> Ecke.",
        "answer_key_raw": "Er wohnt an der Ecke.",
        "alternatives": [],
        "flags": [],
        "key_page": 210,
    }
    raw.update(overrides)
    return raw


def _chapter_fixture() -> dict:
    return {
        "chapter": 18,
        "title": "Prepositions",
        "hammer_sections": [
            "Section 18.1.1",
            "Sections 18.2–18.3 and Chapter 2",
        ],
        "exercises": [
            {
                "ex_no": 3,
                "instruction": "Add   the missing prepositions.",
                "page": 150,
                "items": [
                    _item(1),
                    _item(2, flags=["reconstructed-by-model"]),
                    _item(3, full_solution_html=
                          "Er wohnt <mark>an der</mark> ___ Ecke."),
                    _item(4, prompt="an der Ecke wohnen (er)",
                          full_solution_html=
                          "<mark>an der Ecke wohnen</mark> stimmt.",),
                    _item(5),
                    _item(6),
                ],
            },
            {
                "ex_no": 5,
                "instruction": "Construct sentences.",
                "page": 152,
                "items": [
                    _item(1, answer_key_raw="Wir fahren in die Stadt."),
                    _item(2, answer_key_raw="Noch ___ offen"),
                ],
            },
        ],
    }


class TestSelectUnit:
    def _plan(self, tmp_path: Path, blocks: list[dict]):
        return course_select.load_plan(
            _write_plan(tmp_path, _plan_dict(blocks=blocks))
        )

    def test_explode_gate_cap_order(self, tmp_path: Path) -> None:
        plan = self._plan(tmp_path, [
            _plan_block(1, 2, exercise_sets=["3"], max_items=2),
            _plan_block(2, 3, exercise_sets=["5:key"],
                        hammer_refs=["18.2", "Ch. 2"]),
        ])
        payload, report = course_select.select_unit(plan, _chapter_fixture())
        # gate: item 2 flagged, item 3 has a blank placeholder, item 4
        # duplicates prompt text inside <mark>; 1, 5, 6 survive; the cap
        # keeps the first two in book order.
        block1 = payload["blocks"][0]
        assert block1["block"] == 2  # output block = card_seq
        assert [e["id"] for e in block1["exercises"]] == \
            ["pgg-c18-e03-i1", "pgg-c18-e03-i5"]
        assert report["capped"] and "first 2 of 3" in report["capped"][0]
        # key mode: printed answer key wrapped in one whole-sentence mark;
        # the unusable key (blank placeholder) is skipped.
        block2 = payload["blocks"][1]
        assert [e["id"] for e in block2["exercises"]] == ["pgg-c18-e05-i1"]
        assert block2["exercises"][0]["solution_html"] == \
            "<mark>Wir fahren in die Stadt.</mark>"
        assert any("unusable answer key" in line
                   for line in report["skipped"])
        # instruction whitespace collapsed, refs + source_ref shaped
        first = block1["exercises"][0]
        assert first["instruction"] == "Add the missing prepositions."
        assert first["hammer_refs"] == ["18.1.1"]
        assert first["source_ref"] == \
            "PGG Kap. 18, Üb. 3, Nr. 1 (S. 150; Key S. 210)"
        assert first["provenance"] == "book-verbatim"

    def test_output_shape_is_accepted_by_course_parser(
        self, tmp_path: Path
    ) -> None:
        plan = self._plan(tmp_path, [_plan_block(1, 2, exercise_sets=["3"])])
        payload, _report = course_select.select_unit(
            plan, _chapter_fixture()
        )
        exercises = course.parse_exercises_payload(
            payload, name="de_praepositionen.exercises.json"
        )
        assert exercises[0].lang == "de"
        assert exercises[0].unit == "praepositionen"
        assert exercises[0].block == 2
        # and byte-shape via the file loader too
        path = tmp_path / "de_praepositionen.exercises.json"
        path.write_text(json.dumps(payload, ensure_ascii=False),
                        encoding="utf-8")
        assert len(course.parse_exercises_file(path)) == len(exercises)

    def test_spanish_payload_uses_language_metadata(
        self, tmp_path: Path
    ) -> None:
        plan = course_select.load_plan(_write_plan(
            tmp_path,
            _plan_dict(
                lang="es",
                unit="sustantivos",
                chapter=1,
                unit_label="Sustantivos (nouns; B&B 1-2)",
                blocks=[_plan_block(1, 1, hammer_refs=["1.2"])],
            ),
            name="es_sustantivos.plan.json",
        ))
        chapter = _chapter_fixture()
        chapter["chapter"] = 1
        chapter["title"] = "Nouns"
        chapter["hammer_sections"] = ["Section 1.2"]
        payload, _report = course_select.select_unit(plan, chapter)
        assert payload["lang"] == "es"
        first = payload["blocks"][0]["exercises"][0]
        assert first["id"] == "psg-c01-e03-i1"
        assert first["source_ref"] == \
            "PSG Ch. 1, Ex. 3, No. 1 (p. 150; key p. 210)"
        assert "Practising Spanish Grammar" in \
            payload["source"]["workbook"]

    def test_unknown_set_id_names_available_ids(self, tmp_path: Path) -> None:
        plan = self._plan(tmp_path, [_plan_block(1, 2, exercise_sets=["9"])])
        with pytest.raises(course_select.PlanError,
                           match=r"available set ids: 3, 5"):
            course_select.select_unit(plan, _chapter_fixture())

    def test_empty_block_after_gate_is_fatal(self, tmp_path: Path) -> None:
        chapter = _chapter_fixture()
        for item in chapter["exercises"][0]["items"]:
            item["flags"] = ["judgment-call"]
        plan = self._plan(tmp_path, [_plan_block(1, 2, exercise_sets=["3"])])
        with pytest.raises(course_select.PlanError,
                           match="empty after the hygiene gate"):
            course_select.select_unit(plan, chapter)

    def test_ref_must_appear_in_printed_headers(self, tmp_path: Path) -> None:
        plan = self._plan(
            tmp_path, [_plan_block(1, 2, hammer_refs=["19.4"])]
        )
        with pytest.raises(course_select.PlanError,
                           match="printed"):
            course_select.select_unit(plan, _chapter_fixture())

    def test_ref_inside_printed_section_range_is_accepted(
        self, tmp_path: Path
    ) -> None:
        plan = self._plan(
            tmp_path, [_plan_block(1, 2, hammer_refs=["18.2"])]
        )
        chapter = _chapter_fixture()
        chapter["hammer_sections"] = ["Sections 18.1–18.4"]
        payload, _report = course_select.select_unit(plan, chapter)
        assert payload["blocks"][0]["exercises"][0]["hammer_refs"] == [
            "18.2"
        ]

    def test_chapter_mismatch_is_fatal(self, tmp_path: Path) -> None:
        plan = self._plan(tmp_path, [_plan_block(1, 2)])
        chapter = _chapter_fixture()
        chapter["chapter"] = 17
        with pytest.raises(course_select.PlanError,
                           match="corpus chapter"):
            course_select.select_unit(plan, chapter)


# ---------------------------------------------------------------------------
# Production deck-name routing
# ---------------------------------------------------------------------------


class TestProductionRouting:
    def test_default_stays_on_pilot_root(self) -> None:
        assert resolve_deck_root(
            "de", "kasus", "Kasus (cases)", production=False
        ) == PILOT_ROOT

    def test_production_composes_from_anki_root(self) -> None:
        override = resolve_deck_root(
            "de", "kasus", "Kasus (cases)", production=True
        )
        assert override is None
        lesson_deck, exercise_deck = course.course_deck_names(
            "de", "Kasus (cases)", root_override=override
        )
        root = anki_root("de")
        assert lesson_deck == f"{root}::2 Grammar::Kasus (cases)::1 Lesson"
        assert exercise_deck == \
            f"{root}::2 Grammar::Kasus (cases)::2 Exercises"

    def test_production_rejects_label_mismatch(self) -> None:
        with pytest.raises(SystemExit, match="does not match"):
            resolve_deck_root("de", "kasus", "Cases", production=True)

    def test_production_rejects_unknown_unit(self) -> None:
        with pytest.raises(SystemExit, match="unknown DE course unit"):
            resolve_deck_root("de", "nope", "Whatever", production=True)

    def test_spanish_production_validates_its_registry(self) -> None:
        assert resolve_deck_root(
            "es", "sustantivos", "Sustantivos (nouns; B&B 1-2)",
            production=True,
        ) is None
        with pytest.raises(SystemExit, match="does not match ES_UNITS"):
            resolve_deck_root(
                "es", "sustantivos", "Sustantivos", production=True
            )


# ---------------------------------------------------------------------------
# The committed kasus plan parses against the registry
# ---------------------------------------------------------------------------


class TestCommittedPlans:
    def test_kasus_plan_is_valid(self) -> None:
        plan = course_select.load_plan(
            course_select.PLANS_DIR / "de_kasus.plan.json"
        )
        assert plan.chapter == 2
        assert [block.card_seq for block in plan.blocks] == \
            [3, 4, 5, 6, 8, 9, 10]

    def test_every_committed_plan_parses(self) -> None:
        plans = sorted(course_select.PLANS_DIR.glob("*.plan.json"))
        assert plans, "plans dir must at least carry de_kasus"
        for path in plans:
            course_select.load_plan(path)
