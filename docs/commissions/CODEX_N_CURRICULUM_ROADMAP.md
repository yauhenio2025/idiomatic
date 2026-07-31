# Codex commission N: curriculum roadmap vs CEFR inventories (+ the missing Italian taxonomy)

> Work dir: /home/admin/projects/idiomatic (main repo). Write ONLY
> `docs/research/CURRICULUM_ROADMAP.md`, `docs/research/taxonomies/`
> (new dir), and `docs/research/it-grammar-taxonomy.yaml`. No git ops.
> Web research REQUIRED. Read first: docs/GRAMMAR_STRATEGY.md §3 + §5
> (curriculum-taxonomy sources already vetted: PCIC es, Referencial
> Camões pt, Kwiziq trees fr/es, German Grammar Profile; Italian has
> NO open CEFR dataset — triangulate), the five error profiles,
> idiomatic/grammar/curriculum.py (the 67 live units — the roadmap is
> what comes AFTER these).

## Tasks

1. **Italian taxonomy** (strategy §10 item 3, never executed): build a
   CEFR-tagged (A2-C1) Italian grammar topic tree in machine-readable
   YAML: topic, subtopics, level, prerequisites, 2 example sentences
   each; base on CELI/CILS syllabi, Kwiziq-style sibling lists,
   Profilo della lingua italiana summaries; mark uncertain levels.
2. **Per-language gap analysis**: for each of the 5 languages, diff
   the live 67 units + the roadmap-relevant error-profile findings
   against the CEFR inventories → what a B2-C1 learner is expected to
   control that we neither drill nor have evidence he's mastered.
3. **Roadmap**: 15-25 candidate units per language, prioritized by
   (error-profile evidence > CEFR B2/C1 coverage gap > frequency),
   each with: proposed key, cluster (respect existing numbering:
   9 = my errors, 10 = interference), format (F1/F2/F3/F5),
   verification tier (morph / bank+deterministic / blind K=3 — say
   what bank or table it would need), and a one-line rationale.
   Flag which candidates need new verifier machinery vs none.
4. **Taxonomy snapshots**: save distilled per-language topic trees
   (not scraped dumps — your synthesis) under docs/research/
   taxonomies/{lang}.yaml so future planners diff against them.

Honesty rules: cite sources with URLs; mark every uncertain level
assignment; where the web source conflicts with the strategy doc's
claims, note it rather than silently choosing.
