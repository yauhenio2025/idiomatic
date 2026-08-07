#!/usr/bin/env python3
"""Observed-source to proposed-target deck rules for the estate draft."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    code: str
    english: str
    root: str


LANGUAGES = {
    "de": Language("de", "German", "DE German"),
    "es": Language("es", "Spanish", "ES Spanish"),
    "fr": Language("fr", "French", "FR French"),
    "it": Language("it", "Italian", "IT Italian"),
    "pt": Language("pt", "Portuguese", "PT Portuguese"),
}
LANG_BY_ENGLISH = {item.english: item for item in LANGUAGES.values()}
MANDARIN_ROOT = "ZH Mandarin"
DORMANT_ROOT = "zz Dormant"
MANDARIN_RENAME_ROOTS = {
    "Languages::Mandarin": f"{MANDARIN_ROOT}::Languages::Mandarin",
    "Mandarin Actors": f"{MANDARIN_ROOT}::Mandarin Actors",
    "Mandarin Characters 2026-06-20": f"{MANDARIN_ROOT}::Mandarin Characters 2026-06-20",
    "Mandarin China Provinces": f"{MANDARIN_ROOT}::Mandarin China Provinces",
    "Mandarin Locations": f"{MANDARIN_ROOT}::Mandarin Locations",
    "Mandarin Palace": f"{MANDARIN_ROOT}::Mandarin Palace",
    "Mandarin Props": f"{MANDARIN_ROOT}::Mandarin Props",
    "Mandarin Zones": f"{MANDARIN_ROOT}::Mandarin Zones",
}
PIMSLEUR_RENAME_ROOTS = {
    "Pimsleur::Danish": f"{DORMANT_ROOT}::Pimsleur::Danish",
    "Pimsleur::Dutch": f"{DORMANT_ROOT}::Pimsleur::Dutch",
    "Pimsleur::French": f"{LANGUAGES['fr'].root}::8 Pimsleur",
    "Pimsleur::German": f"{LANGUAGES['de'].root}::8 Pimsleur",
    "Pimsleur::Italian": f"{LANGUAGES['it'].root}::8 Pimsleur",
    "Pimsleur::Mandarin": f"{MANDARIN_ROOT}::8 Pimsleur",
    "Pimsleur::Norwegian": f"{DORMANT_ROOT}::Pimsleur::Norwegian",
    "Pimsleur::Portuguese": f"{LANGUAGES['pt'].root}::8 Pimsleur",
    "Pimsleur::Spanish": f"{LANGUAGES['es'].root}::8 Pimsleur::Spain",
    "Pimsleur::Spanish (Latin America)": (
        f"{LANGUAGES['es'].root}::8 Pimsleur::Latin America"
    ),
    "Pimsleur::Swedish": f"{DORMANT_ROOT}::Pimsleur::Swedish",
}
PLACEMENT_RENAME_ROOTS = {**MANDARIN_RENAME_ROOTS, **PIMSLEUR_RENAME_ROOTS}


SENTENCE_MODELS = {
    "YouTube Audio Phrase Reverse v1",
    "YouTube Audio Phrase v3",
    "YouTube Expression Pool v1",
}
ACTIVE_FLUENCY_MODELS = {"YouTube Expression Pool v1"}
EXPRESSION_MODELS = {
    "Idiomatic Cloud Card v1",
    "Idiomatic Cloud Card v2",
    "YouTube Idiom Card v2",
    "YouTube Idiom Card v2 (ElevenLabs Flash)",
    "YouTube Idiom Card v2 (Gemini Flash TTS)",
    "YouTube Idiom Card v2 (Piper)",
    "YouTube Idiom Card v3 Structured (de)",
    "YouTube Idiom Card v3 Structured (es)",
    "YouTube Idiom Card v3 Structured (es)+",
    "YouTube Idiom Card v3 Structured (fr)",
    "YouTube Idiom Card v3 Structured (fr)+",
    "YouTube Idiom Card v3 Structured (it)",
    "YouTube Idiom Card v3 Structured (it)+",
    "YouTube Idiom Card v3 Structured (pt)",
    "YouTube Idiom Card v3 Structured (pt)+",
}
RETIRED_EXPRESSION_TASK_MODELS = EXPRESSION_MODELS | {
    "YouTube Audio Phrase Reverse v1",
    "YouTube Audio Phrase v3",
}
AUDIO_MODELS = {
    "YouTube Idiom Audio EN→Target v1": "EN to target",
    "YouTube Idiom Audio Target→EN v1": "target to EN",
}


def active_language_for_deck(deck_name: str) -> Language | None:
    for language in LANGUAGES.values():
        prefixes = (
            f"Idiomatic::{language.english}",
            f"Languages::{language.english}",
            f"Idiomatic Grammar {language.code.upper()}",
            f"Idiomatic Exercises {language.code.upper()}",
            f"Idiomatic Translation {language.code.upper()}",
            f"Idiomatic Tenses {language.code.upper()}",
            f"Idiomatic Tenses Exercises {language.code.upper()}",
            f"Idiomatic Rescue Comics::{language.code.upper()}",
        )
        if any(deck_name == prefix or deck_name.startswith(prefix + "::") for prefix in prefixes):
            return language
    return None


def expression_card_destination(deck_name: str, model_name: str) -> str | None:
    """Map active fluency cards and retire old hub/raw-phrase task models."""

    if deck_name.startswith("Idiomatic::z-archive::"):
        parts = deck_name.split("::")
        language = LANGUAGES.get(parts[2].casefold()) if len(parts) > 2 else None
    else:
        language = active_language_for_deck(deck_name)
    if language is None:
        return None
    if not deck_name.startswith(("Idiomatic::", "Languages::")):
        return None
    if model_name in ACTIVE_FLUENCY_MODELS:
        return f"{language.root}::1 Expressions::1 Fluency"
    if model_name in RETIRED_EXPRESSION_TASK_MODELS:
        return f"{DORMANT_ROOT}::z-archive::{language.code.upper()}"
    return None


def learning_card_destination(deck_name: str, model_name: str) -> str | None:
    """Map generated grammar/exercise/translation/tenses/rescue cards."""

    language = active_language_for_deck(deck_name)
    if language is None:
        return None
    code = language.code.upper()
    families = (
        (f"Idiomatic Exercises {code}", "4 Exercises"),
        (f"Idiomatic Translation {code}", "5 Translation"),
        (f"Idiomatic Tenses Exercises {code}", "3 Tenses::2 Exercises"),
        (f"Idiomatic Tenses {code}", "3 Tenses::1 Production"),
    )
    for prefix, target in families:
        if deck_name == prefix or deck_name.startswith(prefix + "::"):
            suffix = deck_name[len(prefix) :].lstrip(":")
            return f"{language.root}::{target}" + (f"::{suffix}" if suffix else "")

    grammar_prefix = f"Idiomatic Grammar {code}"
    if deck_name == grammar_prefix or deck_name.startswith(grammar_prefix + "::"):
        suffix = deck_name[len(grammar_prefix) :].lstrip(":")
        first = suffix.split("::", 1)[0]
        if first.startswith("9 "):
            # F3 personal errors are deliberately separated from the grammar syllabus.
            remainder = suffix.split("::", 1)[1] if "::" in suffix else ""
            return f"{language.root}::6 My Errors" + (f"::{remainder}" if remainder else "")
        return f"{language.root}::2 Grammar" + (f"::{suffix}" if suffix else "")

    rescue_prefix = f"Idiomatic Rescue Comics::{code}"
    if deck_name == rescue_prefix or deck_name.startswith(rescue_prefix + "::"):
        suffix = deck_name[len(rescue_prefix) :].lstrip(":")
        return f"{language.root}::7 Rescue" + (f"::{suffix}" if suffix else "")
    return None


def audio_card_destination(deck_name: str, model_name: str) -> str | None:
    language = active_language_for_deck(deck_name)
    direction = AUDIO_MODELS.get(model_name)
    if language is None or direction is None:
        return None
    return f"{DORMANT_ROOT}::Retired Idioms Audio::{language.code.upper()}::{direction}"


def placement_card_destination(deck_name: str, model_name: str) -> str | None:
    """Place Mandarin families, Pimsleur courses, and z-archive."""

    if destination := archive_card_destination(deck_name):
        return destination
    return placement_rename_destination(deck_name)


def archive_card_destination(deck_name: str) -> str | None:
    if deck_name.startswith("Idiomatic::z-archive"):
        suffix = deck_name[len("Idiomatic::z-archive") :].lstrip(":")
        code = suffix.split("::", 1)[0].casefold() if suffix else "unclassified"
        label = code.upper() if code in LANGUAGES else "Unclassified"
        return f"{DORMANT_ROOT}::z-archive::{label}"
    return None


def placement_rename_destination(deck_name: str) -> str | None:
    """Map a deck row that will move through a metadata-preserving subtree rename."""

    for source, destination in PLACEMENT_RENAME_ROOTS.items():
        if deck_name == source or deck_name.startswith(source + "::"):
            suffix = deck_name[len(source) :].lstrip(":")
            return destination + (f"::{suffix}" if suffix else "")
    return None


def placement_root_renames(existing_names: set[str]) -> dict[str, str]:
    return {
        source: destination
        for source, destination in PLACEMENT_RENAME_ROOTS.items()
        if source in existing_names
    }


def fixed_target_decks() -> set[str]:
    decks: set[str] = {
        DORMANT_ROOT,
        f"{DORMANT_ROOT}::Pimsleur",
        f"{DORMANT_ROOT}::Retired Idioms Audio",
        f"{DORMANT_ROOT}::z-archive",
        *(f"{DORMANT_ROOT}::z-archive::{code.upper()}" for code in LANGUAGES),
        MANDARIN_ROOT,
        f"{MANDARIN_ROOT}::Languages",
        *MANDARIN_RENAME_ROOTS.values(),
        *PIMSLEUR_RENAME_ROOTS.values(),
    }
    for language in LANGUAGES.values():
        root = language.root
        decks.update(
            {
                root,
                f"{root}::1 Expressions",
                f"{root}::1 Expressions::1 Fluency",
                f"{root}::1 Expressions::2 Expression Focus",
                f"{root}::2 Grammar",
                f"{root}::3 Tenses",
                f"{root}::3 Tenses::1 Production",
                f"{root}::3 Tenses::2 Exercises",
                f"{root}::4 Exercises",
                f"{root}::4 Exercises::Diagnosed trouble spots",
                f"{root}::5 Translation",
                f"{root}::6 My Errors",
                f"{root}::7 Rescue",
                f"{root}::8 Pimsleur",
            }
        )
    return decks


def precreated_target_decks() -> set[str]:
    """Desired shells excluding roots that phase 5 must rename in place."""

    return fixed_target_decks() - set(PLACEMENT_RENAME_ROOTS.values())
