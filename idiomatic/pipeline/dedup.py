"""Filter freshly-extracted phrases against the per-language expression library."""

from __future__ import annotations

import re
import unicodedata


_WHITESPACE_RE = re.compile(r"\s+")
_NONALPHA_RE = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(text: str) -> str:
    """Lowercased, NFC-normalized, whitespace-collapsed, punctuation-stripped.

    Intentionally not lemmatized — that's a future addition for inflected
    languages once we see how much near-duplicate noise leaks through.
    """
    t = unicodedata.normalize("NFC", text).lower().strip()
    t = _NONALPHA_RE.sub(" ", t)
    t = _WHITESPACE_RE.sub(" ", t).strip()
    return t


def filter_fresh(extracted: list, existing_normalized: set[str]) -> list:
    """Drop entries whose normalized form is already in the library."""
    return [e for e in extracted if e.normalized not in existing_normalized]
