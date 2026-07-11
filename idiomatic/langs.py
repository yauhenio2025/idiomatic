"""Canonical language-code → English-name map.

Single source of truth. This dict used to be duplicated in 7 modules
with drifting contents (pool.py's copy lacked nl/sv/no/da, so a future
Dutch pool deck would have landed under Idiomatic::NL:: while its video
decks used Idiomatic::Dutch::).
"""

from __future__ import annotations

LANG_NAMES: dict[str, str] = {
    "de": "German", "fr": "French", "it": "Italian",
    "pt": "Portuguese", "es": "Spanish", "zh": "Mandarin",
    "nl": "Dutch", "sv": "Swedish", "no": "Norwegian", "da": "Danish",
}


def lang_name(code: str) -> str:
    return LANG_NAMES.get(code, code.upper())
