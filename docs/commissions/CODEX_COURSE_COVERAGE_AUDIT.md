# Codex: German course completeness audit — mechanical coverage map

You are producing the DATA for a second-pass completeness audit of the
21-unit German grammar course. You do NOT judge materiality or fix
anything — the coordinator does that from your output. Read-only with
respect to all course data: never modify anything under
`idiomatic/grammar/data/course/` or `docs/research/grammar_books/`
except the NEW output directory named below.

## Inputs (all machine-local)

- Hammer section inventory: `docs/research/grammar_books/de_hammer_ref/`
  (`REF_MANIFEST.json` — 146 numbered sections; `sections/chNN.json`
  per chapter; JOIN_CHECK.md explains the join).
- Unit plans: `idiomatic/grammar/data/course/plans/de_<unit>.plan.json`
  (20 files) — per-block `hammer_refs` + `exercise_sets`.
- Lessons: `idiomatic/grammar/data/course/lessons/de_<unit>.md`
  (21 units; `de_svg.md` is a style guide, SKIP it) — `REF:` citation
  lines, possibly deeper than section granularity (e.g. `2.2.2a`;
  normalize to the owning numbered section, e.g. `2.2`; `REF: 2` cites
  a whole chapter — record it as chapter-level, do not expand it to
  every section).
- Workbook corpus (sealed, NEVER quote body/exercise text):
  `docs/research/grammar_books/de_hammer_work/chapters/` — full
  exercise-set inventory per chapter (`ex_no`), item-level Pass-2
  flags.
- Selection/gate logic: `tools/course_select.py` — import and reuse its
  gate functions to RECOMPUTE, per selected set, which items the
  Pass-2 flags exclude, which the structural hygiene gate drops (and
  WHICH RULE fired), and which `max_items` truncates. Recompute
  in-memory or under the output dir — do not overwrite anything in
  `book_local/`.
- `partikeln` (ch09) has NO plan (lesson-only — all sets were
  provenance-flagged at authoring time). Still inventory ch09 fully:
  sets, item counts, per-item flag classes, so the coordinator can
  judge whether original-exercise commissioning is warranted.

## Outputs (create `docs/research/grammar_books/course_audit/`)

1. `coverage_data.json`:
   - `sections`: for each of the 146 numbered sections: chapter, id,
     title (titles are fine; NEVER body text), `cited_by_plans`
     [{unit, block}], `cited_by_lessons` [{unit, ref_as_written}],
     `chapter_level_citations` [units citing the bare chapter],
     and `taught: true/false` (taught = cited by at least one plan
     block or lesson REF at section or deeper granularity).
   - `units`: for each of the 21 units: chapter; full workbook set
     inventory [{ex_no, item_count, selected: bool, key_mode: bool}];
     for each SELECTED set: {items_total, items_kept,
     dropped_pass2: n, dropped_hygiene: [{rule, n}],
     truncated_max_items: n}; for each UNSELECTED set: {items_total,
     pass2_clean_items: n} (how many items WOULD survive the flags —
     i.e. what selecting it would buy).
2. `COVERAGE_REPORT.md`:
   - Table 1: never-taught sections grouped by chapter (id + title +
     nearest-taught neighbor sections).
   - Table 2: per-unit exercise coverage — sets selected/total, items
     kept/dropped by cause; flag the thin units (wortbildung, zahlen,
     rechtschreibung, partikeln) with a per-set breakdown of exactly
     which gate rule or flag class killed what.
   - Table 3: hygiene-gate rule × total items killed across the
     course (so over-strict rules stand out).
   - NO book body text, NO exercise text anywhere in either output —
     section titles and set numbers/counts only.
3. Print Table 1 and Table 2 to stdout at the end.

Self-check before finishing: every plan `hammer_refs` entry must
resolve to a real section id (report any that do not as
`dangling_refs`); section count must equal 146; unit count 21.
