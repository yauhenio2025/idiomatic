# Codex commission L: German NP-declension engine + adjective endings + passive

> Work dir: /home/admin/projects/idiomatic-wt/declension (isolated
> worktree). No git ops; `uv run pytest tests/` green. This is the
> most engineering-heavy commission — take your time. Read:
> idiomatic/grammar/morphology.py (the de_art machinery: gender table,
> article matrix — your foundation), curriculum.py TOPICS_DE,
> generate.py de_art/de_art_blind paths, docs/research/
> error-profiles/de.md (§3-A adjective-ending fossils, §2 passive
> findings, the Russian-L1 signatures), unit-specs README DECISIONS
> (the engine was explicitly deferred TO THIS build; de_dativ_verben
> may later reuse it).

## Part 1 — deterministic NP-inflection engine (morphology.py)

`decline_np(noun, *, case, number, definiteness, adjective=None) ->
str` producing the full NP surface: article (der/ein/kein/possessive
classes as definiteness modes) + adjective with correct WEAK/MIXED/
STRONG ending + noun with required inflection (dative-plural -n, weak
nouns/n-declension incl. -n/-en singular obliques, genitive -s/-es).
Data: the existing vendored gender table + a hardcoded declension
matrix + a weak-noun list (build grammar/data/de_weak_nouns.json,
~120 entries, from standard n-declension membership — no personal
data). Exhaustive tests: every (case × number × 3 declension
patterns) cell for a masc/fem/neut/plural example, the learner's
attested fossils as regression cases ("der härtester Konkurrent" →
der härteste, "keinen kohärentes Weltbild" → kein kohärentes,
"Meine ultimative Ziel" → mein ultimatives, dative plural Schillingen
→ Schilling issue is NUMBER not case — encode the unit-noun rule).

## Part 2 — units

1. `de_adj_endings` (planned → active, cluster "3 Adjektive"):
   F1 cloze, blank = article+adjective (or adjective alone after a
   given article) before a banked noun; verify = engine lookup
   (Tier A). Generator prompt mirrors the de_art metadata pattern
   (returns noun/case/number/definiteness/adjective); include an F5
   landmark-card note in guidance per strategy §4.
2. `de_passiv` (NEW Topic, cluster "4 Verben"): werden-passive forms
   (present/Präteritum/Perfekt + modal+infinitive passive), verify:
   werden-form via a small hardcoded werden table + participle via
   dictionary check where possible, else blind K=3 fallback — state
   clearly in code comments which path each item takes. Evidence: ~35
   teacher-supplied passives, zero spontaneous production.

Remove de_adj_endings + de_verb_core from PLANNED_UNITS; keep
de_verb_core OUT of the curriculum (superseded: its scope was passive
+ KII; you ship de_passiv now, KII stays future — document this in
unit-specs). Update seed-row expectations in tests accordingly.
