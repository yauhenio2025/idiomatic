# Codex commission G: vocabulary-side mining of the error corpus

> Work dir: /home/admin/projects/idiomatic-data/ — write ONLY inside
> its `vocab/` subdirectory (personal data, stays out of the public
> repo). Data: errmine/personal_errors.jsonl (the ~3,600 kind=vocab_gap
> rows + vocabulary-category rows), errmine/teachee_*.jsonl (the vocab
> teaching cards), errmine/xlsx_*.jsonl. Repo context (read-only):
> docs/commissions/ERROR_PROFILE_PROPOSAL.md §5 task 4,
> idiomatic/lingq.py + the lingq_terms usage in
> idiomatic/grammar/generate.py (how vocab currently rides into
> generation), docs/research/error-profiles/*.md §4 (vocab profiles).

## Goal

Five years of teachers writing down words the learner reached for and
lacked — barely used so far. Turn it into actionable vocabulary data.

## Tasks

1. **Thematic clustering** (`vocab/clusters_{lang}.md` + `.json`): for
   each language, cluster the vocab_gap rows + teachee vocab cards
   into domains (politics/media/tech/daily-life/abstract-argument...)
   and types (single word / collocation / fixed phrase / register
   pair). Counts per cluster, top examples verbatim, and which
   clusters RECUR across years (persistent gaps) vs one-offs.
2. **Collocation goldlist** (`vocab/collocations_{lang}.jsonl`): the
   subset that is collocations/fixed phrases (these transfer worst and
   were taught most) — {"phrase", "gloss_en", "domain", "occurrences",
   "first_seen", "last_seen"}. These are candidates for the idiom
   pipeline's pool decks.
3. **Generation-weave list** (`vocab/weave_{lang}.jsonl`): the ~200
   highest-value items per language (persistent, professional-register,
   still plausibly unmastered) in the exact shape
   grammar/generate.py's extra_vocab expects ({"term", "gloss",
   "status": null}) so they can complement the LingQ sample as
   sentence material in drill generation.
4. **Absorption proposal** (`vocab/ABSORPTION.md`): concretely how
   each artifact should enter the system: weave lists alongside
   lingq_terms (a second source for _vocab_lines), collocation
   goldlist → periodic themed pool deck or F1-style vocab cloze unit,
   what NOT to import (stale one-offs), and a dedup strategy against
   the ~52k LingQ terms already mirrored (flag overlaps in the
   goldlist with an "in_lingq_likely" boolean using string matching
   heuristics documented in the file).

## Rules

No git ops. No writes outside idiomatic-data/vocab/. Verbatim forms
stay verbatim. Every JSON/JSONL parses; _meta headers with counts.
