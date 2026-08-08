"""Durable-ID recipes for the Expression Hub.

Single source of truth for every deterministic identity the Hub emits:
note GUIDs, source retry keys, example stable keys, and content-addressed
media basenames. The SQL backfill in db/schema.sql mirrors
:func:`source_key_youtube` — keep the two in sync.

GUID doctrine (design §4, migration §4.3): production GUIDs are the
migration contract and are proven collection-unique before any target
release. The PILOT namespace is deliberately different so a lingering
disposable pilot note can never collide with (or be updated by) a
production release.
"""

from __future__ import annotations

import hashlib

HUB_GUID_NS = "idiomatic-expression-hub-v1"
EXAMPLE_GUID_NS = "idiomatic-expression-example-v1"
PILOT_GUID_NS = "idiomatic-hub-pilot"

SOURCE_KEY_RECIPE_VERSION = "v1"


def _sha1_16(key: str) -> str:
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def hash8(data: bytes) -> str:
    """Content-address fragment for media basenames."""
    return hashlib.sha1(data).hexdigest()[:8]


# --- note GUIDs -------------------------------------------------------------

def hub_guid(lang: str, expression_id: int) -> str:
    """Production hub-note GUID: sha1("…-hub-v1::<lang>::<expr_id>")[:16]."""
    return _sha1_16(f"{HUB_GUID_NS}::{lang}::{expression_id}")


def example_guid(example_id: int) -> str:
    """Production example-note GUID (new notes only — a compatible migrated
    fluency note RETAINS its old text-derived GUID per migration §4.3)."""
    return _sha1_16(f"{EXAMPLE_GUID_NS}::{example_id}")


def pilot_hub_guid(lang: str, expression_id: int) -> str:
    return _sha1_16(f"{PILOT_GUID_NS}::hub::{lang}::{expression_id}")


def pilot_example_guid(example_id: int) -> str:
    return _sha1_16(f"{PILOT_GUID_NS}::example::{example_id}")


# --- durable retry / stable keys -------------------------------------------

def source_key_youtube(youtube_id: str, *, source_phrase: str | None = None,
                       row_id: int | None = None) -> str:
    """Durable retry key for a YouTube source occurrence (design §3.2).

    Prefers the source-phrase hash (computable before insert, hence a true
    retry key); falls back to the row id for phrase-less legacy rows.
    Mirrors the SQL backfill in db/schema.sql exactly.
    """
    if source_phrase is not None:
        frag = "p" + hashlib.md5(source_phrase.encode()).hexdigest()[:8]
    elif row_id is not None:
        frag = f"r{row_id}"
    else:
        raise ValueError("need source_phrase or row_id")
    return f"youtube:{SOURCE_KEY_RECIPE_VERSION}:{youtube_id}:{frag}"


def stable_key_legacy(example_id: int) -> str:
    return f"legacy:{example_id}"


def stable_key_topup(batch_id: int, attempt_no: int, slot: int) -> str:
    return f"topup:{batch_id}:{attempt_no}:{slot}"


# --- content-addressed media basenames --------------------------------------
# A revised asset gets a new basename; stale bytes are never silently
# reused (design §3.4). Names are flat because genanki/Anki media is flat.

def image_media_name(example_id: int, h8: str) -> str:
    return f"idh_ex_{example_id}_{h8}.jpg"


def context_media_name(source_id: int, h8: str) -> str:
    """Per-occurrence context clip (expression_idioms.audio_context)."""
    return f"idh_ctx_{source_id}_{h8}.mp3"


def expression_audio_media_name(source_id: int, h8: str) -> str:
    """Atomic expression pronunciation clip (audio_idiom_tgt)."""
    return f"idh_expr_{source_id}_{h8}.mp3"


def example_audio_media_name(example_id: int, side: str, h8: str) -> str:
    if side not in ("en", "tl"):
        raise ValueError(f"side must be en|tl, got {side!r}")
    return f"idh_exau_{example_id}_{side}_{h8}.mp3"
