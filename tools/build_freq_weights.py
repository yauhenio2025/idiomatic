#!/usr/bin/env python3
"""Build per-unit tense/person frequency weights for grammar drills.

The builder downloads pinned per-form frequency resources, joins them to the
live morphology-backed curriculum, and emits only normalized aggregate JSON.
Raw sources are cached outside the repository and can be reused with
``--offline``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from idiomatic.grammar import morphology  # noqa: E402
from idiomatic.grammar.curriculum import Topic, topics_for  # noqa: E402


LANGS = ("es", "fr", "it", "pt")


@dataclass(frozen=True)
class Source:
    name: str
    version: str
    url: str
    project_url: str
    cache_filename: str
    sha256: str
    parser: str
    corpus: str
    frequency_field: str
    citation: str
    license: str
    license_url: str
    license_note: str
    selection_note: str


SOURCES = {
    "es": Source(
        name="SUBTLEX-ESP",
        version="OSF snapshot, file modified 2023-04-22",
        url="https://osf.io/download/fxt57/",
        project_url="https://osf.io/xp6sz/",
        cache_filename="SUBTLEX-ESP.xlsx",
        sha256="6e7b099ca87efa28c16bb1aafd51fc9e383182210f1bca621b7fd9b137657acb",
        parser="subtlex_es_xlsx",
        corpus="Spanish film-subtitle word forms",
        frequency_field="Freq. count",
        citation=(
            "Cuetos, Glez-Nosti, Barbón & Brysbaert (2011), SUBTLEX-ESP: "
            "Spanish word frequencies based on film subtitles, Psicológica "
            "32:133-143"
        ),
        license="OSF bundle carries a CC BY-NC-SA 4.0 notice",
        license_url="https://osf.io/download/xk2p8/",
        license_note=(
            "The notice is in the OSF bundle; its scope over the frequency "
            "spreadsheet was not independently confirmed; legacy distributions "
            "have also been described as CC BY-NC-ND 3.0."
        ),
        selection_note=(
            "Direct Spanish subtitle list. The distributed spreadsheet omits "
            "hapaxes, so a missing form means no usable evidence, not a known "
            "corpus count of zero."
        ),
    ),
    "fr": Source(
        name="Lexique 4.00",
        version="Lexique400.zip, published 2026-05-20",
        url="https://www.lexique.org/databases/Lexique400/Lexique400.zip",
        project_url="https://www.lexique.org/",
        cache_filename="Lexique400.zip",
        sha256="8ed5a64373ae798f0485a2a35848c09286b6694c6859abeaab6806594c046993",
        parser="lexique4_zip",
        corpus="316-million-token French subtitle corpus",
        frequency_field=("10_FreqMot (summed VER/AUX lemma-analysis occurrences per million)"),
        citation=(
            "New, Pallier, Schalchli, Bourgin & Gimenes (2026), Lexique 4: A "
            "major upgrade of the Lexique French lexical database, Behavior "
            "Research Methods 58(5):140"
        ),
        license="CC BY-SA 4.0",
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
        license_note="Lexique 4 is distributed under CC BY-SA 4.0.",
        selection_note=(
            "Lemma- and POS-tagged subtitle frequencies allow VER/AUX rows for "
            "the target lemma to be separated from noun/adjective homographs."
        ),
    ),
    "it": Source(
        name="hermitdave/FrequencyWords Italian full list",
        version="OpenSubtitles 2018; commit 525f9b560de45753a5ea01069454e72e9aa541c6",
        url=(
            "https://raw.githubusercontent.com/hermitdave/FrequencyWords/"
            "525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/it/it_full.txt"
        ),
        project_url=(
            "https://github.com/hermitdave/FrequencyWords/tree/"
            "525f9b560de45753a5ea01069454e72e9aa541c6"
        ),
        cache_filename="frequencywords-2018-it-full.txt",
        sha256="b23b0c6a3f59c1da1c7caa667b9df5699e95323fee20a05f343c7d7dae73c4be",
        parser="frequency_words",
        corpus="OPUS OpenSubtitles 2018 Italian snapshot",
        frequency_field="raw token count",
        citation=(
            "hermitdave/FrequencyWords, OpenSubtitles 2018 snapshot, commit "
            "525f9b560de45753a5ea01069454e72e9aa541c6"
        ),
        license="CC BY-SA 4.0 for generated list content; generator code MIT",
        license_url=(
            "https://github.com/hermitdave/FrequencyWords/blob/"
            "525f9b560de45753a5ea01069454e72e9aa541c6/README.md#license"
        ),
        license_note=(
            "The repository license does not establish ownership of every "
            "underlying subtitle; OPUS publishes a notice-and-takedown policy."
        ),
        selection_note=(
            "Documented untagged fallback because no stable, license-explicit "
            "direct SUBTLEX-IT download was pinned."
        ),
    ),
    "pt": Source(
        name="SUBTLEX-PT-BR",
        version="CD>2 alphabetic spellcheck-true OSF list, modified 2025-04-22",
        url="https://osf.io/download/3r5j8/",
        project_url="https://osf.io/vb5yp/",
        cache_filename="SUBTLEX_PT-BR_CDAbove2_Alpha_SpellcheckTrue.tsv",
        sha256="766322bcce39df959886d9352b57aaa625232317c4e83d051b35b62d406461b6",
        parser="subtlex_pt_tsv",
        corpus="61,609,241-token Brazilian Portuguese film-subtitle corpus",
        frequency_field="FREQcount",
        citation=(
            "Tang (2012), A 61 Million Word Corpus of Brazilian Portuguese Film "
            "Subtitles as a Resource for Linguistic Research, UCL Working Papers "
            "in Linguistics 24:208-214"
        ),
        license="CC BY-NC-ND 4.0",
        license_url="https://www.kevintang.org/Tools.html",
        license_note="The source author labels this resource CC BY-NC-ND 4.0.",
        selection_note=(
            "Direct Brazilian subtitle list filtered to CD>2, alphabetic, and "
            "spellcheck-true rows; filtering reduces but cannot remove corpus noise."
        ),
    ),
}


MORPHOLOGY_SOURCES = {
    "es": {
        "name": "Fred Jehle Spanish Verb Database (vendored table)",
        "url": "https://github.com/ghidinelli/fred-jehle-spanish-verbs",
        "license": "CC BY-NC-SA 3.0",
        "license_url": (
            "https://github.com/ghidinelli/fred-jehle-spanish-verbs/blob/master/license.txt"
        ),
    },
    "fr": {
        "name": "verbecc French table, credited upstream to Verbiste (vendored)",
        "url": "https://github.com/bretttolbert/verbecc",
        "license": ("French XML declares GPL-2.0-or-later; verbecc package code is LGPL-3.0"),
        "license_url": (
            "https://github.com/bretttolbert/verbecc/blob/main/verbecc/"
            "data/xml/conjugations/conjugations-fr.xml"
        ),
    },
    "it": {
        "name": "verbecc Italian table, credited upstream to mlconjug (vendored)",
        "url": "https://github.com/bretttolbert/verbecc",
        "license": (
            "verbecc package code is LGPL-3.0; Italian XML credits mlconjug "
            "and its model/data lineage is not resolved by a per-file license header"
        ),
        "license_url": (
            "https://github.com/bretttolbert/verbecc/blob/main/verbecc/"
            "data/xml/conjugations/conjugations-it.xml"
        ),
    },
    "pt": {
        "name": "verbecc Portuguese table, credited upstream to mlconjug (vendored)",
        "url": "https://github.com/bretttolbert/verbecc",
        "license": (
            "verbecc package code is LGPL-3.0; Portuguese XML credits mlconjug "
            "and its model/data lineage is not resolved by a per-file license header"
        ),
        "license_url": (
            "https://github.com/bretttolbert/verbecc/blob/main/verbecc/"
            "data/xml/conjugations/conjugations-pt.xml"
        ),
    },
}


# These are reviewed high-risk candidates, not a claim to exhaustively tag an
# untagged corpus. Only tokens that occur in emitted cells are reported in the
# JSON metadata. The 0.10 factor
# intentionally prefers underweighting over copying a cross-POS, cross-lemma,
# or cross-mood count into a target cell.  French does not need this list
# because Lexique 4 supplies POS+lemma analysis frequencies.
UNTAGGED_HOMOGRAPHS = {
    "es": frozenset(
        {
            "como",
            "crea",
            "creamos",
            "crean",
            "creas",
            "creáis",
            "cuenta",
            "era",
            "fuera",
            "para",
            "sal",
            "sienta",
            "sientan",
            "sientas",
            "vino",
            "viste",
        }
    ),
    "it": frozenset(
        {
            "conto",
            "dai",
            "danno",
            "era",
            "fa",
            "parte",
            "porta",
            "sale",
            "sei",
            "stati",
            "stato",
        }
    ),
    "pt": frozenset(
        {
            "como",
            "conta",
            "era",
            "estado",
            "para",
            "rio",
            "vamos",
            "virem",
            "virmos",
        }
    ),
}
HOMOGRAPH_FACTOR = 0.10

# These Spanish subjunctive/command surfaces of crear are also ordinary
# present-indicative forms of creer.  In particular, the negative-command
# proxy ``no crees`` cannot distinguish "do not create" from the much more
# common "you do not believe" using unigram counts.  Zero is the deliberately
# conservative allocation for an unresolved cross-lemma collision.
UNTAGGED_ZERO_HOMOGRAPHS = {
    "es": frozenset({"cree", "crees", "creemos", "creéis", "creen"}),
}

PT_PERSONS = ("1s", "3s", "1p", "3p")
ES_TOPIC_PERSONS = {
    "es_cmd_tu": ("2s",),
    "es_cmd_usted": ("3s", "1p", "3p"),
    "es_cmd_neg": ("2s", "3s", "3p"),
}

COMPOUND_UNITS = frozenset(
    {
        "es_perfecto",
        "es_cmd_neg",
        "es_cond_perf",
        "es_plusc_subj",
        "fr_passe_compose",
        "it_passato_prossimo",
    }
)

EXPECTED_COVERAGE = {
    "es": (13, 4_160, 0),
    "fr": (7, 818, 22),
    "it": (7, 840, 0),
    "pt": (7, 560, 0),
}

MORPHOLOGY_FILES = {
    "es": ROOT / "idiomatic" / "grammar" / "data" / "es_verbs_jehle.csv.gz",
    "fr": ROOT / "idiomatic" / "grammar" / "data" / "fr_verbs_verbecc.json.gz",
    "it": ROOT / "idiomatic" / "grammar" / "data" / "it_verbs_verbecc.json.gz",
    "pt": ROOT / "idiomatic" / "grammar" / "data" / "pt_verbs_verbecc.json.gz",
}


@dataclass(frozen=True)
class Cell:
    unit: str
    verb: str
    mood: str
    tense: str
    person: str
    surface: str
    variants: tuple[str, ...]

    @property
    def analysis(self) -> tuple[str, str, str, str]:
        return (self.verb, self.mood, self.tense, self.person)


@dataclass
class FrequencyData:
    # For untagged lists, surface_counts contains all orthographic counts.
    # For Lexique 4 it contains the sum of VER/AUX rows and lemma_counts is
    # the more precise lookup used by the join. AUX is included because uses
    # of avoir/etre as auxiliaries are still occurrences of the target form.
    surface_counts: dict[str, float]
    lemma_counts: dict[tuple[str, str], float] | None = None

    @property
    def lemma_tagged(self) -> bool:
        return self.lemma_counts is not None

    def count(self, token: str, lemma: str | None) -> float:
        if self.lemma_counts is not None and lemma is not None:
            return self.lemma_counts.get((_norm(token), _norm(lemma)), 0.0)
        return self.surface_counts.get(_norm(token), 0.0)


@dataclass
class BuildResult:
    output: dict[str, object]
    cells: list[Cell]
    scores: dict[Cell, float]
    weights: dict[Cell, float]


def _norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _tokens(surface: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for raw in _norm(surface).split():
        token = raw.strip(".,;:!?¡¿\"'«»()[]{}")
        if token:
            tokens.append(token)
    return tuple(tokens)


@lru_cache(maxsize=len(LANGS))
def _known_infinitives(lang: str) -> frozenset[str]:
    """Infinitives in the vendored morphology table for conservative joins."""
    if lang == "es":
        return frozenset(_norm(verb) for verb in morphology.known_verbs(lang))
    if lang in {"fr", "it", "pt"}:
        # The builder already depends on these exact vendored verbecc tables;
        # their keys are the complete local infinitive inventory.
        return frozenset(_norm(verb) for verb in morphology._load_verbecc(lang))
    return frozenset()


def _surface_variants(surface: str) -> tuple[str, ...]:
    """Expand verbecc slash alternatives, including shared auxiliaries.

    ``faccio/fo`` becomes two simple variants.  ``sono rimasto/rimaso``
    becomes ``sono rimasto`` and ``sono rimaso`` rather than the invalid bare
    second participle.
    """
    normalized = _norm(surface)
    parts = tuple(part for part in re.split(r"\s*/\s*", normalized) if part)
    if len(parts) <= 1:
        return parts
    first_tokens = parts[0].split()
    prefix = first_tokens[:-1]
    variants = [parts[0]]
    for part in parts[1:]:
        if prefix and len(part.split()) == 1:
            variants.append(" ".join([*prefix, part]))
        else:
            variants.append(part)
    return tuple(dict.fromkeys(variants))


def _eligible_persons(topic: Topic) -> tuple[str, ...]:
    if topic.lang == "pt":
        return PT_PERSONS
    return ES_TOPIC_PERSONS.get(topic.key, morphology.PERSONS)


def _morphology_topics(lang: str) -> Iterator[Topic]:
    for topic in topics_for(lang):
        if topic.verify != "morph":
            continue
        if not topic.mood or not topic.tense:
            raise RuntimeError(f"morphology-backed topic lacks mood/tense: {topic.key}")
        yield topic


def curriculum_cells(lang: str) -> tuple[list[Cell], dict[str, list[str]], int]:
    cells: list[Cell] = []
    units: dict[str, list[str]] = {}
    missing_morphology = 0
    for topic in _morphology_topics(lang):
        units[topic.key] = list(topic.verbs)
        for verb in topic.verbs:
            for person in _eligible_persons(topic):
                surface = morphology.lookup(lang, verb, topic.mood, topic.tense, person)
                # A few defective verbecc cells contain a literal "-".
                if not surface or not any(character.isalpha() for character in surface):
                    missing_morphology += 1
                    continue
                variants = _surface_variants(surface)
                if not variants:
                    missing_morphology += 1
                    continue
                cells.append(
                    Cell(
                        topic.key,
                        verb,
                        topic.mood,
                        topic.tense,
                        person,
                        _norm(surface),
                        variants,
                    )
                )
    return cells, units, missing_morphology


def source_path(cache_dir: Path, source: Source) -> Path:
    return cache_dir / source.sha256[:12] / source.cache_filename


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_json(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _curriculum_fingerprint(lang: str) -> dict[str, str]:
    snapshot = [
        {
            "unit": topic.key,
            "mood": topic.mood,
            "tense": topic.tense,
            "verbs": list(topic.verbs),
            "persons": list(_eligible_persons(topic)),
        }
        for topic in _morphology_topics(lang)
    ]
    return {
        "scope": "ordered verify=morph unit/mood/tense/verb/person specification",
        "sha256": _sha256_json(snapshot),
    }


def obtain_source(cache_dir: Path, source: Source, *, offline: bool, refresh: bool) -> Path:
    destination = source_path(cache_dir, source)
    if destination.exists() and not refresh:
        actual = sha256(destination)
        if actual == source.sha256:
            return destination
        if offline:
            raise RuntimeError(
                f"cached source checksum mismatch: {destination}\n"
                f"expected {source.sha256}, got {actual}"
            )
    elif offline:
        raise FileNotFoundError(
            f"offline source is missing: {destination}; run once without --offline"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "idiomatic-frequency-builder/2"},
    )
    temporary: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as target:
                temporary = Path(target.name)
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
        actual = sha256(temporary)
        if actual != source.sha256:
            raise RuntimeError(
                f"downloaded source checksum mismatch for {source.name}: "
                f"expected {source.sha256}, got {actual}"
            )
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return destination


def _column_number(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference)
    if not match:
        raise ValueError(f"bad XLSX cell reference: {reference!r}")
    number = 0
    for character in match.group(1):
        number = number * 26 + ord(character) - ord("A") + 1
    return number


def _xlsx_cell_value(cell: ElementTree.Element, shared: list[str], namespace: str) -> str:
    kind = cell.attrib.get("t")
    value_node = cell.find(f"{namespace}v")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{namespace}t"))
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text
    if kind == "s":
        return shared[int(value)]
    return value


def parse_subtlex_es_xlsx(path: Path, wanted: set[str]) -> FrequencyData:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    counts: dict[str, float] = defaultdict(float)
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter(f"{namespace}t"))
                for item in root.iter(f"{namespace}si")
            ]
        with archive.open("xl/worksheets/sheet1.xml") as worksheet:
            word_columns: tuple[int, ...] | None = None
            for _event, row in ElementTree.iterparse(worksheet, events=("end",)):
                if row.tag != f"{namespace}row":
                    continue
                values = {
                    _column_number(cell.attrib["r"]): _xlsx_cell_value(cell, shared, namespace)
                    for cell in row.findall(f"{namespace}c")
                }
                if word_columns is None:
                    word_columns = tuple(
                        column for column, value in values.items() if value == "Word"
                    )
                    if not word_columns or any(
                        values.get(column + 1) != "Freq. count" for column in word_columns
                    ):
                        raise ValueError("unexpected SUBTLEX-ESP XLSX header")
                else:
                    for column in word_columns:
                        word = _norm(values.get(column, ""))
                        raw_count = values.get(column + 1, "")
                        if word in wanted and raw_count:
                            counts[word] += int(float(raw_count))
                row.clear()
    return FrequencyData(dict(counts))


def parse_subtlex_pt_tsv(path: Path, wanted: set[str]) -> FrequencyData:
    counts: dict[str, float] = defaultdict(float)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream, delimiter="\t")
        if rows.fieldnames != ["Word", "FREQcount", "CDcount", "Spellcheck"]:
            raise ValueError(f"unexpected SUBTLEX-PT-BR header: {rows.fieldnames}")
        for line_number, row in enumerate(rows, 2):
            word = _norm(row["Word"])
            if word not in wanted:
                continue
            try:
                counts[word] += int(row["FREQcount"])
            except ValueError as exc:
                raise ValueError(f"bad SUBTLEX-PT-BR count at {path}:{line_number}") from exc
    return FrequencyData(dict(counts))


def parse_frequency_words(path: Path, wanted: set[str]) -> FrequencyData:
    counts: dict[str, float] = defaultdict(float)
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                word, raw_count = line.rstrip("\n").rsplit(" ", 1)
                word = _norm(word)
                if word in wanted:
                    counts[word] += int(raw_count)
            except (UnicodeError, ValueError) as exc:
                raise ValueError(f"malformed FrequencyWords row at {path}:{line_number}") from exc
    return FrequencyData(dict(counts))


def parse_lexique4_zip(path: Path, wanted: set[str]) -> FrequencyData:
    surface_counts: dict[str, float] = defaultdict(float)
    lemma_counts: dict[tuple[str, str], float] = defaultdict(float)
    with zipfile.ZipFile(path) as archive:
        candidates = [
            name
            for name in archive.namelist()
            if name.endswith("/Lexique4.tsv") and not name.startswith("__MACOSX/")
        ]
        if len(candidates) != 1:
            raise ValueError(f"expected one Lexique4.tsv in {path}, got {candidates}")
        with archive.open(candidates[0]) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                rows = csv.DictReader(stream, delimiter="\t")
                required = {"1_Mot", "4_Lemme", "5_Cgram", "10_FreqMot"}
                if not required.issubset(rows.fieldnames or ()):
                    raise ValueError("unexpected Lexique 4 TSV header")
                for line_number, row in enumerate(rows, 2):
                    if row["5_Cgram"] not in {"VER", "AUX"}:
                        continue
                    word = _norm(row["1_Mot"])
                    if word not in wanted:
                        continue
                    lemma = _norm(row["4_Lemme"])
                    try:
                        frequency = float(row["10_FreqMot"])
                    except ValueError as exc:
                        raise ValueError(
                            f"bad Lexique 4 frequency at {candidates[0]}:{line_number}"
                        ) from exc
                    surface_counts[word] += frequency
                    lemma_counts[(word, lemma)] += frequency
    return FrequencyData(dict(surface_counts), dict(lemma_counts))


PARSERS = {
    "subtlex_es_xlsx": parse_subtlex_es_xlsx,
    "subtlex_pt_tsv": parse_subtlex_pt_tsv,
    "frequency_words": parse_frequency_words,
    "lexique4_zip": parse_lexique4_zip,
}


def _token_lemmas(lang: str, cell: Cell, variant: str) -> tuple[tuple[str, str | None], ...]:
    tokens = _tokens(variant)
    if not tokens:
        return ()
    lemmas: list[str | None] = [None] * len(tokens)
    lemmas[-1] = cell.verb
    if lang == "fr" and len(tokens) > 1:
        # Current French compound scope is passé composé: one present-tense
        # auxiliary plus a lexical participle.
        for auxiliary in ("avoir", "être"):
            expected = morphology.lookup("fr", auxiliary, "indicatif", "présent", cell.person)
            if expected and _norm(expected) == tokens[0]:
                lemmas[0] = auxiliary
                break
    return tuple(zip(tokens, lemmas, strict=True))


def _ambiguity_index(
    lang: str, cells: list[Cell], *, lemma_tagged: bool
) -> dict[tuple[str, str | None], int]:
    analyses: dict[tuple[str, str | None], set[tuple[str, str, str, str]]] = defaultdict(set)
    for cell in cells:
        for variant in cell.variants:
            tokens = _tokens(variant)
            if not tokens:
                continue
            # Allocate the lexical token across distinct analyses represented
            # by emitted cells. Duplicate curriculum units do not add analyses.
            # Out-of-scope morphology and cross-POS uses are not inferable from
            # an untagged count list; the curated rules and metadata disclose
            # that residual limitation. Auxiliary counts remain person evidence
            # and are not divided by the number of curriculum verbs using them.
            lemma_key = cell.verb if lemma_tagged else None
            analyses[(tokens[-1], lemma_key)].add(cell.analysis)
    return {key: len(values) for key, values in analyses.items()}


def _variant_score(
    lang: str,
    cell: Cell,
    variant: str,
    data: FrequencyData,
    ambiguity: dict[tuple[str, str | None], int],
) -> float:
    token_lemmas = _token_lemmas(lang, cell, variant)
    if not token_lemmas:
        return 0.0
    # A finite surface identical to an infinitive cannot be separated from the
    # overwhelmingly common non-finite use in an untagged input.  For the
    # lemma-tagged French source, only identity with the target's own infinitive
    # remains unresolved.  Zero is conservative, not a claim of corpus absence.
    if len(token_lemmas) == 1:
        token = token_lemmas[0][0]
        if token == _norm(cell.verb) or (
            not data.lemma_tagged and token in _known_infinitives(lang)
        ):
            return 0.0

    component_counts: list[float] = []
    for index, (token, lemma) in enumerate(token_lemmas):
        count = data.count(token, lemma)
        if not data.lemma_tagged and token in UNTAGGED_ZERO_HOMOGRAPHS.get(lang, ()):
            return 0.0
        if not data.lemma_tagged and token in UNTAGGED_HOMOGRAPHS.get(lang, ()):
            count *= HOMOGRAPH_FACTOR
        if index == len(token_lemmas) - 1:
            lemma_key = cell.verb if data.lemma_tagged else None
            count /= ambiguity[(token, lemma_key)]
        if count <= 0:
            return 0.0
        component_counts.append(count)

    # The lists are unigram resources.  The shifted geometric component proxy
    # (geometric mean of count + 1, then minus 1) retains both person-marked
    # auxiliary and lexical-participle evidence while remaining in the source
    # frequency's units.  It is not a phrase count.
    score = (
        math.exp(sum(math.log1p(count) for count in component_counts) / len(component_counts)) - 1.0
    )
    return score


def score_cells(lang: str, cells: list[Cell], data: FrequencyData) -> dict[Cell, float]:
    ambiguity = _ambiguity_index(lang, cells, lemma_tagged=data.lemma_tagged)
    scores: dict[Cell, float] = {}
    for cell in cells:
        # Alternative spellings/forms all realize the same cell, so their
        # ambiguity-adjusted evidence is additive.
        scores[cell] = sum(
            _variant_score(lang, cell, variant, data, ambiguity) for variant in cell.variants
        )
    return scores


def normalize_by_unit(cells: list[Cell], scores: dict[Cell, float]) -> dict[Cell, float]:
    by_unit: dict[str, list[Cell]] = defaultdict(list)
    for cell in cells:
        by_unit[cell.unit].append(cell)
    weights: dict[Cell, float] = {}
    for unit_cells in by_unit.values():
        maximum = max((math.log1p(scores[cell]) for cell in unit_cells), default=0.0)
        for cell in unit_cells:
            transformed = math.log1p(scores[cell])
            weights[cell] = round(transformed / maximum, 6) if maximum else 0.0
    return weights


def _source_metadata(source: Source, path: Path) -> dict[str, str]:
    return {
        "name": source.name,
        "version": source.version,
        "url": source.url,
        "project_url": source.project_url,
        "cache_filename": source.cache_filename,
        "sha256": sha256(path),
        "corpus": source.corpus,
        "frequency_field": source.frequency_field,
        "citation": source.citation,
        "license": source.license,
        "license_url": source.license_url,
        "license_note": source.license_note,
        "selection_note": source.selection_note,
    }


def _morphology_metadata(lang: str) -> dict[str, str]:
    path = MORPHOLOGY_FILES[lang]
    return {
        **MORPHOLOGY_SOURCES[lang],
        "local_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def build_language(lang: str, source_path_: Path, build_date: str) -> BuildResult:
    source = SOURCES[lang]
    cells, unit_verbs, missing_morphology = curriculum_cells(lang)
    wanted = {token for cell in cells for variant in cell.variants for token in _tokens(variant)}
    data = PARSERS[source.parser](source_path_, wanted)
    scores = score_cells(lang, cells, data)
    weights = normalize_by_unit(cells, scores)

    output: dict[str, object] = {
        "_meta": {
            "schema_version": 1,
            "language": lang,
            "build_date": build_date,
            "scope": (
                "live curriculum topics with verify=morph; unsupported and "
                "pedagogically disallowed persons are omitted"
            ),
            "source": _source_metadata(source, source_path_),
            "morphology_source": _morphology_metadata(lang),
            "curriculum_fingerprint": _curriculum_fingerprint(lang),
            "normalization": (
                "weight = log1p(effective_score) / max_unit(log1p(effective_score)); "
                "rounded to 6 decimals"
            ),
            "multiword_policy": (
                "exp(mean(log1p(component_count))) - 1; ranking proxy only, not "
                "an attested phrase count"
            ),
            "homograph_policy": (
                "divide lexical-token evidence across distinct analyses in the "
                "emitted curriculum cells (duplicate units do not count twice); zero "
                "finite forms identical to an infinitive and listed unresolved "
                "cross-lemma collisions; Lexique 4 sums target-lemma VER/AUX "
                "counts; untagged sources apply a 0.10 factor only to listed "
                "reviewed cross-POS, cross-lemma, or cross-mood collisions; "
                "residual homographs remain possible"
            ),
            "applied_curated_homograph_tokens": sorted(
                wanted.intersection(UNTAGGED_HOMOGRAPHS.get(lang, ()))
            ),
            "applied_zeroed_homograph_tokens": sorted(
                wanted.intersection(UNTAGGED_ZERO_HOMOGRAPHS.get(lang, ()))
            ),
            "license_note": (
                "raw inputs are cached but not shipped; these files contain only "
                "normalized aggregate weights and attribution; this is a provenance "
                "record, not a legal determination"
            ),
            "unit_count": len(unit_verbs),
            "weighted_cell_count": len(cells),
            "zero_weight_cell_count": sum(weight == 0 for weight in weights.values()),
            "missing_morphology_cell_count": missing_morphology,
            "alternative_surface_cell_count": sum(len(cell.variants) > 1 for cell in cells),
        }
    }
    if lang == "pt":
        output["_meta"]["person_policy"] = (  # type: ignore[index]
            "Brazilian curriculum uses 1s/3s/1p/3p; generator policy rejects 2s/2p"
        )
    elif lang == "es":
        output["_meta"]["person_policy"] = (  # type: ignore[index]
            "all persons except unit-specific command restrictions: tú=2s; "
            "usted/ustedes=3s/1p/3p; negative=2s/3s/3p"
        )
    else:
        output["_meta"]["person_policy"] = "all morphology-backed persons"

    indexed = {(cell.unit, cell.verb, cell.person): weights[cell] for cell in cells}
    for unit, verbs in unit_verbs.items():
        output[unit] = {
            verb: {
                person: indexed[(unit, verb, person)]
                for person in morphology.PERSONS
                if (unit, verb, person) in indexed
            }
            for verb in verbs
        }

    result = BuildResult(output, cells, scores, weights)
    validate_result(lang, unit_verbs, result)
    return result


def validate_result(lang: str, unit_verbs: dict[str, list[str]], result: BuildResult) -> None:
    if set(result.output) != {"_meta", *unit_verbs}:
        raise RuntimeError(f"output unit mismatch for {lang}")
    for unit, verbs in unit_verbs.items():
        emitted = result.output[unit]
        if not isinstance(emitted, dict) or list(emitted) != verbs:
            raise RuntimeError(f"verb inventory mismatch for {unit}")
    for cell, weight in result.weights.items():
        if isinstance(weight, bool) or not math.isfinite(weight) or not 0 <= weight <= 1:
            raise RuntimeError(f"invalid weight for {cell}: {weight!r}")
    for unit in unit_verbs:
        unit_weights = [result.weights[cell] for cell in result.cells if cell.unit == unit]
        if not any(unit_weights):
            raise RuntimeError(f"unit has no source evidence: {unit}")
        if max(unit_weights) != 1.0:
            raise RuntimeError(f"nonzero unit lacks a 1.0 maximum: {unit}")
    for unit in COMPOUND_UNITS.intersection(unit_verbs):
        if not any(result.scores[cell] > 0 for cell in result.cells if cell.unit == unit):
            raise RuntimeError(f"compound unit has no source evidence: {unit}")
    if lang == "pt":
        if any(cell.person in {"2s", "2p"} for cell in result.cells):
            raise RuntimeError("Brazilian Portuguese output contains tu/vós cells")
    expected_units, expected_cells, expected_missing = EXPECTED_COVERAGE[lang]
    actual_missing = result.output["_meta"][  # type: ignore[index]
        "missing_morphology_cell_count"
    ]
    if (len(unit_verbs), len(result.cells), actual_missing) != (
        expected_units,
        expected_cells,
        expected_missing,
    ):
        raise RuntimeError(
            f"coverage regression for {lang}: expected "
            f"{(expected_units, expected_cells, expected_missing)}, got "
            f"{(len(unit_verbs), len(result.cells), actual_missing)}"
        )
    if lang == "it":
        alternatives = sum(len(cell.variants) > 1 for cell in result.cells)
        if alternatives != 55:
            raise RuntimeError(
                f"Italian alternative expansion regression: expected 55, got {alternatives}"
            )
    if lang == "es":
        high = next(
            cell
            for cell in result.cells
            if (cell.unit, cell.verb, cell.person) == ("es_preterito", "decir", "3s")
        )
        low = next(
            cell
            for cell in result.cells
            if (cell.unit, cell.verb, cell.person) == ("es_futuro", "traducir", "2p")
        )
        if result.scores[high] <= result.scores[low]:
            raise RuntimeError("Spanish sanity ordering failed: dijo <= traduciréis")
        unresolved = next(
            cell
            for cell in result.cells
            if (cell.unit, cell.verb, cell.person) == ("es_cmd_neg", "crear", "2s")
        )
        if result.scores[unresolved] != 0:
            raise RuntimeError("Spanish unresolved no-crees homograph was not zeroed")
    if lang == "pt":
        distinct_infinitive = next(
            cell
            for cell in result.cells
            if (cell.unit, cell.verb, cell.person) == ("pt_futuro_subjuntivo", "ver", "1s")
        )
        if result.scores[distinct_infinitive] != 0:
            raise RuntimeError("Portuguese ver/vir infinitive collision was not zeroed")


def _build_date(argument: str | None) -> str:
    if argument:
        return date.fromisoformat(argument).isoformat()
    if epoch := os.environ.get("SOURCE_DATE_EPOCH"):
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date().isoformat()
    return date.today().isoformat()


def _cell_order(result: BuildResult) -> dict[Cell, int]:
    return {cell: index for index, cell in enumerate(result.cells)}


def print_summary(lang: str, result: BuildResult) -> None:
    order = _cell_order(result)
    highest = sorted(
        result.cells,
        key=lambda cell: (-result.scores[cell], order[cell]),
    )[:10]
    lowest = sorted(
        result.cells,
        key=lambda cell: (result.scores[cell], -order[cell]),
    )[:10]
    print(f"\n{lang.upper()} highest 10 by pre-normalization effective score")
    print("unit\tverb\tperson\tsurface\teffective_score\tunit_weight")
    for cell in highest:
        print(
            f"{cell.unit}\t{cell.verb}\t{cell.person}\t{cell.surface}\t"
            f"{result.scores[cell]:.9g}\t{result.weights[cell]:.6f}"
        )
    print(f"{lang.upper()} lowest 10 by pre-normalization effective score")
    print("unit\tverb\tperson\tsurface\teffective_score\tunit_weight")
    for cell in lowest:
        print(
            f"{cell.unit}\t{cell.verb}\t{cell.person}\t{cell.surface}\t"
            f"{result.scores[cell]:.9g}\t{result.weights[cell]:.6f}"
        )


def _default_cache_dir() -> Path:
    configured = os.environ.get("XDG_CACHE_HOME")
    cache_root = Path(configured) if configured else Path.home() / ".cache"
    return cache_root / "idiomatic" / "frequency-weights"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--languages", nargs="+", choices=LANGS, default=list(LANGS))
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=_default_cache_dir(),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "idiomatic" / "grammar" / "data",
    )
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--build-date", help="ISO date; defaults to today")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args(argv)


def _write_atomic(destination: Path, serialized: str) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(serialized)
        temporary.replace(destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    if args.offline and args.refresh:
        raise SystemExit("--offline and --refresh cannot be combined")
    build_date = _build_date(args.build_date)
    artifacts: list[tuple[str, BuildResult, Path, str, int]] = []
    for lang in args.languages:
        source = SOURCES[lang]
        path = obtain_source(args.cache_dir, source, offline=args.offline, refresh=args.refresh)
        result = build_language(lang, path, build_date)
        destination = args.output_dir / f"freq_weights_{lang}.json"
        serialized = json.dumps(result.output, ensure_ascii=False, indent=2) + "\n"
        size = len(serialized.encode("utf-8"))
        if size >= 500_000:
            raise RuntimeError(f"output exceeds 500 KB: {destination} ({size} bytes)")
        artifacts.append((lang, result, destination, serialized, size))

    # Do not replace any artifact until every selected language has parsed and
    # validated successfully. Each individual replacement is also atomic.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for lang, result, destination, serialized, size in artifacts:
        _write_atomic(destination, serialized)
        print(f"wrote {destination} ({size:,} bytes)")
        if args.summary:
            print_summary(lang, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
