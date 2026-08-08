#!/usr/bin/env python3
"""Build the committed, read-only inventory of the legacy +2 Anki estate.

The source must be a physical SQLite collection copy beneath
``docs/research/legacy_estate_work``.  It is opened through SQLite's
``mode=ro&immutable=1`` URI; this module never imports ``anki.Collection`` and
has no AnkiWeb sync or collection-write path.

The generated JSON is deliberately flat at the deck-row level so it can seed
the ``legacy_estate`` dashboard table without translating a second audit
format.  Markdown files are views of exactly the same manifest.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import hashlib
import html
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator, Sequence


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORK_ROOT = REPO_ROOT / "docs" / "research" / "legacy_estate_work"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "docs" / "research" / "legacy_estate"
SOURCE_ACCOUNT = "evgeny.morozov+2@gmail.com"
SQLITE_HEADER = b"SQLite format 3\x00"
DECK_SEPARATOR = "\x1f"
FIELD_SEPARATOR = "\x1f"
VERDICTS = ("import", "partial", "skip", "already-covered")

SOUND_RE = re.compile(r"\[sound:([^\]\r\n]+)\]", re.IGNORECASE)
HTML_RE = re.compile(r"<[^>]*>")
SPACE_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
TENSE_FRONT_RE = re.compile(
    r"^\s*(?P<verb>[^;]+?)\s*;\s*_(?P<lang>[a-z]{2})"
    r"(?:\s*_?(?P<tense>[\w'’]+))?\s*$",
    re.UNICODE,
)

LANG_CODES = frozenset({"de", "es", "fr", "it", "pt", "zh", "nl", "sv", "no"})
LANG_ALIASES = {
    "br": "pt",
    "brazilian": "pt",
    "chinese": "zh",
    "cn": "zh",
    "deutsch": "de",
    "german": "de",
    "spanish": "es",
    "sp": "es",
    "french": "fr",
    "italian": "it",
    "portuguese": "pt",
    "mandarin": "zh",
    "dutch": "nl",
    "swedish": "sv",
    "norwegian": "no",
}

CURRICULUM_LANGS = ("de", "es", "fr", "it", "pt")

# These are deliberately language-distinct function words/forms.  This is not
# a general language detector: a back is only flagged when it has at least two
# distinct markers for one non-target language, none for the target language,
# and enough words to avoid short-gloss guesses.
WRONG_LANGUAGE_MARKERS = {
    "de": frozenset(
        {
            "der",
            "den",
            "dem",
            "des",
            "das",
            "die",
            "eine",
            "einen",
            "einem",
            "einer",
            "eines",
            "nicht",
            "für",
            "über",
            "unter",
            "zwischen",
            "beim",
            "zum",
            "zur",
            "wird",
            "werden",
            "sind",
            "kann",
            "können",
            "muss",
            "müssen",
        }
    ),
    "es": frozenset(
        {
            "el",
            "los",
            "las",
            "usted",
            "ustedes",
            "ellos",
            "ellas",
            "hay",
            "aunque",
            "mientras",
            "tiene",
            "tienen",
            "hemos",
            "han",
            "está",
            "están",
            "fue",
            "fueron",
        }
    ),
    "fr": frozenset(
        {
            "aux",
            "avec",
            "pour",
            "dans",
            "cette",
            "ces",
            "nous",
            "vous",
            "ils",
            "elles",
            "sont",
            "pas",
            "ont",
            "était",
            "été",
        }
    ),
    "it": frozenset(
        {
            "gli",
            "dello",
            "della",
            "delle",
            "degli",
            "nel",
            "nella",
            "nei",
            "nelle",
            "perché",
            "questo",
            "questa",
            "questi",
            "queste",
            "sono",
            "siamo",
            "anche",
            "aveva",
            "hanno",
        }
    ),
    "pt": frozenset(
        {
            "os",
            "uma",
            "umas",
            "não",
            "você",
            "vocês",
            "eles",
            "elas",
            "aos",
            "num",
            "numa",
            "pelo",
            "pela",
            "pelos",
            "pelas",
            "são",
            "estão",
            "têm",
            "temos",
            "foram",
            "isso",
        }
    ),
}

# Explicit curriculum allowlist.  It excludes exercises2, tenses, morphology
# lookup tables, private banks, and explanatory prose by construction.
GRAMMAR_BANK_FILES = {
    "de": ("de_preps.json", "de_dativ_verben.json", "f2_de_case_roles.json"),
    "es": ("es_verb_prep.json", "es_muy_mucho.json", "f2_es_pret_impf.json"),
    "fr": (
        "fr_quantites_de.json",
        "fr_prep_lieux.json",
        "fr_genre_noyau.json",
        "fr_an_annee.json",
        "f2_fr_pc_imparfait.json",
    ),
    "it": (
        "it_clitici_ci_ne.json",
        "it_genere_plurali.json",
        "it_reggenze_verbali.json",
        "f2_it_pp_imperfetto.json",
    ),
    "pt": (
        "pt_clitic_placement.json",
        "pt_gender_core.json",
        "pt_regencia_verbal.json",
        "f2_pt_person_aspect.json",
    ),
}
GRAMMAR_SENTENCE_FIELDS = (
    "sentence",
    "contrast_form",
    "example",
    "example_es",
    "example_dat_or_fixed",
    "example_akk",
)
GRAMMAR_GLOSS_FIELDS = ("example_en", "gloss_en", "en")

EXERCISE_TOPIC_STATUS = {
    "CONNECTING": ("shipped", "wave-1"),
    "CONDITIONALS": ("shipped", "wave-2"),
    "TENSES": ("planned", "wave-3"),
    "FANCY_VOCAB": ("planned", "wave-4"),
    "BIG_TECH_VOCAB": ("planned", "wave-5"),
    "COLD_WAR_VOCAB": ("planned", "wave-5"),
    "GEOPOLITICS": ("planned", "wave-5"),
    "BIG_TECH_PHRASES": ("planned", "wave-6"),
    "FALSE_FRIENDS": ("rebuild", "wave-7"),
    "COMMANDS": ("gap-audit", "roadmap"),
    "PRONOUNS": ("gap-audit", "roadmap"),
    "REFLEXIVE": ("gap-audit", "roadmap"),
    "RELFEXIVE": ("gap-audit", "roadmap"),
    "REFLEXIV": ("gap-audit", "roadmap"),
}

SETTLED_FACTS = (
    {
        "code": "exercises_it_french_copy",
        "finding": (
            "The 2026-08-03 audit proved all 2,612 former IT exercise backs were "
            "byte-identical French copies. The fresh snapshot contains no EXCERCISES::IT "
            "tree; the finding is settled and was not re-tested."
        ),
    },
    {
        "code": "exercises_pt_big_tech_phrases_spanish",
        "finding": (
            "The prior audit proved 30 of 91 PT::BIG_TECH_PHRASES backs were Spanish. "
            "The fresh deck has 61 notes, proving those 30 contaminated rows are absent; "
            "this settled subtraction was not re-litigated."
        ),
    },
    {
        "code": "exercises_es_false_friends_toxic",
        "finding": (
            "The prior audit found ES::FALSE_FRIENDS pedagogically toxic. It is absent "
            "from the fresh snapshot and remains rebuild-only."
        ),
    },
    {
        "code": "tenses_old_profiled",
        "finding": (
            "The 14,267-card _tenses_old whole-paradigm corpus has already been reduced "
            "to committed five-language profiles; attested paradigms are evidence, not "
            "forms safe to import without re-verification."
        ),
    },
)

REQUIRED_TABLE_COLUMNS = {
    "decks": {"id", "name"},
    "notetypes": {"id", "name"},
    "fields": {"ntid", "ord", "name"},
    "templates": {"ntid", "ord", "name"},
    "notes": {"id", "mid", "tags", "flds"},
    "cards": {"id", "nid", "did", "ivl", "reps", "type", "queue", "odid", "odue"},
    "revlog": {"id", "cid"},
}


class AuditError(RuntimeError):
    """The source or requested output cannot satisfy the read-only contract."""


@dataclasses.dataclass(frozen=True)
class NoteInfo:
    mid: int
    front: str
    back: str
    sound_tags: int
    tag_langs: frozenset[str]


@dataclasses.dataclass
class DeckAccumulator:
    note_ids: set[int] = dataclasses.field(default_factory=set)
    cards: int = 0
    mature: int = 0
    reps: int = 0
    reviews: int = 0
    last_review_ms: int | None = None

    def add_card(
        self,
        *,
        note_id: int,
        interval: int,
        reps: int,
        reviews: int,
        last_review_ms: int | None,
    ) -> None:
        self.note_ids.add(note_id)
        self.cards += 1
        self.mature += int(interval > 21)
        self.reps += reps
        self.reviews += reviews
        if last_review_ms is not None and (
            self.last_review_ms is None or last_review_ms > self.last_review_ms
        ):
            self.last_review_ms = last_review_ms


@dataclasses.dataclass(frozen=True)
class ContentIndex:
    exercise_prompts: dict[str, frozenset[str]]
    exercise_pairs: dict[str, frozenset[tuple[str, str]]]
    grammar_sentences: dict[str, frozenset[str]]
    grammar_glosses: dict[str, frozenset[str]]
    grammar_pairs: dict[str, frozenset[tuple[str, str]]]
    tenses: frozenset[tuple[str, str, str]]


def normalize_text(value: str) -> str:
    """Normalize text for conservative exact-content comparison."""

    value = SOUND_RE.sub(" ", value)
    value = HTML_RE.sub(" ", value)
    value = html.unescape(value).replace("\xa0", " ")
    value = unicodedata.normalize("NFKC", value).casefold()
    return SPACE_RE.sub(" ", value).strip()


def _lexical_text(value: str) -> str:
    """Return normalized letter tokens, ignoring punctuation deterministically."""

    return " ".join(WORD_RE.findall(normalize_text(value)))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_components(path: Path, root: Path) -> Iterator[Path]:
    current = root
    yield current
    for part in path.relative_to(root).parts:
        current = current / part
        yield current


def validate_collection_path(
    raw_path: Path,
    *,
    work_root: Path = DEFAULT_WORK_ROOT,
) -> Path:
    """Prove that ``raw_path`` is a physical, settled SQLite work copy."""

    work_root = work_root.expanduser().resolve(strict=True)
    if work_root.is_symlink() or not work_root.is_dir():
        raise AuditError(f"invalid legacy-estate work root: {work_root}")

    expanded = raw_path.expanduser()
    if expanded.is_symlink():
        raise AuditError(f"collection copy must not be a symlink: {expanded}")
    path = expanded.resolve(strict=True)
    try:
        path.relative_to(work_root)
    except ValueError as error:
        raise AuditError(f"collection must remain beneath {work_root}") from error
    for component in _relative_components(path, work_root):
        if component.is_symlink():
            raise AuditError(f"symlink component is forbidden: {component}")
    if not path.is_file():
        raise AuditError(f"collection is not a regular file: {path}")
    if path.stat().st_nlink != 1:
        raise AuditError(f"collection must be a physical single-link copy: {path}")
    with path.open("rb") as handle:
        if handle.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
            raise AuditError(f"collection is not uncompressed SQLite: {path}")
    for suffix in ("-wal", "-journal"):
        sidecar = Path(f"{path}{suffix}")
        if sidecar.is_symlink():
            raise AuditError(f"SQLite sidecar must not be a symlink: {sidecar}")
        if sidecar.exists() and sidecar.stat().st_size:
            raise AuditError(f"collection has a non-empty SQLite sidecar: {sidecar}")
    return path


def read_only_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.create_collation(
        "unicase",
        lambda left, right: (
            (left.casefold() > right.casefold()) - (left.casefold() < right.casefold())
        ),
    )
    return connection


def _validate_schema(connection: sqlite3.Connection) -> None:
    tables = {
        str(row["name"])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    for table, required in REQUIRED_TABLE_COLUMNS.items():
        if table not in tables:
            raise AuditError(f"collection is missing current-schema table {table!r}")
        present = {str(row["name"]) for row in connection.execute(f'PRAGMA table_info("{table}")')}
        missing = sorted(required - present)
        if missing:
            raise AuditError(f"collection table {table!r} lacks columns: {missing}")


def _parse_audited_at(value: str) -> str:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        parsed = dt.datetime.fromisoformat(candidate)
    except ValueError as error:
        raise AuditError("--audited-at must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise AuditError("--audited-at must include a UTC offset or Z")
    return parsed.isoformat(timespec="seconds")


def _iso_review(milliseconds: int | None) -> str | None:
    if milliseconds is None:
        return None
    return (
        dt.datetime.fromtimestamp(milliseconds / 1000, tz=dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _display_deck_name(value: str) -> str:
    return value.replace(DECK_SEPARATOR, "::")


def _field_pair(blob: str) -> tuple[str, str]:
    fields = blob.split(FIELD_SEPARATOR)
    front = normalize_text(fields[0]) if fields else ""
    back = normalize_text(fields[1]) if len(fields) > 1 else ""
    return front, back


def _tag_langs(tags: str) -> frozenset[str]:
    found: set[str] = set()
    for raw in tags.split():
        folded = raw.casefold().strip("_-")
        mapped = LANG_ALIASES.get(folded, folded)
        if mapped in LANG_CODES:
            found.add(mapped)
    return frozenset(found)


def _path_language(deck_path: str) -> tuple[str | None, str | None]:
    folded = deck_path.casefold()
    parts = deck_path.split("::")
    folded_parts = [part.casefold() for part in parts]

    if folded.startswith(("_cn_", "_ct_")) or folded_parts[0] == "spoonfedchinese":
        return "zh", "deck-prefix"
    if folded_parts[0] == "babla" and len(parts) > 1:
        if folded_parts[1].startswith("no_") or folded_parts[1] == "norwegian":
            return "no", "deck-path"
    if folded_parts[0] == "_subtitles" and len(parts) > 1:
        mapped = LANG_ALIASES.get(folded_parts[1])
        if mapped:
            return mapped, "deck-path"
    if folded_parts[0] == "_tenses_old" and len(parts) > 1:
        for word, code in (
            ("german", "de"),
            ("spanish", "es"),
            ("french", "fr"),
            ("italian", "it"),
            ("portuguese", "pt"),
        ):
            if word in folded_parts[1]:
                return code, "deck-path"

    for part in folded_parts[1:] if len(folded_parts) > 1 else folded_parts:
        stripped = part.strip("_-")
        mapped = LANG_ALIASES.get(stripped, stripped)
        if mapped in LANG_CODES:
            return mapped, "deck-path"
        tokens = [token for token in re.split(r"[^a-z]+", stripped) if token]
        for token in tokens:
            mapped = LANG_ALIASES.get(token, token)
            if mapped in LANG_CODES:
                return mapped, "deck-token"

    if folded.startswith("a frequency dictionary of portuguese"):
        return "pt", "deck-title"
    if folded.startswith("a frequency dictionary of spanish"):
        return "es", "deck-title"
    return None, None


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _add_exercise_row(
    prompts: dict[str, set[str]],
    pairs: dict[str, set[tuple[str, str]]],
    *,
    langs: Iterable[str],
    english: object,
    targets: dict[str, object] | None = None,
) -> None:
    if not isinstance(english, str):
        return
    en = normalize_text(english)
    if not en:
        return
    for lang in langs:
        if lang in prompts:
            prompts[lang].add(en)
    for lang, target in (targets or {}).items():
        if lang in pairs and isinstance(target, str):
            normalized_target = normalize_text(target)
            if normalized_target:
                pairs[lang].add((en, normalized_target))


def _completed_frame(row: dict, frame_field: str, answer_field: str) -> str:
    frame = row.get(frame_field)
    answer = row.get(answer_field)
    if not isinstance(frame, str) or not isinstance(answer, str):
        return ""
    if frame.count("___") != 1:
        return ""
    # German citation hints belong to the exercise prompt, not the completed
    # sentence: ``___ (das Ministerium)`` becomes ``dem Ministerium``.
    with_answer = re.sub(r"___\s*\([^()]++\)", answer, frame, count=1)
    if with_answer == frame:
        with_answer = frame.replace("___", answer, 1)
    return normalize_text(with_answer)


def _load_grammar_content(
    repo_root: Path,
) -> tuple[
    dict[str, frozenset[str]],
    dict[str, frozenset[str]],
    dict[str, frozenset[tuple[str, str]]],
]:
    sentences: dict[str, set[str]] = {lang: set() for lang in CURRICULUM_LANGS}
    glosses: dict[str, set[str]] = {lang: set() for lang in CURRICULUM_LANGS}
    pairs: dict[str, set[tuple[str, str]]] = {lang: set() for lang in CURRICULUM_LANGS}
    base = repo_root / "idiomatic" / "grammar" / "data"
    for lang in CURRICULUM_LANGS:
        for filename in GRAMMAR_BANK_FILES[lang]:
            path = base / filename
            if not path.is_file():
                raise AuditError(f"committed grammar bank is missing: {path}")
            data = _load_json(path)
            if not isinstance(data, list):
                raise AuditError(f"committed grammar bank is not a JSON array: {path}")
            for row in data:
                if not isinstance(row, dict) or "_meta" in row:
                    continue

                row_sentences: set[str] = set()
                for field in GRAMMAR_SENTENCE_FIELDS:
                    value = row.get(field)
                    if isinstance(value, str) and (normalized := normalize_text(value)):
                        row_sentences.add(normalized)
                for frame_field, answer_field in (
                    ("frame", "correct"),
                    ("example_frame", "example_answer"),
                ):
                    if completed := _completed_frame(row, frame_field, answer_field):
                        row_sentences.add(completed)
                sentences[lang].update(row_sentences)

                row_glosses = {
                    normalize_text(value)
                    for field in GRAMMAR_GLOSS_FIELDS
                    if isinstance((value := row.get(field)), str) and normalize_text(value)
                }
                glosses[lang].update(row_glosses)

                # Only pair fields that are explicitly aligned translations;
                # short lexical `en` glosses are not paired with full examples.
                aligned_target = row.get("example_es", row.get("example"))
                aligned_gloss = row.get("example_en")
                if isinstance(aligned_target, str) and isinstance(aligned_gloss, str):
                    target = normalize_text(aligned_target)
                    gloss = normalize_text(aligned_gloss)
                    if target and gloss:
                        pairs[lang].add((gloss, target))
                sentence = row.get("sentence")
                gloss_en = row.get("gloss_en")
                if isinstance(sentence, str) and isinstance(gloss_en, str):
                    target = normalize_text(sentence)
                    gloss = normalize_text(gloss_en)
                    if target and gloss:
                        pairs[lang].add((gloss, target))

    return (
        {lang: frozenset(values) for lang, values in sentences.items()},
        {lang: frozenset(values) for lang, values in glosses.items()},
        {lang: frozenset(values) for lang, values in pairs.items()},
    )


def load_content_index(repo_root: Path = REPO_ROOT) -> ContentIndex:
    """Load conservative exact-match keys from committed content only."""

    prompts: dict[str, set[str]] = {lang: set() for lang in ("de", "es", "fr", "it", "pt")}
    pairs: dict[str, set[tuple[str, str]]] = {
        lang: set() for lang in ("de", "es", "fr", "it", "pt")
    }
    base = repo_root / "idiomatic" / "grammar" / "data" / "exercises2"

    for path in sorted((base / "batches" / "input").glob("*.json")):
        lang = path.name[:2]
        if lang not in prompts:
            continue
        data = _load_json(path)
        if not isinstance(data, list):
            continue
        for row in data:
            if isinstance(row, dict):
                _add_exercise_row(
                    prompts,
                    pairs,
                    langs=(lang,),
                    english=row.get("en"),
                    targets={lang: row.get("old_back")},
                )

    for path in sorted((base / "notes").glob("*.json")):
        lang = path.name[:2]
        if lang not in prompts:
            continue
        data = _load_json(path)
        if not isinstance(data, list):
            continue
        for row in data:
            if not isinstance(row, dict):
                continue
            target = row.get("tl", row.get(f"{lang}_main"))
            _add_exercise_row(
                prompts,
                pairs,
                langs=(lang,),
                english=row.get("en"),
                targets={lang: target},
            )

    # The Italian-rebuild inputs carry the shared English prompt corpus and
    # trusted reference backs from the four surviving legacy languages.
    for path in sorted((base / "it_rebuild" / "input").glob("*.json")):
        data = _load_json(path)
        if not isinstance(data, list):
            continue
        for row in data:
            if not isinstance(row, dict):
                continue
            refs = row.get("refs") if isinstance(row.get("refs"), dict) else {}
            _add_exercise_row(
                prompts,
                pairs,
                langs=prompts,
                english=row.get("en"),
                targets=refs,
            )
    for path in sorted((base / "it_rebuild" / "output").glob("*.json")):
        data = _load_json(path)
        if not isinstance(data, list):
            continue
        for row in data:
            if isinstance(row, dict):
                _add_exercise_row(
                    prompts,
                    pairs,
                    langs=("it",),
                    english=row.get("en"),
                    targets={"it": row.get("it")},
                )

    grammar_sentences, grammar_glosses, grammar_pairs = _load_grammar_content(repo_root)

    tense_path = repo_root / "docs" / "research" / "tenses-profiles" / "tenses_priors.json"
    tense_data = _load_json(tense_path)
    tense_keys: set[tuple[str, str, str]] = set()
    if isinstance(tense_data, dict) and isinstance(tense_data.get("langs"), dict):
        for lang, rows in tense_data["langs"].items():
            if not isinstance(lang, str) or not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                verb = row.get("verb")
                tense = row.get("tense")
                if isinstance(verb, str) and isinstance(tense, str):
                    tense_keys.add((lang, normalize_text(verb), normalize_text(tense)))

    return ContentIndex(
        exercise_prompts={key: frozenset(value) for key, value in prompts.items()},
        exercise_pairs={key: frozenset(value) for key, value in pairs.items()},
        grammar_sentences=grammar_sentences,
        grammar_glosses=grammar_glosses,
        grammar_pairs=grammar_pairs,
        tenses=frozenset(tense_keys),
    )


def _quality_flags(
    note_ids: set[int],
    note_info: dict[int, NoteInfo],
    *,
    lang: str,
    scope: str,
) -> list[dict]:
    empty_front = 0
    empty_back = 0
    exact_front_back_suspects = 0
    wrong_language_suspects: collections.Counter[str] = collections.Counter()
    machine_english_suspects: collections.Counter[str] = collections.Counter()
    drift_suspects: collections.Counter[str] = collections.Counter()
    literal_traps: collections.Counter[str] = collections.Counter()
    by_front: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for note_id in note_ids:
        info = note_info[note_id]
        empty_front += int(not info.front)
        empty_back += int(not info.back)
        if info.front:
            by_front[info.front][info.back] += 1

        front_words = _lexical_text(info.front)
        back_words = _lexical_text(info.back)
        if info.front and info.front == info.back and len(front_words.split()) >= 2:
            exact_front_back_suspects += 1

        if lang in WRONG_LANGUAGE_MARKERS and len(back_words.split()) >= 4:
            tokens = set(back_words.split())
            if not tokens.intersection(WRONG_LANGUAGE_MARKERS[lang]):
                scores = {
                    candidate: len(tokens.intersection(markers))
                    for candidate, markers in WRONG_LANGUAGE_MARKERS.items()
                    if candidate != lang
                }
                best_score = max(scores.values(), default=0)
                best = [code for code, score in scores.items() if score == best_score]
                if best_score >= 2 and len(best) == 1:
                    wrong_language_suspects[best[0]] += 1

        machine_pattern = None
        if front_words == "the technological solutionism":
            machine_pattern = "the-technological-solutionism"
        elif re.match(
            r"^recommend (?:him|her|me|us|them|you) "
            r"(?:that|this|these|those|the|a|an)\b",
            front_words,
        ):
            machine_pattern = "recommend-indirect-object"
        elif re.search(
            r"\bexplain (?:him|her|me|us|them|you) "
            r"(?:that|this|these|those|the|a|an)\b",
            front_words,
        ):
            machine_pattern = "explain-indirect-object"
        if machine_pattern:
            machine_english_suspects[machine_pattern] += 1

        if (
            lang == "pt"
            and front_words.startswith(("they have been championing", "they ve been championing"))
            and back_words.startswith(("os senhores têm defendido", "as senhoras têm defendido"))
        ):
            drift_suspects["pt-they-to-formal-you"] += 1
        elif (
            lang == "es"
            and front_words.startswith(("they have instructed us", "they ve instructed us"))
            and back_words.startswith("nos ha pedido")
        ):
            drift_suspects["es-they-to-singular-verb"] += 1

        literal_key = (lang, front_words, back_words)
        if literal_key in {
            ("es", "nuclear fallout", "la caída nuclear"),
            ("es", "the nuclear fallout", "la caída nuclear"),
        }:
            literal_traps["es-nuclear-fallout"] += 1
        elif literal_key == ("fr", "to fail", "pour échouer"):
            literal_traps["fr-to-fail"] += 1
        elif lang == "pt" and front_words == "accordingly" and back_words.startswith("de acordo"):
            literal_traps["pt-accordingly"] += 1

    duplicate_groups = 0
    duplicate_notes = 0
    conflicting_groups = 0
    conflicting_notes = 0
    exact_duplicate_groups = 0
    exact_duplicate_notes = 0
    for backs in by_front.values():
        total = sum(backs.values())
        if total < 2:
            continue
        duplicate_groups += 1
        duplicate_notes += total
        nonempty_backs = {back for back in backs if back}
        if len(nonempty_backs) > 1:
            conflicting_groups += 1
            conflicting_notes += total
        duplicate_counts = [count for count in backs.values() if count > 1]
        if duplicate_counts:
            exact_duplicate_groups += len(duplicate_counts)
            exact_duplicate_notes += sum(duplicate_counts)

    flags = []
    for code, count, details in (
        ("empty_front", empty_front, None),
        ("empty_back", empty_back, None),
        ("duplicate_front", duplicate_groups, f"{duplicate_notes} notes"),
        (
            "conflicting_back",
            conflicting_groups,
            f"{conflicting_notes} notes",
        ),
        (
            "exact_duplicate",
            exact_duplicate_groups,
            f"{exact_duplicate_notes} notes",
        ),
        (
            "exact_front_back_suspect",
            exact_front_back_suspects,
            "normalized identical fields with >=2 words; untranslated suspect",
        ),
        (
            "suspected_wrong_target_language_back",
            sum(wrong_language_suspects.values()),
            "heuristic suspects by inferred back language: "
            + ", ".join(
                f"{code}={count}" for code, count in sorted(wrong_language_suspects.items())
            )
            + "; requires >=4 words, >=2 distinct markers, and no target-language marker",
        ),
        (
            "documented_machine_english_front_suspect",
            sum(machine_english_suspects.values()),
            "exact §2.4 pattern suspects: "
            + ", ".join(
                f"{code}={count}" for code, count in sorted(machine_english_suspects.items())
            ),
        ),
        (
            "documented_subject_drift_suspect",
            sum(drift_suspects.values()),
            "exact §2.4 subject/number-drift pattern suspects: "
            + ", ".join(f"{code}={count}" for code, count in sorted(drift_suspects.items())),
        ),
        (
            "documented_literal_translation_trap",
            sum(literal_traps.values()),
            "documented §2.4 trap patterns: "
            + ", ".join(f"{code}={count}" for code, count in sorted(literal_traps.items())),
        ),
    ):
        if count:
            flag = {"code": code, "scope": scope, "count": count}
            if details:
                flag["details"] = details
            flags.append(flag)
    return flags


def _note_language_candidates(note_ids: set[int], note_info: dict[int, NoteInfo]) -> set[str]:
    candidates: set[str] = set()
    for note_id in note_ids:
        candidates.update(note_info[note_id].tag_langs)
    return candidates


def _stats_fields(
    accumulator: DeckAccumulator,
    note_info: dict[int, NoteInfo],
) -> dict[str, int | str | None]:
    return {
        "notes": len(accumulator.note_ids),
        "cards": accumulator.cards,
        "mature": accumulator.mature,
        "reps": accumulator.reps,
        "reviews": accumulator.reviews,
        "audio_notes": sum(note_info[note_id].sound_tags > 0 for note_id in accumulator.note_ids),
        "sound_tags": sum(note_info[note_id].sound_tags for note_id in accumulator.note_ids),
        "last_review": _iso_review(accumulator.last_review_ms),
    }


def _model_counts(note_ids: set[int], note_info: dict[int, NoteInfo]) -> collections.Counter[int]:
    return collections.Counter(note_info[note_id].mid for note_id in note_ids)


def _exercise_match_counts(
    note_ids: set[int],
    note_info: dict[int, NoteInfo],
    *,
    lang: str,
    content: ContentIndex,
) -> tuple[int, int]:
    languages: Sequence[str]
    if lang in content.exercise_prompts:
        languages = (lang,)
    else:
        languages = tuple(sorted(content.exercise_prompts))
    prompt_matches = 0
    pair_matches = 0
    for note_id in note_ids:
        info = note_info[note_id]
        matching_langs = [
            code
            for code in languages
            if info.front and info.front in content.exercise_prompts[code]
        ]
        if matching_langs:
            prompt_matches += 1
        if any(
            info.back and (info.front, info.back) in content.exercise_pairs[code]
            for code in matching_langs
        ):
            pair_matches += 1
    return prompt_matches, pair_matches


def _tense_matches(
    note_ids: set[int],
    note_info: dict[int, NoteInfo],
    content: ContentIndex,
) -> int:
    matches = 0
    for note_id in note_ids:
        front = note_info[note_id].front
        match = TENSE_FRONT_RE.match(front)
        if not match:
            continue
        source_lang = match.group("lang")
        key = (
            LANG_ALIASES.get(source_lang, source_lang),
            normalize_text(match.group("verb")),
            normalize_text(match.group("tense") or "(untagged)"),
        )
        matches += int(key in content.tenses)
    return matches


def _grammar_match_counts(
    note_ids: set[int],
    note_info: dict[int, NoteInfo],
    *,
    lang: str,
    content: ContentIndex,
) -> dict[str, tuple[int, int, int]]:
    languages = (lang,) if lang in content.grammar_sentences else CURRICULUM_LANGS
    counts: dict[str, tuple[int, int, int]] = {}
    for code in languages:
        sentence_matches = 0
        gloss_matches = 0
        pair_matches = 0
        for note_id in note_ids:
            info = note_info[note_id]
            fields = {value for value in (info.front, info.back) if value}
            sentence_matches += int(bool(fields.intersection(content.grammar_sentences[code])))
            gloss_matches += int(bool(fields.intersection(content.grammar_glosses[code])))
            pair_matches += int(
                (info.front, info.back) in content.grammar_pairs[code]
                or (info.back, info.front) in content.grammar_pairs[code]
            )
        counts[code] = (sentence_matches, gloss_matches, pair_matches)
    return counts


def _exercise_topics(deck_path: str, descendant_paths: Iterable[str]) -> list[str]:
    if not deck_path.startswith("EXCERCISES"):
        return []
    topics = {
        path.rsplit("::", 1)[-1]
        for path in descendant_paths
        if path.startswith("EXCERCISES::") and path.rsplit("::", 1)[-1] in EXERCISE_TOPIC_STATUS
    }
    if deck_path.rsplit("::", 1)[-1] in EXERCISE_TOPIC_STATUS:
        topics.add(deck_path.rsplit("::", 1)[-1])
    return sorted(topics)


def _overlap_rows(
    *,
    deck_path: str,
    descendant_paths: Iterable[str],
    lang: str,
    direct_note_ids: set[int],
    subtree_note_ids: set[int],
    note_info: dict[int, NoteInfo],
    content: ContentIndex,
) -> list[dict]:
    overlaps: list[dict] = []
    for topic in _exercise_topics(deck_path, descendant_paths):
        status, plan = EXERCISE_TOPIC_STATUS[topic]
        overlaps.append(
            {
                "kind": "exercises2-roadmap",
                "status": status,
                "scope": "subtree",
                "topic": topic.casefold(),
                "details": plan,
            }
        )

    direct_prompts, direct_pairs = _exercise_match_counts(
        direct_note_ids, note_info, lang=lang, content=content
    )
    subtree_prompts, subtree_pairs = _exercise_match_counts(
        subtree_note_ids, note_info, lang=lang, content=content
    )
    for kind, scope, count in (
        ("normalized-exercise-prompt", "direct", direct_prompts),
        ("normalized-exercise-pair", "direct", direct_pairs),
        ("normalized-exercise-prompt", "subtree", subtree_prompts),
        ("normalized-exercise-pair", "subtree", subtree_pairs),
    ):
        if count:
            overlaps.append({"kind": kind, "status": "exact", "scope": scope, "count": count})

    for scope, note_ids in (
        ("direct", direct_note_ids),
        ("subtree", subtree_note_ids),
    ):
        grammar_counts = _grammar_match_counts(note_ids, note_info, lang=lang, content=content)
        for code, (sentence_count, gloss_count, pair_count) in grammar_counts.items():
            for kind, count in (
                ("normalized-grammar-sentence", sentence_count),
                ("normalized-grammar-gloss", gloss_count),
                ("normalized-grammar-pair", pair_count),
            ):
                if count:
                    overlaps.append(
                        {
                            "kind": kind,
                            "status": "exact",
                            "scope": scope,
                            "lang": code,
                            "count": count,
                        }
                    )

    if deck_path.startswith("_tenses_old"):
        overlaps.append(
            {
                "kind": "tenses-profiles",
                "status": "profiled",
                "scope": "subtree",
                "count": _tense_matches(subtree_note_ids, note_info, content),
                "details": "top-60 verb×tense priors per language",
            }
        )
    elif count := _tense_matches(subtree_note_ids, note_info, content):
        overlaps.append(
            {
                "kind": "normalized-tenses-prior",
                "status": "exact",
                "scope": "subtree",
                "count": count,
            }
        )

    if deck_path.startswith("Idiomatic"):
        overlaps.append(
            {
                "kind": "current-pipeline",
                "status": "already-covered",
                "scope": "subtree",
                "details": "stale/misdelivered current-pipeline notes in the +2 account",
            }
        )
    return overlaps


def _settled_fact_codes(deck_path: str) -> list[str]:
    codes: list[str] = []
    if deck_path == "EXCERCISES":
        codes.extend(
            (
                "exercises_it_french_copy",
                "exercises_pt_big_tech_phrases_spanish",
                "exercises_es_false_friends_toxic",
            )
        )
    if deck_path == "EXCERCISES::PT::BIG_TECH_PHRASES":
        codes.append("exercises_pt_big_tech_phrases_spanish")
    if deck_path.startswith("_tenses_old"):
        codes.append("tenses_old_profiled")
    return codes


def _proposed_verdict(deck_path: str, subtree: DeckAccumulator) -> tuple[str, str]:
    folded = deck_path.casefold()
    if deck_path.startswith("EXCERCISES"):
        topic = deck_path.rsplit("::", 1)[-1]
        if topic in {"CONNECTING", "CONDITIONALS"}:
            return (
                "already-covered",
                "Exercises 2.0 waves 1–2 already shipped this topic through the audited rebuild pipeline.",
            )
        if topic in {
            "TENSES",
            "FANCY_VOCAB",
            "BIG_TECH_VOCAB",
            "COLD_WAR_VOCAB",
            "GEOPOLITICS",
            "BIG_TECH_PHRASES",
        }:
            return (
                "import",
                "Exercises 2.0 waves 3–6 already specify an audited rebuild/import lane for this topic.",
            )
        if topic in {"COMMANDS", "PRONOUNS", "REFLEXIVE", "RELFEXIVE", "REFLEXIV"}:
            return (
                "partial",
                "Roadmap disposition is a grammar-overlap gap audit, importing only uncovered material.",
            )
        if topic == "FALSE_FRIENDS":
            return (
                "skip",
                "False friends are rebuild-only Wave 7 territory; legacy cards are not an import source.",
            )
        return (
            "partial",
            "Container has mixed child dispositions; owner verdicts apply to its topic leaves, not wholesale.",
        )
    if deck_path.startswith("_tenses_old"):
        return (
            "already-covered",
            "Study history and paradigms are already captured in committed tenses profiles; source forms still require verification.",
        )
    if deck_path.startswith("Idiomatic"):
        return (
            "already-covered",
            "These are stale/current-pipeline deliveries already represented by the live catalog, not a legacy source to re-import.",
        )
    if not subtree.cards:
        return "skip", "Empty deck shell in the fresh snapshot."
    if folded.startswith("_ct_mt"):
        return (
            "skip",
            "Mass MT-labeled corpus with negligible study history; retain only audit evidence.",
        )
    if folded.startswith("a frequency dictionary of"):
        return (
            "skip",
            "Generic frequency-deck corpus; no meaningful study history justifies estate import.",
        )
    if folded in {"default", "custom study session"} or folded.startswith("recovered"):
        return "skip", "System/recovery residue rather than a coherent import family."
    if folded.startswith("_errors"):
        return (
            "import",
            "Personal error material is high-value learner evidence; preserve provenance and pass through an audited import wave.",
        )
    if folded.startswith("teachee"):
        return (
            "import",
            "Teacher-authored dated material is unique learner evidence and merits a provenance-preserving import wave.",
        )
    if not subtree.reviews:
        return (
            "skip",
            "Never reviewed in the source account; no study-history signal supports importing it wholesale.",
        )
    return (
        "partial",
        "The family has source-account study history, but its size/heterogeneity calls for a studied-and-quality-filtered subset.",
    )


def _descendants(deck_path: str, paths: Iterable[str]) -> list[str]:
    prefix = f"{deck_path}::"
    return [path for path in paths if path == deck_path or path.startswith(prefix)]


def analyze_collection(
    collection_path: Path,
    *,
    audited_at: str,
    work_root: Path = DEFAULT_WORK_ROOT,
    repo_root: Path = REPO_ROOT,
    source_account: str = SOURCE_ACCOUNT,
) -> dict:
    """Return the deterministic manifest without writing any files."""

    path = validate_collection_path(collection_path, work_root=work_root)
    audited_at = _parse_audited_at(audited_at)
    source_sha256 = sha256_file(path)
    content = load_content_index(repo_root)
    connection = read_only_connection(path)
    try:
        quick_check_rows = [str(row[0]) for row in connection.execute("PRAGMA quick_check")]
        if quick_check_rows != ["ok"]:
            raise AuditError(f"SQLite quick_check failed: {quick_check_rows[:10]}")
        _validate_schema(connection)

        deck_paths = {
            int(row["id"]): _display_deck_name(str(row["name"]))
            for row in connection.execute("SELECT id,name FROM decks")
        }
        path_to_id = {name: deck_id for deck_id, name in deck_paths.items()}
        model_names = {
            int(row["id"]): str(row["name"])
            for row in connection.execute("SELECT id,name FROM notetypes")
        }
        model_fields: dict[int, list[str]] = collections.defaultdict(list)
        for row in connection.execute("SELECT ntid,name FROM fields ORDER BY ntid,ord"):
            model_fields[int(row["ntid"])].append(str(row["name"]))
        model_templates: dict[int, list[str]] = collections.defaultdict(list)
        for row in connection.execute("SELECT ntid,name FROM templates ORDER BY ntid,ord"):
            model_templates[int(row["ntid"])].append(str(row["name"]))

        note_info: dict[int, NoteInfo] = {}
        for row in connection.execute("SELECT id,mid,tags,flds FROM notes ORDER BY id"):
            front, back = _field_pair(str(row["flds"]))
            blob = str(row["flds"])
            note_info[int(row["id"])] = NoteInfo(
                mid=int(row["mid"]),
                front=front,
                back=back,
                sound_tags=len(SOUND_RE.findall(blob)),
                tag_langs=_tag_langs(str(row["tags"])),
            )

        review_by_card = {
            int(row["cid"]): (int(row["reviews"]), int(row["last_review"]))
            for row in connection.execute(
                "SELECT cid,COUNT(*) AS reviews,MAX(id) AS last_review FROM revlog GROUP BY cid"
            )
        }
        direct = {deck_id: DeckAccumulator() for deck_id in deck_paths}
        subtree = {deck_id: DeckAccumulator() for deck_id in deck_paths}
        ancestors_by_id: dict[int, list[int]] = {}
        for deck_id, deck_path in deck_paths.items():
            parts = deck_path.split("::")
            ancestors_by_id[deck_id] = [
                path_to_id[name]
                for length in range(1, len(parts) + 1)
                if (name := "::".join(parts[:length])) in path_to_id
            ]

        for row in connection.execute("SELECT id,nid,did,ivl,reps FROM cards ORDER BY id"):
            card_id = int(row["id"])
            note_id = int(row["nid"])
            deck_id = int(row["did"])
            if deck_id not in deck_paths:
                raise AuditError(f"card {card_id} references unknown deck {deck_id}")
            if note_id not in note_info:
                raise AuditError(f"card {card_id} references unknown note {note_id}")
            reviews, last_review = review_by_card.get(card_id, (0, None))
            kwargs = {
                "note_id": note_id,
                "interval": int(row["ivl"]),
                "reps": int(row["reps"]),
                "reviews": reviews,
                "last_review_ms": last_review,
            }
            direct[deck_id].add_card(**kwargs)
            for ancestor_id in ancestors_by_id[deck_id]:
                subtree[ancestor_id].add_card(**kwargs)

        # Infer language path-first, then unambiguous note tags, then children.
        languages: dict[int, tuple[str, str]] = {}
        for deck_id, deck_path in deck_paths.items():
            language, basis = _path_language(deck_path)
            if language:
                languages[deck_id] = (language, basis or "deck-path")
                continue
            candidates = _note_language_candidates(direct[deck_id].note_ids, note_info)
            if len(candidates) == 1:
                languages[deck_id] = (next(iter(candidates)), "note-tags")
            elif len(candidates) > 1:
                languages[deck_id] = ("multi", "note-tags")
        for deck_id, deck_path in sorted(
            deck_paths.items(), key=lambda item: item[1].count("::"), reverse=True
        ):
            if deck_id in languages:
                continue
            child_langs = {
                languages[other_id][0]
                for other_id, other_path in deck_paths.items()
                if other_path.startswith(f"{deck_path}::")
                and other_id in languages
                and languages[other_id][0] not in {"und", "multi"}
            }
            if len(child_langs) == 1:
                languages[deck_id] = (next(iter(child_langs)), "descendant-decks")
            elif len(child_langs) > 1:
                languages[deck_id] = ("multi", "descendant-decks")
            else:
                languages[deck_id] = ("und", "unresolved")

        global_model_notes = _model_counts(set(note_info), note_info)
        global_model_cards: collections.Counter[int] = collections.Counter()
        model_decks: dict[int, set[int]] = collections.defaultdict(set)
        for deck_id, accumulator in direct.items():
            counts = _model_counts(accumulator.note_ids, note_info)
            for model_id, count in counts.items():
                model_decks[model_id].add(deck_id)
                # Multiple cards for one note are intentionally counted below.
                del count
        for row in connection.execute(
            "SELECT n.mid,COUNT(*) AS cards FROM cards c JOIN notes n ON n.id=c.nid GROUP BY n.mid"
        ):
            global_model_cards[int(row["mid"])] = int(row["cards"])

        models = []
        for model_id, name in sorted(
            model_names.items(), key=lambda item: (item[1].casefold(), item[0])
        ):
            models.append(
                {
                    "id": model_id,
                    "name": name,
                    "fields": model_fields.get(model_id, []),
                    "templates": model_templates.get(model_id, []),
                    "notes": global_model_notes.get(model_id, 0),
                    "cards": global_model_cards.get(model_id, 0),
                    "deck_count": len(model_decks.get(model_id, set())),
                }
            )

        rows = []
        all_paths = sorted(
            deck_paths.values(), key=lambda value: [part.casefold() for part in value.split("::")]
        )
        for deck_id, deck_path in sorted(
            deck_paths.items(), key=lambda item: [part.casefold() for part in item[1].split("::")]
        ):
            direct_stats = _stats_fields(direct[deck_id], note_info)
            subtree_stats = _stats_fields(subtree[deck_id], note_info)
            language, language_basis = languages[deck_id]
            direct_models = _model_counts(direct[deck_id].note_ids, note_info)
            subtree_models = _model_counts(subtree[deck_id].note_ids, note_info)
            note_models = [
                {
                    "id": model_id,
                    "name": model_names.get(model_id, f"unknown:{model_id}"),
                    "direct_notes": direct_models.get(model_id, 0),
                    "subtree_notes": subtree_models.get(model_id, 0),
                }
                for model_id in sorted(
                    subtree_models,
                    key=lambda value: (model_names.get(value, "").casefold(), value),
                )
            ]
            descendant_paths = _descendants(deck_path, all_paths)
            verdict, reason = _proposed_verdict(deck_path, subtree[deck_id])
            if verdict not in VERDICTS:
                raise AssertionError(f"unknown verdict {verdict}")
            parts = deck_path.split("::")
            row = {
                "source_deck_id": deck_id,
                "deck_path": deck_path,
                "parent_path": "::".join(parts[:-1]) if len(parts) > 1 else None,
                "depth": len(parts) - 1,
                "top_level": parts[0],
                "lang": language,
                "language_basis": language_basis,
            }
            for prefix, values in (("direct", direct_stats), ("subtree", subtree_stats)):
                for key, value in values.items():
                    row[f"{prefix}_{key}"] = value
            row.update(
                {
                    "note_models": note_models,
                    "quality_flags": _quality_flags(
                        direct[deck_id].note_ids,
                        note_info,
                        lang=language,
                        scope="direct",
                    )
                    + _quality_flags(
                        subtree[deck_id].note_ids,
                        note_info,
                        lang=language,
                        scope="subtree",
                    ),
                    "overlap": _overlap_rows(
                        deck_path=deck_path,
                        descendant_paths=descendant_paths,
                        lang=language,
                        direct_note_ids=direct[deck_id].note_ids,
                        subtree_note_ids=subtree[deck_id].note_ids,
                        note_info=note_info,
                        content=content,
                    ),
                    "settled_facts": _settled_fact_codes(deck_path),
                    "proposed_verdict": verdict,
                    "proposal_reason": reason,
                }
            )
            rows.append(row)

        total_revlog = int(connection.execute("SELECT COUNT(*) FROM revlog").fetchone()[0])
        attributed_reviews = int(
            connection.execute(
                "SELECT COUNT(*) FROM revlog WHERE cid IN (SELECT id FROM cards)"
            ).fetchone()[0]
        )
        total_sound_tags = sum(info.sound_tags for info in note_info.values())
        max_review = connection.execute("SELECT MAX(id) FROM revlog").fetchone()[0]
        totals = {
            "deck_rows": len(deck_paths),
            "top_level_decks": sum("::" not in path for path in deck_paths.values()),
            "note_models": len(model_names),
            "notes": len(note_info),
            "cards": int(connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]),
            "mature_cards": int(
                connection.execute("SELECT COUNT(*) FROM cards WHERE ivl > 21").fetchone()[0]
            ),
            "card_reps": int(
                connection.execute("SELECT COALESCE(SUM(reps),0) FROM cards").fetchone()[0]
            ),
            "review_rows": total_revlog,
            "attributed_review_rows": attributed_reviews,
            "orphaned_review_rows": total_revlog - attributed_reviews,
            "last_review": _iso_review(int(max_review)) if max_review is not None else None,
            "audio_notes": sum(info.sound_tags > 0 for info in note_info.values()),
            "sound_tags": total_sound_tags,
            "new_cards": int(
                connection.execute("SELECT COUNT(*) FROM cards WHERE type=0").fetchone()[0]
            ),
            "learning_or_relearning_cards": int(
                connection.execute("SELECT COUNT(*) FROM cards WHERE type IN (1,3)").fetchone()[0]
            ),
            "review_state_cards": int(
                connection.execute("SELECT COUNT(*) FROM cards WHERE type=2").fetchone()[0]
            ),
            "suspended_cards": int(
                connection.execute("SELECT COUNT(*) FROM cards WHERE queue=-1").fetchone()[0]
            ),
            "filtered_deck_cards": int(
                connection.execute(
                    "SELECT COUNT(*) FROM cards WHERE odid != 0 OR odue != 0"
                ).fetchone()[0]
            ),
        }
    finally:
        connection.close()

    try:
        source_path = path.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        source_path = path.name
    return {
        "snapshot": {
            "source_account": source_account,
            "source_path": source_path,
            "source_sha256": source_sha256,
            "source_bytes": path.stat().st_size,
            "audited_at": audited_at,
            "quick_check": "ok",
            "audio_measure": "[sound:] references in note fields; media files were not synced",
            "settled_facts": list(SETTLED_FACTS),
        },
        "totals": totals,
        "models": models,
        "rows": rows,
    }


def manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def _md(value: object) -> str:
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _flag_summary(flags: list[dict]) -> str:
    return "; ".join(f"{flag['scope'][0]}:{flag['code']}={flag['count']}" for flag in flags) or "—"


def _overlap_summary(overlaps: list[dict]) -> str:
    items = []
    for overlap in overlaps:
        label = f"{overlap['kind']}:{overlap['status']}"
        if "lang" in overlap:
            label += f":{overlap['lang']}"
        if "topic" in overlap:
            label += f":{overlap['topic']}"
        if "count" in overlap:
            label += f"={overlap['count']}"
        items.append(label)
    return "; ".join(items) or "—"


def render_summary(manifest: dict) -> str:
    snapshot = manifest["snapshot"]
    totals = manifest["totals"]
    rows = manifest["rows"]
    verdicts = collections.Counter(row["proposed_verdict"] for row in rows)
    top_rows = [row for row in rows if row["depth"] == 0]
    lines = [
        "# Legacy +2 estate — audit summary",
        "",
        f"Audited `{snapshot['source_path']}` at `{snapshot['audited_at']}`.",
        f"Source SHA-256: `{snapshot['source_sha256']}`; SQLite quick-check: **ok**.",
        "",
        "This is a read-only inventory. Audio means a `[sound:]` reference in note fields; "
        "media files were deliberately not downloaded. Review counts attributed to decks exclude "
        "orphaned revlog rows whose cards no longer exist.",
        "",
        "## Totals",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in totals.items():
        lines.append(f"| {_md(key)} | {_md(f'{value:,}' if isinstance(value, int) else value)} |")
    lines.extend(
        [
            "",
            "## Proposed verdicts",
            "",
            "| Verdict | Deck rows |",
            "|---|---:|",
        ]
    )
    for verdict in VERDICTS:
        lines.append(f"| {verdict} | {verdicts[verdict]:,} |")
    lines.extend(
        [
            "",
            "## Top-level estate",
            "",
            "| Deck | Lang | Notes | Cards | Mature | Reps | Reviews | Audio notes | Last review | Proposal |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in top_rows:
        lines.append(
            "| "
            + " | ".join(
                _md(value)
                for value in (
                    row["deck_path"],
                    row["lang"],
                    f"{row['subtree_notes']:,}",
                    f"{row['subtree_cards']:,}",
                    f"{row['subtree_mature']:,}",
                    f"{row['subtree_reps']:,}",
                    f"{row['subtree_reviews']:,}",
                    f"{row['subtree_audio_notes']:,}",
                    row["subtree_last_review"],
                    row["proposed_verdict"],
                )
            )
            + " |"
        )
    lines.extend(["", "## Settled findings (not re-litigated)", ""])
    for fact in snapshot["settled_facts"]:
        lines.append(f"- **{fact['code']}** — {fact['finding']}")
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `manifest.json` — DB-seedable canonical evidence",
            "- `DECKS.md` — every deck row with direct and subtree measures",
            "- `MODELS.md` — complete note-model catalog",
            "",
        ]
    )
    return "\n".join(lines)


def render_decks(manifest: dict) -> str:
    lines = [
        "# Legacy +2 estate — all deck rows",
        "",
        f"Generated from source SHA-256 `{manifest['snapshot']['source_sha256']}`. "
        f"All {manifest['totals']['deck_rows']:,} Anki deck rows appear exactly once.",
        "",
        "`d:` and `s:` in Quality mean direct and subtree scope. Suspect/heuristic flags are "
        "triage signals, not automated translation verdicts. Exact normalized overlap is "
        "mechanical evidence, not a semantic identity claim; grammar overlap labels include "
        "their indexed language.",
        "",
        "| Deck | Lang | Direct notes/cards | Subtree notes/cards | Mature | Reps | Reviews | Audio notes / sound tags | Last review | Models | Quality | Overlap | Proposal | Reason |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for row in manifest["rows"]:
        indent = "↳ " * row["depth"]
        model_names = ", ".join(model["name"] for model in row["note_models"]) or "—"
        lines.append(
            "| "
            + " | ".join(
                _md(value)
                for value in (
                    f"{indent}{row['deck_path']}",
                    row["lang"],
                    f"{row['direct_notes']:,}/{row['direct_cards']:,}",
                    f"{row['subtree_notes']:,}/{row['subtree_cards']:,}",
                    f"{row['subtree_mature']:,}",
                    f"{row['subtree_reps']:,}",
                    f"{row['subtree_reviews']:,}",
                    f"{row['subtree_audio_notes']:,}/{row['subtree_sound_tags']:,}",
                    row["subtree_last_review"],
                    model_names,
                    _flag_summary(row["quality_flags"]),
                    _overlap_summary(row["overlap"]),
                    row["proposed_verdict"],
                    row["proposal_reason"],
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_models(manifest: dict) -> str:
    lines = [
        "# Legacy +2 estate — note models",
        "",
        f"Complete catalog of {manifest['totals']['note_models']:,} note models from source "
        f"SHA-256 `{manifest['snapshot']['source_sha256']}`.",
        "",
        "| Model (ID) | Notes | Cards | Decks | Fields in stored order | Templates |",
        "|---|---:|---:|---:|---|---|",
    ]
    for model in manifest["models"]:
        lines.append(
            "| "
            + " | ".join(
                _md(value)
                for value in (
                    f"{model['name']} ({model['id']})",
                    f"{model['notes']:,}",
                    f"{model['cards']:,}",
                    f"{model['deck_count']:,}",
                    " · ".join(model["fields"]) or "—",
                    " · ".join(model["templates"]) or "—",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def validate_output_dir(
    raw_path: Path,
    *,
    output_root: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    output_root = output_root.expanduser().resolve(strict=False)
    path = raw_path.expanduser().resolve(strict=False)
    if raw_path.is_symlink() or path != output_root:
        raise AuditError(f"artifacts must be written to exactly {output_root}")
    if path.exists() and not path.is_dir():
        raise AuditError(f"artifact target is not a directory: {path}")
    return path


def write_artifacts(manifest: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "manifest.json": manifest_json(manifest),
        "SUMMARY.md": render_summary(manifest),
        "DECKS.md": render_decks(manifest),
        "MODELS.md": render_models(manifest),
    }
    for filename, content in files.items():
        path = output_dir / filename
        if path.is_symlink():
            raise AuditError(f"refusing to overwrite symlink artifact: {path}")
        path.write_text(content, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True, type=Path)
    parser.add_argument(
        "--audited-at",
        required=True,
        help="Stable ISO-8601 evidence timestamp, including timezone.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-account", default=SOURCE_ACCOUNT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        output_dir = validate_output_dir(args.output_dir)
        manifest = analyze_collection(
            args.collection,
            audited_at=args.audited_at,
            source_account=args.source_account,
        )
        write_artifacts(manifest, output_dir)
    except AuditError as error:
        raise SystemExit(f"legacy estate audit refused: {error}") from error
    print(
        f"audited {manifest['totals']['deck_rows']} deck rows / "
        f"{manifest['totals']['cards']} cards -> {output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
