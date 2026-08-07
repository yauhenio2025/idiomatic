# Anki estate reorganization — owner decisions

No migration phase should be applied, even to the disposable collection copy, until the owner selects one option in every row.

| Decision | Recommended option | Implication | Alternative / consequence |
|---|---|---|---|
| Top-level language roots | `DE German`, `ES Spanish`, `FR French`, `IT Italian`, `PT Portuguese`, `ZH Mandarin` (`deck_label_language: code-plus-english`) | The ISO-like prefix gives deterministic sorting while the English name stays immediately recognizable. Changing this requires updating the mapping and every affected builder constant before migration. | English-only roots, or owner-specified bilingual roots. |
| Structural branch labels | Keep one English, numbered structure in every active-language root: `1 Expressions`, `2 Grammar`, `3 Tenses`, `4 Exercises`, `5 Translation`, `6 My Errors`, `7 Rescue`, `8 Pimsleur`; retain existing native-language syllabus leaves beneath those branches. | All languages have the same navigational and automation contract, while labels such as `Preposiciones` and `Reggenze` remain native. Fully native structural branches require changing the draft mapping and downstream builder names first. | Native structural labels per language. |
| F3 personal-error decks | Move `9 Meine Fehler`, `9 Mis errores`, `9 Mes erreurs`, `9 I miei errori`, and `9 Meus erros` out of Grammar into each language's `6 My Errors` branch. | Personal corrections remain a distinct study lane; notes, models, scheduling, and review history are preserved. Their old deck origin remains recorded in the phase journal. | Keep each native `9 …` branch under `2 Grammar`. |
| Dormant-tree label | `zz Dormant` (`dormant_root: zz Dormant`) | Inactive Pimsleur languages, retired Idioms Audio, experiments selected for demotion, and `z-archive` sort after active study trees. A different label requires changing the draft mapping before migration. | An owner-specified sort-last label. |
| Exact surface-collision policy | `defer-to-hub-manifest` | Add reversible `estate::surface_collision::<group-id>` evidence tags only. Do not infer a canonical expression/sense from equal target+English text, select a winner, move a schedule, or merge history. The accepted Hub's checksummed, sense-resolved ID manifest decides the eventual disposition. | `keep-all` leaves the 2,646 groups untagged; every old task is still archived intact by phase 3. |
| `EXPERIMENTS-YT` | `suspend_and_demote` | Its 27 `YouTube Audio Phrase v3` cards and all 43 reps remain intact under `zz Dormant::Experiments::EXPERIMENTS-YT::Ciumes do Uber`, but stop being studied. Phrase v3's target/audio-to-English task cannot safely donate its schedule to the active English-to-target Fluency task. | `keep` preserves the existing top-level tree and active state. Any later EN-to-target replacement must be created from the sense-resolved Hub manifest with a compatible or fresh schedule. |

Record the approved values in a copy of `anki_reorg_scripts/odd_decisions.example.json` beside the disposable collection copy. The recommended structural choices correspond to `native_branch_labels: numbered-english` and `personal_errors_branch: 6 My Errors`. The scripts refuse unsupported structural values, and phase 7's `--policy` must exactly match `dedupe_policy`.

The Expression Hub's four choices are already settled upstream (owner verdict, 2026-08-07): normally six initial examples with no hard cap, Balanced weakness policy, `<Language>::4 Exercises::Diagnosed trouble spots`, and the vertical comic rail. The estate plan reserves those deck destinations; they are not additional open decisions here.

---

## VERDICTS (owner, 2026-08-07)

All six recommendations ACCEPTED verbatim: code-plus-english roots,
numbered-english branches with native leaves, personal errors to
`6 My Errors`, `zz Dormant` root, `defer-to-hub-manifest` collisions
(tag-only), EXPERIMENTS-YT `suspend_and_demote`. Approved values live in
`anki_reorg_scripts/odd_decisions.approved.json`. With the Expression
Hub's four upstream verdicts this closes every open decision: the
migration may be sequenced.
