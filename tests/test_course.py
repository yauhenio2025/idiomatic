"""Grammar Course tests: deterministic, with no network or DB."""

from __future__ import annotations

import html
import json
import sqlite3
import subprocess
import zipfile
from pathlib import Path

import pytest

from idiomatic.grammar import course
from idiomatic.grammar.exercises2 import MODEL_ID as X2_MODEL_ID
from idiomatic.grammar.podcast_cards import MODEL_ID as PODCAST_MODEL_ID


_FROZEN_LESSON_FIELDS = [
    "LessonId",
    "Unit",
    "Seq",
    "Lang",
    "FrontHTML",
    "BackHTML",
    "FrontAudio",
    "BackAudio",
    "FrontImage",
    "BackImage",
    "Extra1",
    "Extra2",
    "Extra3",
    "Extra4",
]

_FROZEN_EXERCISE_FIELDS = [
    "ItemId",
    "Lang",
    "Unit",
    "Block",
    "Instruction",
    "PromptHTML",
    "SolutionHTML",
    "AltsHTML",
    "SourceRef",
    "HammerRefs",
    "Provenance",
    "SolutionAudio",
    "Extra1",
    "Extra2",
    "Extra3",
]

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _frontmatter(*, series: str = "grammar-course-lesson", lang: str = "de",
                 unit: str = "kasus") -> str:
    return f"""---
series: {series}
lang: {lang}
unit: {unit}
title: "Fixture unit"
unit_label: "Kasus (cases)"
---
"""


def _card(seq: int, *, front_extra: str = "", refs: str = "2.1") -> str:
    return f"""[CARD]
TITLE: Front {seq}
REF: {refs}
Narrate front {seq}.
TL: Der Zug war nicht pünktlich.
{front_extra}[SIDE]
TITLE: Back {seq}
REF: {refs}
Narrate back {seq}.
SHOW: Back note {seq}
TL-: Der Zug war nicht pünktlich.
"""


def _lesson_source(n_cards: int = 8, **kwargs: str) -> str:
    cards = "".join(_card(seq) for seq in range(1, n_cards + 1))
    return _frontmatter(**kwargs) + "\n## SCRIPT\n" + cards


def _write_lesson(tmp_path: Path, source: str, *, lang: str = "de",
                  unit: str = "kasus") -> Path:
    path = tmp_path / f"{lang}_{unit}.md"
    path.write_text(source, encoding="utf-8")
    return path


def _exercise(item_id: str, **overrides: object) -> dict:
    raw: dict = {
        "id": item_id,
        "instruction": "Add the missing endings.",
        "prompt": "Wir sprachen mit Maria Simon, d___ Filmschauspielerin.",
        "solution_html":
            "Wir sprachen mit Maria Simon, <mark>der</mark> Filmschauspielerin.",
        "alternatives": [],
        "hammer_refs": ["2.6"],
        "source_ref": "PGG Kap. 2, Üb. 14, Nr. 1",
        "provenance": "book-verbatim",
    }
    raw.update(overrides)
    return raw


def _exercises_payload(blocks: dict[int, list[dict]], *, lang: str = "de",
                       unit: str = "kasus") -> dict:
    return {
        "lang": lang,
        "unit": unit,
        "blocks": [
            {"block": block, "exercises": items}
            for block, items in blocks.items()
        ],
    }


def _write_exercises(tmp_path: Path, payload: dict, *, lang: str = "de",
                     unit: str = "kasus") -> Path:
    path = tmp_path / f"{lang}_{unit}.exercises.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _block_enrichment(block: int = 1, **overrides: object) -> dict:
    raw: dict = {
        "block": block,
        "task_html": "Add the case ending.",
        "example_html": None,
    }
    raw.update(overrides)
    return raw


def _exercise_enrichment(item_id: str, **overrides: object) -> dict:
    raw: dict = {
        "id": item_id,
        "solution_en": "We spoke with Maria Simon, the film actress.",
        "why_en": "Apposition copies the case: <i>mit</i> takes the dative.",
        "solution_full_html": None,
    }
    raw.update(overrides)
    return raw


# A complete-production form of the default _exercise solution: glue added,
# the answer span still <mark>der</mark>, terminal punctuation present.
_FULL_SOLUTION = (
    "Gestern sprachen wir mit Maria Simon, "
    "<mark>der</mark> Filmschauspielerin."
)


def _enrichment_payload(blocks: list[dict], exercises: list[dict], *,
                        lang: str = "de", unit: str = "kasus",
                        contract: object = 2) -> dict:
    return {"lang": lang, "unit": unit, "contract": contract,
            "blocks": blocks, "exercises": exercises}


def _write_enrichment(tmp_path: Path, payload: dict, *, lang: str = "de",
                      unit: str = "kasus") -> Path:
    path = tmp_path / f"{lang}_{unit}.enrichment.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Frozen shape
# ---------------------------------------------------------------------------


class TestFrozenShape:
    def test_lesson_model_identity(self) -> None:
        assert course.LESSON_MODEL_ID == 1_820_190_001
        assert course.LESSON_FIELDS == _FROZEN_LESSON_FIELDS
        model = course.make_lesson_model()
        assert [field["name"] for field in model.fields] == _FROZEN_LESSON_FIELDS
        assert len(model.templates) == 1

    def test_exercise_model_identity(self) -> None:
        assert course.EXERCISE_MODEL_ID == 1_820_190_002
        assert course.EXERCISE_FIELDS == _FROZEN_EXERCISE_FIELDS
        model = course.make_exercise_model()
        assert [field["name"] for field in model.fields] == _FROZEN_EXERCISE_FIELDS
        assert len(model.templates) == 1

    def test_model_ids_disjoint_from_existing_ranges(self) -> None:
        taken = {PODCAST_MODEL_ID, X2_MODEL_ID}
        assert course.LESSON_MODEL_ID not in taken
        assert course.EXERCISE_MODEL_ID not in taken
        assert course.LESSON_MODEL_ID != course.EXERCISE_MODEL_ID

    def test_deck_id_range_disjoint_from_pool_and_exercises(self) -> None:
        deck_id = course._deck_id("Any::Deck")
        assert 1_930_000_000 <= deck_id < 1_990_000_000


# ---------------------------------------------------------------------------
# GUID discipline
# ---------------------------------------------------------------------------


class TestGuids:
    def test_lesson_guid_stable_and_distinct(self) -> None:
        assert course.lesson_guid("de", "kasus", 1) == \
            course.lesson_guid("de", "kasus", 1)
        assert course.lesson_guid("de", "kasus", 1) != \
            course.lesson_guid("de", "kasus", 2)
        assert course.lesson_guid("de", "kasus", 1) != \
            course.lesson_guid("it", "kasus", 1)

    def test_exercise_guid_distinct_namespace(self) -> None:
        assert course.exercise_guid("de", "kasus", "1") != \
            course.lesson_guid("de", "kasus", 1)
        assert course.exercise_guid("de", "kasus", "a") != \
            course.exercise_guid("de", "kasus", "b")


# ---------------------------------------------------------------------------
# Lesson parsing
# ---------------------------------------------------------------------------


class TestLessonParsing:
    def test_parses_valid_lesson(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(10))
        )
        assert lesson.lang == "de"
        assert lesson.unit == "kasus"
        assert lesson.unit_label == "Kasus (cases)"
        assert len(lesson.cards) == 10
        first = lesson.cards[0]
        assert first.front.refs == ("2.1",)
        assert first.front.display[0].kind == "tl"
        assert any(seg.kind == "speech" for seg in first.front.segments)

    def test_rejects_wrong_series(self, tmp_path: Path) -> None:
        with pytest.raises(course.CourseSourceError, match="series"):
            course.parse_course_lesson(_write_lesson(
                tmp_path, _lesson_source(8, series="grammar-walk-cards")
            ))

    def test_rejects_card_count_out_of_bounds(self, tmp_path: Path) -> None:
        for n_cards in (7, 13):
            with pytest.raises(course.CourseSourceError, match="8-12"):
                course.parse_course_lesson(_write_lesson(
                    tmp_path, _lesson_source(n_cards)
                ))

    def test_requires_ref_per_side(self, tmp_path: Path) -> None:
        source = _lesson_source(8).replace("REF: 2.1\nNarrate front 1.",
                                           "Narrate front 1.", 1)
        with pytest.raises(course.CourseSourceError, match="REF:"):
            course.parse_course_lesson(_write_lesson(tmp_path, source))

    def test_rejects_bad_ref_id(self, tmp_path: Path) -> None:
        source = _lesson_source(8).replace("REF: 2.1", "REF: not-a-ref", 1)
        with pytest.raises(course.CourseSourceError, match="§-id"):
            course.parse_course_lesson(_write_lesson(tmp_path, source))

    def test_accepts_chapter_refs_and_lettered_subsections(
        self, tmp_path: Path
    ) -> None:
        source = _lesson_source(8).replace(
            "REF: 2.1", "REF: 2.2.2a, Ch. 18", 1
        )
        lesson = course.parse_course_lesson(_write_lesson(tmp_path, source))
        assert lesson.cards[0].front.refs == ("2.2.2a", "Ch. 18")

    def test_svg_sidecar_must_exist(self, tmp_path: Path) -> None:
        source = _lesson_source(8).replace(
            "REF: 2.1\nNarrate front 1.",
            "REF: 2.1\nSVG: missing.svg\nNarrate front 1.", 1,
        )
        with pytest.raises(course.CourseSourceError, match="does not exist"):
            course.parse_course_lesson(_write_lesson(tmp_path, source))

    def test_visual_is_optional(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        assert lesson.cards[0].front.svg_file is None
        assert course._visual_field(lesson, lesson.cards[0].front) == ""

    def test_filename_must_match_lang_unit(self, tmp_path: Path) -> None:
        path = tmp_path / "de_other.md"
        path.write_text(_lesson_source(8), encoding="utf-8")
        with pytest.raises(course.CourseSourceError, match="filename"):
            course.parse_course_lesson(path)

    def test_side_html_carries_sources_footer(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        html_out = course.side_html(lesson.cards[0].front)
        assert "cl-refs" in html_out
        assert "Hammer §2.1" in html_out


# ---------------------------------------------------------------------------
# Exercise parsing + hygiene gate
# ---------------------------------------------------------------------------


class TestExerciseParsing:
    def test_parses_valid_file(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("c02-e14-i01")]}
        ))
        exercises = course.parse_exercises_file(path)
        assert len(exercises) == 1
        assert exercises[0].block == 1
        assert exercises[0].hammer_refs == ("2.6",)

    def test_rejects_solution_without_mark(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1", solution_html="Kein Highlight hier.")]}
        ))
        with pytest.raises(course.CourseSourceError, match="mark"):
            course.parse_exercises_file(path)

    def test_rejects_solution_with_blank_placeholder(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise(
                "x1",
                solution_html="Wir sprachen mit d___ <mark>der</mark> Frau.",
            )]}
        ))
        with pytest.raises(course.CourseSourceError, match="placeholder"):
            course.parse_exercises_file(path)

    def test_rejects_markup_beyond_mark(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise(
                "x1",
                solution_html='<script>x</script> <mark>der</mark> Frau.',
            )]}
        ))
        with pytest.raises(course.CourseSourceError, match="only <mark>"):
            course.parse_exercises_file(path)

    def test_rejects_unknown_provenance(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1", provenance="llm-freestyle")]}
        ))
        with pytest.raises(course.CourseSourceError, match="provenance"):
            course.parse_exercises_file(path)

    def test_rejects_duplicate_ids_across_blocks(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1")], 2: [_exercise("x1")]}
        ))
        with pytest.raises(course.CourseSourceError, match="duplicate"):
            course.parse_exercises_file(path)

    def test_rejects_missing_hammer_refs(self, tmp_path: Path) -> None:
        path = _write_exercises(tmp_path, _exercises_payload(
            {1: [_exercise("x1", hammer_refs=[])]}
        ))
        with pytest.raises(course.CourseSourceError, match="hammer_refs"):
            course.parse_exercises_file(path)

    def test_filename_must_encode_lang_and_unit(self, tmp_path: Path) -> None:
        path = tmp_path / "kasus.json"
        path.write_text("{}", encoding="utf-8")
        with pytest.raises(course.CourseSourceError, match="filename"):
            course.parse_exercises_file(path)

    def test_solution_html_escapes_outside_marks(self) -> None:
        raw = _exercise("x1", solution_html="A & B <mark>c < d</mark> e")
        parsed = course._parse_exercise(
            Path("de_kasus.exercises.json"), "de", "kasus", 1, raw
        )
        rendered = course.exercise_solution_html(parsed)
        assert "&amp;" in rendered
        assert "<mark>c &lt; d</mark>" in rendered


# ---------------------------------------------------------------------------
# Enrichment sidecar parsing
# ---------------------------------------------------------------------------


class TestEnrichmentParsing:
    def test_parses_valid_sidecar(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1, example_html=(
                "e.g. <i>mit Maria Simon</i><br>then say it aloud")),
             _block_enrichment(2)],
            [_exercise_enrichment("x1"), _exercise_enrichment("x2")],
        )
        enrichment = course.parse_enrichment_file(
            _write_enrichment(tmp_path, payload)
        )
        assert enrichment.lang == "de"
        assert enrichment.unit == "kasus"
        assert set(enrichment.block_tasks) == {1, 2}
        assert enrichment.block_tasks[1].task_html == "Add the case ending."
        assert enrichment.block_tasks[2].example_html is None
        assert set(enrichment.exercises) == {"x1", "x2"}
        assert enrichment.exercises["x1"].solution_en.startswith("We spoke")

    def test_rejects_contract_one_with_clear_error(
        self, tmp_path: Path
    ) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)], [_exercise_enrichment("x1")], contract=1
        )
        with pytest.raises(course.CourseSourceError,
                           match=r"contract must be 2, got 1"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_missing_contract(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)], [_exercise_enrichment("x1")]
        )
        del payload["contract"]
        with pytest.raises(course.CourseSourceError,
                           match="contract must be 2"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_lang_unit_mismatch_with_filename(
        self, tmp_path: Path
    ) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)], [_exercise_enrichment("x1")],
            unit="plurals",
        )
        with pytest.raises(course.CourseSourceError, match="filename"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_duplicate_block(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1), _block_enrichment(1)],
            [_exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="duplicate block"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_duplicate_exercise_id(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment("x1"), _exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="duplicate"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_span_tag_in_task(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1, task_html='<span>Add</span> the ending.')],
            [_exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="only"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_script_tag_in_task(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(
                1, task_html='<script>alert(1)</script> the ending.'
            )],
            [_exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="only"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_event_handler(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(
                1, task_html='Fill <i onclick=alert(1)>this</i> in.'
            )],
            [_exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="event-handler"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_src_href(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(
                1, example_html='<i href="http://x">Wein</i>'
            )],
            [_exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="src/href"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_markup_in_solution_en(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment("x1", solution_en="the <b>wine</b>")],
        )
        with pytest.raises(course.CourseSourceError, match="plain text"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_b_tag_in_why(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment("x1", why_en="Use the <b>dative</b>.")],
        )
        with pytest.raises(course.CourseSourceError, match="only"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_parses_full_solution_string_and_null(
        self, tmp_path: Path
    ) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment("x1", solution_full_html=_FULL_SOLUTION),
             _exercise_enrichment("x2")],
        )
        enrichment = course.parse_enrichment_file(
            _write_enrichment(tmp_path, payload)
        )
        assert enrichment.exercises["x1"].solution_full_html == _FULL_SOLUTION
        assert enrichment.exercises["x2"].solution_full_html is None

    def test_rejects_missing_full_solution_key(self, tmp_path: Path) -> None:
        item = _exercise_enrichment("x1")
        del item["solution_full_html"]
        payload = _enrichment_payload([_block_enrichment(1)], [item])
        with pytest.raises(course.CourseSourceError,
                           match="solution_full_html is required"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_full_solution_without_terminal_punctuation(
        self, tmp_path: Path
    ) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1",
                solution_full_html="Ich möchte <mark>den</mark> Wein",
            )],
        )
        with pytest.raises(course.CourseSourceError,
                           match="terminal punctuation"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_full_solution_without_mark(self, tmp_path: Path) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1", solution_full_html="Ich möchte den Wein."
            )],
        )
        with pytest.raises(course.CourseSourceError, match="nonempty <mark>"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))

    def test_rejects_disallowed_tag_in_full_solution(
        self, tmp_path: Path
    ) -> None:
        payload = _enrichment_payload(
            [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1",
                solution_full_html="<b>Ich</b> möchte <mark>den</mark> Wein.",
            )],
        )
        with pytest.raises(course.CourseSourceError, match="only"):
            course.parse_enrichment_file(_write_enrichment(tmp_path, payload))


# ---------------------------------------------------------------------------
# Enrichment cross-validation (id/block coverage + no-invented-German)
# ---------------------------------------------------------------------------


class TestEnrichmentValidation:
    def _exercises(self, tmp_path: Path,
                   blocks: dict[int, list[dict]]) -> list:
        return course.parse_exercises_file(
            _write_exercises(tmp_path, _exercises_payload(blocks))
        )

    def _enrichment(self, tmp_path: Path, blocks: list[dict],
                    items: list[dict]):
        return course.parse_enrichment_file(_write_enrichment(
            tmp_path, _enrichment_payload(blocks, items)
        ))

    def test_valid_sidecar_passes(self, tmp_path: Path) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)], [_exercise_enrichment("x1")]
        )
        course.validate_enrichment(exercises, enrichment)

    def test_unknown_id_rejected(self, tmp_path: Path) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment("x1"), _exercise_enrichment("x9")],
        )
        with pytest.raises(course.CourseSourceError, match="unknown.*x9"):
            course.validate_enrichment(exercises, enrichment)

    def test_missing_id_named_in_error(self, tmp_path: Path) -> None:
        exercises = self._exercises(
            tmp_path, {1: [_exercise("x1"), _exercise("x2")]}
        )
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)], [_exercise_enrichment("x1")]
        )
        with pytest.raises(course.CourseSourceError, match="missing.*x2"):
            course.validate_enrichment(exercises, enrichment)

    def test_missing_block_rejected(self, tmp_path: Path) -> None:
        exercises = self._exercises(
            tmp_path, {1: [_exercise("x1")], 2: [_exercise("x2")]}
        )
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment("x1"), _exercise_enrichment("x2")],
        )
        with pytest.raises(course.CourseSourceError, match="block"):
            course.validate_enrichment(exercises, enrichment)

    def test_invented_german_in_task_rejected(self, tmp_path: Path) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path,
            [_block_enrichment(
                1, task_html="Decline <i>ein ganz neuer Satz</i> correctly."
            )],
            [_exercise_enrichment("x1")],
        )
        with pytest.raises(course.CourseSourceError, match="verbatim"):
            course.validate_enrichment(exercises, enrichment)

    def test_invented_german_in_why_rejected(self, tmp_path: Path) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1", why_en="Because <i>zu Hause bleiben</i> is dative."
            )],
        )
        with pytest.raises(course.CourseSourceError, match="verbatim"):
            course.validate_enrichment(exercises, enrichment)

    def test_verbatim_german_with_other_whitespace_accepted(
        self, tmp_path: Path
    ) -> None:
        # Prompt says "… mit Maria Simon, …"; the span copies it with
        # different internal whitespace — normalization must accept it.
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path,
            [_block_enrichment(
                1, task_html="Complete <i>Maria\n   Simon</i>'s apposition."
            )],
            [_exercise_enrichment("x1")],
        )
        course.validate_enrichment(exercises, enrichment)

    def test_span_may_quote_solution_text(self, tmp_path: Path) -> None:
        # <mark>-wrapped solution text counts as block source (tags are
        # stripped before the substring check).
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1",
                why_en="The apposition takes <i>der Filmschauspielerin</i>.",
            )],
        )
        course.validate_enrichment(exercises, enrichment)

    def test_full_solution_passes_when_spans_match(
        self, tmp_path: Path
    ) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment("x1", solution_full_html=_FULL_SOLUTION)],
        )
        course.validate_enrichment(exercises, enrichment)

    def test_full_solution_null_passes(self, tmp_path: Path) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)], [_exercise_enrichment("x1")]
        )
        assert enrichment.exercises["x1"].solution_full_html is None
        course.validate_enrichment(exercises, enrichment)

    def test_full_solution_mark_not_in_original_rejected(
        self, tmp_path: Path
    ) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1",
                solution_full_html=(
                    "Wir sprachen mit <mark>einer falschen</mark> Frau."
                ),
            )],
        )
        with pytest.raises(course.CourseSourceError,
                           match="does not match any <mark> span"):
            course.validate_enrichment(exercises, enrichment)

    def test_original_mark_missing_from_full_rejected(
        self, tmp_path: Path
    ) -> None:
        # Original has TWO answer spans; the full sentence only carries one.
        exercises = self._exercises(tmp_path, {1: [_exercise(
            "x1",
            solution_html=(
                "Ich möchte <mark>den französischen</mark> Wein; "
                "<mark>einen französischen</mark> Wein."
            ),
        )]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1",
                solution_full_html=(
                    "Ich möchte <mark>den französischen</mark> Wein."
                ),
            )],
        )
        with pytest.raises(course.CourseSourceError,
                           match="missing from solution_full_html"):
            course.validate_enrichment(exercises, enrichment)

    def test_full_solution_span_whitespace_normalized(
        self, tmp_path: Path
    ) -> None:
        exercises = self._exercises(tmp_path, {1: [_exercise("x1")]})
        enrichment = self._enrichment(
            tmp_path, [_block_enrichment(1)],
            [_exercise_enrichment(
                "x1",
                solution_full_html=(
                    "Gestern sprachen wir mit Maria Simon, "
                    "<mark> der\n</mark> Filmschauspielerin."
                ),
            )],
        )
        course.validate_enrichment(exercises, enrichment)


# ---------------------------------------------------------------------------
# Enriched field assembly + build wiring
# ---------------------------------------------------------------------------


class TestEnrichedFields:
    def _fixture(self, tmp_path: Path):
        exercises = course.parse_exercises_file(_write_exercises(
            tmp_path, _exercises_payload({1: [_exercise("x1")]})
        ))
        enrichment = course.parse_enrichment_file(_write_enrichment(
            tmp_path, _enrichment_payload(
                [_block_enrichment(1, example_html=(
                    "e.g. <i>mit Maria Simon</i>"))],
                [_exercise_enrichment(
                    "x1", solution_en="We spoke with Maria & the actress."
                )],
            )
        ))
        return exercises, enrichment

    def test_enriched_fields(self, tmp_path: Path) -> None:
        exercises, enrichment = self._fixture(tmp_path)
        fields = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)", enrichment=enrichment
        )
        idx = course.EXERCISE_FIELDS.index
        assert fields[idx("Instruction")] == "Add the case ending."
        assert fields[idx(course.EXERCISE_EXAMPLE_FIELD)] == \
            "e.g. <i>mit Maria Simon</i>"
        assert fields[idx(course.EXERCISE_SOLUTION_EN_FIELD)] == \
            "We spoke with Maria &amp; the actress."
        assert fields[idx(course.EXERCISE_WHY_FIELD)] == \
            "Apposition copies the case: <i>mit</i> takes the dative."

    def test_legacy_fields_without_enrichment(self, tmp_path: Path) -> None:
        exercises, _enrichment = self._fixture(tmp_path)
        fields = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)"
        )
        idx = course.EXERCISE_FIELDS.index
        assert fields[idx("Instruction")] == \
            html.escape(exercises[0].instruction)
        assert fields[idx(course.EXERCISE_EXAMPLE_FIELD)] == ""
        assert fields[idx(course.EXERCISE_SOLUTION_EN_FIELD)] == ""
        assert fields[idx(course.EXERCISE_WHY_FIELD)] == ""

    def test_solution_and_prompt_identical_in_both_modes(
        self, tmp_path: Path
    ) -> None:
        """Audio identity guard: enrichment may not shift the solution."""
        exercises, enrichment = self._fixture(tmp_path)
        idx = course.EXERCISE_FIELDS.index
        with_enrichment = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)", enrichment=enrichment
        )
        without = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)"
        )
        for name in ("ItemId", "PromptHTML", "SolutionHTML", "SolutionAudio"):
            assert with_enrichment[idx(name)] == without[idx(name)]
        assert course.solution_spoken_text(exercises[0]) == \
            "Wir sprachen mit Maria Simon, der Filmschauspielerin."

    def test_build_wires_enrichment_through(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        exercises, enrichment = self._fixture(tmp_path)
        out = tmp_path / "unit.apkg"
        result = course.build_course_apkg(
            out_path=out,
            lesson=lesson,
            exercises=exercises,
            root_override="ZZ Grammar Course Pilot (disposable)",
            enrichment=enrichment,
        )
        assert result["enriched"] is True
        conn = _open_collection(out, tmp_path)
        flds = conn.execute(
            "SELECT flds FROM notes WHERE mid = ?",
            (course.EXERCISE_MODEL_ID,),
        ).fetchone()[0]
        conn.close()
        fields = flds.split("\x1f")
        idx = course.EXERCISE_FIELDS.index
        assert fields[idx("Instruction")] == "Add the case ending."
        assert fields[idx(course.EXERCISE_EXAMPLE_FIELD)] == \
            "e.g. <i>mit Maria Simon</i>"
        assert "<mark>der</mark>" in fields[idx("SolutionHTML")]

    def test_build_aborts_on_bad_enrichment(self, tmp_path: Path) -> None:
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        exercises, _valid = self._fixture(tmp_path)
        bad = course.parse_enrichment_file(_write_enrichment(
            tmp_path, _enrichment_payload(
                [_block_enrichment(1)],
                [_exercise_enrichment("x1"), _exercise_enrichment("x9")],
            )
        ))
        with pytest.raises(course.CourseSourceError, match="x9"):
            course.build_course_apkg(
                out_path=tmp_path / "bad.apkg",
                lesson=lesson,
                exercises=exercises,
                root_override="ZZ Grammar Course Pilot (disposable)",
                enrichment=bad,
            )


# ---------------------------------------------------------------------------
# Effective solution (contract 2): display + voicing follow the full form
# ---------------------------------------------------------------------------


class TestEffectiveSolution:
    def _fixture(self, tmp_path: Path, *, full: object = _FULL_SOLUTION):
        exercises = course.parse_exercises_file(_write_exercises(
            tmp_path, _exercises_payload({1: [_exercise("x1")]})
        ))
        enrichment = course.parse_enrichment_file(_write_enrichment(
            tmp_path, _enrichment_payload(
                [_block_enrichment(1)],
                [_exercise_enrichment("x1", solution_full_html=full)],
            )
        ))
        course.validate_enrichment(exercises, enrichment)
        return exercises, enrichment

    def test_effective_is_full_when_present(self, tmp_path: Path) -> None:
        exercises, enrichment = self._fixture(tmp_path)
        assert course.effective_solution_html(exercises[0], enrichment) == \
            _FULL_SOLUTION

    def test_effective_is_original_when_null(self, tmp_path: Path) -> None:
        exercises, enrichment = self._fixture(tmp_path, full=None)
        assert course.effective_solution_html(exercises[0], enrichment) == \
            course.exercise_solution_html(exercises[0])

    def test_effective_is_original_without_enrichment(
        self, tmp_path: Path
    ) -> None:
        exercises, _enrichment = self._fixture(tmp_path)
        assert course.effective_solution_html(exercises[0], None) == \
            course.exercise_solution_html(exercises[0])

    def test_note_solution_field_carries_full(self, tmp_path: Path) -> None:
        exercises, enrichment = self._fixture(tmp_path)
        fields = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)", enrichment=enrichment
        )
        idx = course.EXERCISE_FIELDS.index
        assert fields[idx("SolutionHTML")] == _FULL_SOLUTION
        # front side + audio identity fields stay untouched
        assert fields[idx("PromptHTML")] == html.escape(exercises[0].prompt)
        assert fields[idx("SolutionAudio")] == ""

    def test_note_solution_field_original_when_null(
        self, tmp_path: Path
    ) -> None:
        exercises, enrichment = self._fixture(tmp_path, full=None)
        fields = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)", enrichment=enrichment
        )
        legacy = course.exercise_note_fields(
            exercises[0], unit_label="Kasus (cases)"
        )
        idx = course.EXERCISE_FIELDS.index
        assert fields[idx("SolutionHTML")] == legacy[idx("SolutionHTML")]

    def test_speakable_form_strips_ital_and_br(self) -> None:
        assert course.speakable_solution_html(
            "Ich möchte <mark>den</mark> <i>Wein</i>.<br>Danke."
        ) == "Ich möchte <mark>den</mark> Wein. Danke."

    def test_apply_effective_solutions_shifts_spoken_text(
        self, tmp_path: Path
    ) -> None:
        exercises, enrichment = self._fixture(tmp_path)
        effective = course.apply_effective_solutions(exercises, enrichment)
        assert course.solution_spoken_text(effective[0]) == (
            "Gestern sprachen wir mit Maria Simon, der Filmschauspielerin."
        )
        # the parsed originals are untouched (frozen dataclass, replace)
        assert exercises[0].solution_html.startswith("Wir sprachen")

    def test_apply_effective_solutions_null_and_absent_are_noops(
        self, tmp_path: Path
    ) -> None:
        exercises, enrichment = self._fixture(tmp_path, full=None)
        assert course.apply_effective_solutions(exercises, enrichment) == \
            list(exercises)
        assert course.apply_effective_solutions(exercises, None) == \
            list(exercises)

    def test_enrich_seed_payload_substitutes_speakable_form(
        self, tmp_path: Path
    ) -> None:
        full = ("Gestern sprachen wir mit <i>Maria Simon</i>, "
                "<mark>der</mark> Filmschauspielerin.")
        exercises, enrichment = self._fixture(tmp_path, full=full)
        payload = _exercises_payload({1: [_exercise("x1")]})
        substituted = course.enrich_seed_payload(payload, enrichment)
        row = substituted["blocks"][0]["exercises"][0]
        assert row["solution_html"] == (
            "Gestern sprachen wir mit Maria Simon, "
            "<mark>der</mark> Filmschauspielerin."
        )
        # deep copy — the caller's payload is untouched
        assert payload["blocks"][0]["exercises"][0]["solution_html"] \
            .startswith("Wir sprachen")
        # the substituted row still satisfies the seed server's own
        # solution hygiene gate (mark-only markup)
        course.validate_solution_html(
            Path("de_kasus.exercises.json"), "x1", row["solution_html"]
        )

    def test_enrich_seed_payload_leaves_null_rows_alone(
        self, tmp_path: Path
    ) -> None:
        exercises, enrichment = self._fixture(tmp_path, full=None)
        payload = _exercises_payload({1: [_exercise("x1")]})
        substituted = course.enrich_seed_payload(payload, enrichment)
        assert substituted == payload


# ---------------------------------------------------------------------------
# Exercise template sanity (redesign classes + spare-field conditionals)
# ---------------------------------------------------------------------------


class TestExerciseTemplates:
    def test_spare_field_constants_are_frozen_names(self) -> None:
        assert course.EXERCISE_EXAMPLE_FIELD == "Extra1"
        assert course.EXERCISE_SOLUTION_EN_FIELD == "Extra2"
        assert course.EXERCISE_WHY_FIELD == "Extra3"
        for name in (course.EXERCISE_EXAMPLE_FIELD,
                     course.EXERCISE_SOLUTION_EN_FIELD,
                     course.EXERCISE_WHY_FIELD):
            assert name in course.EXERCISE_FIELDS

    def test_new_classes_present_with_night_overrides(self) -> None:
        for cls in ("cx-example", "cx-example-label", "cx-prompt-echo",
                    "cx-gloss", "cx-why"):
            assert f".{cls}" in course.EXERCISE_CSS
            assert f".card.night_mode .{cls}" in course.EXERCISE_CSS
            assert f".card.nightMode .{cls}" in course.EXERCISE_CSS

    def test_german_inside_english_renders_serif_italic(self) -> None:
        assert ".cx-instr i, .cx-example i, .cx-why i" in course.EXERCISE_CSS

    def test_front_has_conditional_example_block(self) -> None:
        assert "{{#Extra1}}" in course.EXERCISE_FRONT
        assert "{{/Extra1}}" in course.EXERCISE_FRONT
        assert "cx-example-label" in course.EXERCISE_FRONT
        assert "{{Instruction}}" in course.EXERCISE_FRONT
        assert '<div class="cx-prompt">{{PromptHTML}}</div>' \
            in course.EXERCISE_FRONT

    def test_back_structure_prompt_echo_gloss_why(self) -> None:
        back = course.EXERCISE_BACK
        assert "{{#Extra2}}" in back and "{{/Extra2}}" in back
        assert "{{#Extra3}}" in back and "{{/Extra3}}" in back
        # prompt echo above the solution, gloss below it, why before refs
        assert back.index("cx-prompt-echo") < back.index("cx-solution")
        assert back.index("cx-solution") < back.index("cx-gloss")
        assert back.index("cx-gloss") < back.index("{{SolutionAudio}}")
        assert back.index("cx-why") < back.index('<hr id="answer">')
        assert "cx-refs" in back


# ---------------------------------------------------------------------------
# Interleave arithmetic
# ---------------------------------------------------------------------------


class TestInterleave:
    def _lesson(self, tmp_path: Path, n_cards: int = 8) -> course.CourseLesson:
        return course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(n_cards))
        )

    def _exercises(self, tmp_path: Path,
                   blocks: dict[int, int]) -> list[course.CourseExercise]:
        payload = _exercises_payload({
            block: [_exercise(f"b{block}i{i}") for i in range(count)]
            for block, count in blocks.items()
        })
        return course.parse_exercises_file(_write_exercises(tmp_path, payload))

    def test_positions_follow_card_then_block(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        exercises = self._exercises(tmp_path, {1: 3, 2: 2})
        plan = course.interleave_plan(lesson, exercises)
        kinds = [(kind, key) for kind, key, _due in plan[:8]]
        assert kinds == [
            ("lesson", "1"),
            ("exercise", "b1i0"), ("exercise", "b1i1"), ("exercise", "b1i2"),
            ("lesson", "2"),
            ("exercise", "b2i0"), ("exercise", "b2i1"),
            ("lesson", "3"),
        ]

    def test_dues_are_contiguous_unique_one_based(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        exercises = self._exercises(tmp_path, {1: 5, 3: 4, 8: 2})
        plan = course.interleave_plan(lesson, exercises)
        dues = [due for _kind, _key, due in plan]
        assert dues == list(range(1, len(plan) + 1))
        assert len(plan) == 8 + 11

    def test_empty_blocks_let_cards_run_consecutively(
        self, tmp_path: Path
    ) -> None:
        lesson = self._lesson(tmp_path)
        plan = course.interleave_plan(lesson, [])
        assert [kind for kind, _key, _due in plan] == ["lesson"] * 8

    def test_block_beyond_card_count_is_an_error(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        exercises = self._exercises(tmp_path, {9: 1})
        with pytest.raises(ValueError, match="block"):
            course.interleave_plan(lesson, exercises)

    def test_unit_mismatch_is_an_error(self, tmp_path: Path) -> None:
        lesson = self._lesson(tmp_path)
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        payload = _exercises_payload(
            {1: [_exercise("x1")]}, unit="plurals"
        )
        exercises = course.parse_exercises_file(
            _write_exercises(other_dir, payload, unit="plurals")
        )
        with pytest.raises(ValueError, match="belongs to"):
            course.interleave_plan(lesson, exercises)


# ---------------------------------------------------------------------------
# Deck naming
# ---------------------------------------------------------------------------


class TestDeckNames:
    def test_production_names_compose_from_estate_root(self) -> None:
        lesson_deck, exercise_deck = course.course_deck_names(
            "de", "Kasus (cases)"
        )
        assert lesson_deck == "DE German::2 Grammar::Kasus (cases)::1 Lesson"
        assert exercise_deck == "DE German::2 Grammar::Kasus (cases)::2 Exercises"

    def test_pilot_root_override(self) -> None:
        lesson_deck, exercise_deck = course.course_deck_names(
            "de", "Kasus (cases)",
            root_override="ZZ Grammar Course Pilot (disposable)",
        )
        assert lesson_deck == "ZZ Grammar Course Pilot (disposable)::1 Lesson"
        assert exercise_deck == \
            "ZZ Grammar Course Pilot (disposable)::2 Exercises"


# ---------------------------------------------------------------------------
# APKG build
# ---------------------------------------------------------------------------


def _open_collection(apkg_path: Path, tmp_path: Path) -> sqlite3.Connection:
    extract = tmp_path / "apkg_extract"
    extract.mkdir(exist_ok=True)
    with zipfile.ZipFile(apkg_path) as bundle:
        bundle.extractall(extract)
    return sqlite3.connect(extract / "collection.anki2")


class TestBuild:
    def _build(self, tmp_path: Path, blocks: dict[int, int] | None = None):
        lesson = course.parse_course_lesson(
            _write_lesson(tmp_path, _lesson_source(8))
        )
        payload = _exercises_payload({
            block: [_exercise(f"b{block}i{i}") for i in range(count)]
            for block, count in (blocks or {1: 3, 2: 2}).items()
        })
        exercises = course.parse_exercises_file(
            _write_exercises(tmp_path, payload)
        )
        out = tmp_path / "unit.apkg"
        result = course.build_course_apkg(
            out_path=out,
            lesson=lesson,
            exercises=exercises,
            root_override="ZZ Grammar Course Pilot (disposable)",
        )
        return out, result

    def test_build_counts_and_audio_pending(self, tmp_path: Path) -> None:
        out, result = self._build(tmp_path)
        assert out.exists()
        assert result["notes"] == 8 + 5
        assert result["lesson_cards"] == 8
        assert result["exercises"] == 5
        # 8 fronts + 8 backs + 5 solutions, all pending in the fixture build
        assert result["audio_pending"] == 21

    def test_due_positions_encode_interleave(self, tmp_path: Path) -> None:
        out, _result = self._build(tmp_path)
        conn = _open_collection(out, tmp_path)
        rows = conn.execute(
            "SELECT c.due, n.mid, n.flds FROM cards c JOIN notes n "
            "ON c.nid = n.id ORDER BY c.due"
        ).fetchall()
        dues = [row[0] for row in rows]
        assert dues == list(range(1, 14))
        # Row 1 is lesson card 1; rows 2-4 its block; row 5 lesson card 2.
        assert rows[0][1] == course.LESSON_MODEL_ID
        assert rows[1][1] == course.EXERCISE_MODEL_ID
        assert rows[4][1] == course.LESSON_MODEL_ID
        conn.close()

    def test_two_subdecks_and_tags(self, tmp_path: Path) -> None:
        out, _result = self._build(tmp_path)
        conn = _open_collection(out, tmp_path)
        decks = json.loads(
            conn.execute("SELECT decks FROM col").fetchone()[0]
        )
        names = {deck["name"] for deck in decks.values()}
        assert "ZZ Grammar Course Pilot (disposable)::1 Lesson" in names
        assert "ZZ Grammar Course Pilot (disposable)::2 Exercises" in names
        tags_rows = conn.execute("SELECT tags FROM notes").fetchall()
        all_tags = " ".join(row[0] for row in tags_rows)
        assert "idiomatic-course-lesson" in all_tags
        assert "idiomatic-course-exercise" in all_tags
        assert "idiomatic-course-block::de::kasus::c01" in all_tags
        assert "idiomatic-course-src::book-verbatim" in all_tags
        assert course.AUDIO_PENDING_TAG in all_tags
        conn.close()

    def test_lesson_guids_survive_rebuild(self, tmp_path: Path) -> None:
        out, _result = self._build(tmp_path)
        conn = _open_collection(out, tmp_path)
        guids_first = sorted(
            row[0] for row in conn.execute("SELECT guid FROM notes")
        )
        conn.close()
        out2, _result = self._build(tmp_path)
        conn = _open_collection(out2, tmp_path)
        guids_second = sorted(
            row[0] for row in conn.execute("SELECT guid FROM notes")
        )
        conn.close()
        assert guids_first == guids_second


# ---------------------------------------------------------------------------
# Copyright guard
# ---------------------------------------------------------------------------


class TestCopyrightGuard:
    def test_book_local_path_is_gitignored(self) -> None:
        """Book-derived exercise content must never be committable."""
        probe = _REPO_ROOT / "idiomatic" / "grammar" / "data" / "course" \
            / "book_local" / "de_kasus.exercises.json"
        try:
            completed = subprocess.run(
                ["git", "check-ignore", "-q", str(probe)],
                cwd=_REPO_ROOT,
                capture_output=True,
                timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        assert completed.returncode == 0, \
            "idiomatic/grammar/data/course/book_local/ must be gitignored"

    def test_book_local_dir_constant_points_inside_ignored_path(self) -> None:
        assert course.BOOK_LOCAL_DIR.name == "book_local"
        assert course.BOOK_LOCAL_DIR.parent.name == "course"
