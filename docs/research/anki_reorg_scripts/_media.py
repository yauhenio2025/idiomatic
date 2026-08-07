#!/usr/bin/env python3
"""Shared extraction of local media references from Anki note fields."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import unquote


SOUND = re.compile(r"\[sound:([^\]\r\n]+)\]", re.IGNORECASE)
CSS_URL = re.compile(r"url\(\s*[\"']?([^\)\"']+)[\"']?\s*\)", re.IGNORECASE)
EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "//",
    "data:",
    "mailto:",
    "javascript:",
    "anki:",
)


class MediaAttributeParser(HTMLParser):
    """Collect HTML attributes that can point at Anki media."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del tag
        for attribute, value in attrs:
            if value is None:
                continue
            attribute = attribute.casefold()
            if attribute not in {
                "src",
                "href",
                "poster",
                "srcset",
                "data",
                "data-src",
                "background",
            }:
                continue
            if attribute == "srcset":
                self.references.extend(
                    item.strip().split()[0]
                    for item in value.split(",")
                    if item.strip()
                )
            else:
                self.references.append(value.strip())


def local_reference(raw: str) -> str | None:
    value = html.unescape(raw.strip())
    folded = value.casefold()
    if folded.startswith(EXTERNAL_PREFIXES) or folded.startswith(("file:", "/")):
        return None
    local = unquote(value.split("#", 1)[0].split("?", 1)[0])
    return local or None


def media_references(fields_blob: str) -> list[str]:
    references: list[str] = []
    for raw in SOUND.findall(fields_blob):
        if (reference := local_reference(raw)) is not None:
            references.append(reference)

    parser = MediaAttributeParser()
    try:
        parser.feed(fields_blob)
        parser.close()
    except Exception:
        # A malformed note must not abort the read-only estate inventory.
        pass
    for raw in parser.references:
        if (reference := local_reference(raw)) is not None:
            references.append(reference)

    for raw in CSS_URL.findall(fields_blob):
        if (reference := local_reference(raw)) is not None:
            references.append(reference)
    return references
