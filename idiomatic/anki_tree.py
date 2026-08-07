"""Single source of truth for the post-estate Anki deck tree.

The estate migration (2026-08-07, docs/research/ANKI_ESTATE_REORG_PLAN.md
§ Live copy-back cutover) moved the collection to six language roots with
numbered study lanes. Every builder composes deck paths from here; never
bake a root string anywhere else.
"""

ANKI_ROOTS = {
    "de": "DE German",
    "es": "ES Spanish",
    "fr": "FR French",
    "it": "IT Italian",
    "pt": "PT Portuguese",
    "zh": "ZH Mandarin",
}


def anki_root(lang: str) -> str:
    try:
        return ANKI_ROOTS[lang.lower()]
    except KeyError:
        raise ValueError(f"no Anki root for language {lang!r}")
