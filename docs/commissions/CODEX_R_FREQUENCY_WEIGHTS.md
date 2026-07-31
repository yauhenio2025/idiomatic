# Codex commission R: SUBTLEX frequency weights for tense×person cells

> Work dir: /home/admin/projects/idiomatic (main repo). Write ONLY
> `idiomatic/grammar/data/freq_weights_{lang}.json`, a builder script
> `tools/build_freq_weights.py`, and `docs/research/FREQ_WEIGHTS.md`.
> No git ops, no changes to generation code. Web download of corpora
> is expected. Read: docs/GRAMMAR_STRATEGY.md §5 ("SUBTLEX is per-FORM,
> so tense/person frequency is computable directly" — never executed),
> docs/research/grammar-data-sources.md, idiomatic/grammar/
> curriculum.py (the verb lists per unit), morphology.py (the form
> tables you can join against).

## Goal

The strategy promised frequency-FIRST drilling; today every tense×
person cell is sampled flat. Build the data that lets the generator
weight cells by real-world frequency.

## Tasks

1. Obtain per-language frequency lists (SUBTLEX-ESP/PT-BR variants
   where they exist, wordfreq/FrequencyWords as fallback — document
   exactly which source per language and its license; prefer
   redistributable ones since the output ships in the public repo —
   the OUTPUT is aggregate weights, which is fine even from
   non-redistributable inputs, but say so).
2. Join each language's frequency list against the morphology tables:
   for every unit's verb list, compute relative frequency of each
   (verb, tense, person) surface form. Handle homographs honestly
   (fr "porte" noun/verb — document the heuristic; overcounting
   homographs is the known failure mode, prefer underweighting).
3. Emit freq_weights_{lang}.json: {unit_key: {verb: {person: weight}}}
   normalized 0-1 per unit, plus a "_meta" block (source, build date,
   homograph policy). Keep files < 500 KB each.
4. FREQ_WEIGHTS.md: methodology, per-language source table, the 10
   most/least frequent cells per language (sanity check — "él/ella
   pretérito of decir should rank high, vosotros futuro of traducir
   near zero"), and a 10-line integration sketch for how
   generate.py's prompts would consume the weights (implementation
   belongs to a later session).
5. tools/build_freq_weights.py: reproducible end-to-end (download →
   weights), runnable offline against cached downloads.
