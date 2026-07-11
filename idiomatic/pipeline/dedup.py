"""Normalization for expression dedup (the actual filtering lives in
worker._filter_fresh, which owns the DB lookup)."""

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
