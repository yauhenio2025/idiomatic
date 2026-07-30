# Codex task: backfill citation (dictionary) forms for existing idioms

## Goal

Every `expression_idioms` row needs a `citation_form`: the expression in
its dictionary/citation shape — as-spoken `"hat das Sagen"` → citation
`"das Sagen haben"`. New idioms get this automatically from the cloud
pipeline (since 2026-07-30); your job is the ~1,000+ historical rows
where `citation_form IS NULL`.

You (codex) do the linguistics YOURSELF — no external LLM API calls
needed. You read batches of idioms, produce the citation form for each,
and write them back.

## API (all on https://idiomatic-app.onrender.com)

Auth header for both endpoints: `X-Admin-Token: <token>` — read the
token from `~/.config/idiomatic-admin.env` (single `ADMIN_TOKEN=...`
line; NEVER print it or write it to any file in a git repo).

1. `GET /admin/citation-todo?limit=100`
   → `{"remaining": N, "items": [{"id", "lang", "idiom_text",
      "english_gloss", "source_phrase_target"}, ...]}`
   Rows where citation_form is still NULL, id-ordered.

2. `POST /admin/citation-forms` with JSON
   `{"forms": {"<id>": "<citation form>", ...}}`
   → `{"ok": true, "updated": N, "skipped_empty": M}`
   Empty strings are skipped server-side (row stays NULL and will
   reappear in the todo — use that if you're unsure about an item).

## Citation-form rules

- Verbs → infinitive: `hat das Sagen` → `das Sagen haben`;
  `nous sommes gâtés` → `être gâté`; `si è giocato` → `giocarsi`.
- Conjugated reflexives keep the infinitive reflexive: `me rends compte`
  → `se rendre compte`.
- Nouns → singular, keep an article only when it is part of the fixed
  expression (`das Sagen haben` keeps `das`; a plain noun phrase gets
  no added article).
- Fixed adverbials / discourse markers / conjunctions that have no
  inflection (`quoi qu'il en soit`, `kurz gesagt`, `à titre de
  précaution`) → citation form = the expression unchanged.
- Keep the expression's own pronouns when fixed (`en avoir marre`,
  `farcela` → `farcela`).
- Strip sentence-specific subjects/objects that are NOT part of the
  fixed expression: `il a le vent en poupe` → `avoir le vent en poupe`.
- Use `source_phrase_target` for context when the bare `idiom_text` is
  ambiguous; `english_gloss` tells you the intended meaning.
- Language is in `lang` (`de`, `fr`, `it`, `pt`, `es`). Answer in that
  language's orthography, no quotes, no trailing period.

## Procedure

1. Loop: fetch `citation-todo?limit=100`, produce forms for ALL items
   in the batch, POST them back, repeat until `remaining` is 0.
   (The todo endpoint only returns NULL rows, so the loop naturally
   advances; no offset bookkeeping needed.)
2. Log progress to stdout every batch: `remaining=N updated=M`.
3. If the service returns 5xx or times out (it redeploys occasionally),
   wait 60s and retry the same batch — POSTs are idempotent.
4. When done, print a 20-row sample of (lang, idiom_text →
   citation_form) for human review. Do NOT trigger any rebuild
   endpoints — the nightly pool rebuilds fold the new forms into the
   cards automatically.

## Quality bar

- Prefer leaving an item empty (skip) over guessing wildly — NULL rows
  can be re-run; wrong forms ship to flashcards.
- Sanity check: the citation form must contain the expression's content
  words (or their lemmas). If your form shares no stem with idiom_text,
  you've probably drifted — redo it.

## What happens downstream (not your job)

- Cards render the form as a "Dictionary form" row on the back
  (already deployed; pool decks pick it up on their next rebuild).
- Already-delivered per-video decks are not retroactively updated —
  only pool cards and future video decks show the form.
