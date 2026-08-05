# State of Play — 2026-08-05

## 1. Executive summary

The last ten days comprise 154 commits through `06cd4c8` and turned the project into a six-family learning system rather than only a video-to-idiom pipeline.  
The syllabus packages now contain 895 grammar cards, 953 Exercises 2.0 notes/1,906 cards, 732 translation cards, and 40 podcast cards.  
The idiom side has 2,732 audio-ready didactic cards, 16,386 sentence-expression cards, two 2,732-card directional audio pools, and 365 per-video packages.  
Every latest package row is acknowledged `ok`, but one agent serves both profiles and an acknowledgement does not identify the importing profile.  
The claimed old-profile purge did not fire, the purge file is no longer armed, and substantial cross-profile duplication remains.  
Disk is again close to the action line at 9.04/10.46 GB used with 1.41 GB free; current rolling pool packages alone occupy 4.41 GB.  
CONDITIONALS remains exactly one word away: 15 inputs covering 299 prompts in each of five languages are staged and have never run.  
The highest-value strategy gap is grammar-wide review telemetry plus the weekly planner; a new Rescue-only daily revlog autopilot proves scheduled ingestion but does not plan grammar targets.  
There are 32 immediately viable grammar top-up cards, 12 more behind the broken Portuguese regência verifier, one static F3 slot, and 104 reviewed F4 pairs ready for deterministic conversion.  
Two assumptions in the commission were wrong: the Mandarin audit was completed, and podcast episodes 2/10 already have per-line language markers; only their pilot and parser/renderer work are parked.  
Rescue Lab now has an enabled 24-hour/$1.50-per-invocation autopilot, but rollout produced at least four activation batches and the current snapshot has seven drafts, zero approvals, and no final report.  
One August 4 ENOSPC video is still failed and one July 31 video is still stuck in `processing`, so the health endpoint's green headline is incomplete.

## 2. Shipped, last 10 days

Audit window: 2026-07-26 through 2026-08-05; 154 commits, current audited head `06cd4c86b8b9`.

### Pipeline and infrastructure

- ElevenLabs became the primary TTS path with Gemini fallback (`e8f304b`), and mounted-disk cleanup moved into the worker (`e8f5788`).
- The rolling grammar generator, verifier, TTS and APKG path landed in `4f98713`/`2d138b8`; the initial ES package was 94 cards at apkg 848 and the current five packages total 895 cards.
- Citation-form extraction/storage/rendering landed in `37a49f3`; the live backfill now has only 2 rows left.
- The LingQ mirror (`9e46cfc`) is current through August 4 for all five target languages, and the personal-error registry (`0632d75`) ingested 11,481 normalized rows representing 13,747 occurrences with no staging backlog.
- The Anki study-data proof of concept (`f1c5fd0`) mapped revlog reviews back to stable note GUIDs; orphan support (`c17812c`) adopted the studied set and armed deletion of 3,465 never-studied GUIDs, recorded in `27d251f`.
- The local, unversioned add-on was inspected and does contain the profile guard, `_safe_refresh`, after-import/30-minute AnkiWeb sync, and full-sync refusal described by `59f050f`/`27d251f`; those records are documentation commits, not the implementation source.
- Rescue Lab shipped backend `c832322`, frontend `36879a7`, and deployment/handoff `33a214e`/`431c34c`; daily download-only AnkiWeb ingestion, struggle activation, and budget-capped Chinese-model draft generation followed in `9f56f53`/`3ac0630`.
- At 15:07 +08 the Rescue autopilot is enabled/configured at 24 hours, Qwen Image 3.0 Pro, up to three activations and $1.50 per invocation; live state is 266 items (21 active/245 candidates), 7 draft assets, 0 approved, 7 paid calls, and $0.2556 spend, while `last_report:null` leaves completion versus failure after stamping ⚠ unverified. The rise from 9 seeded to 21 active items requires at least four activation invocations during rollout, so the interval is not a hard daily limit; the exact invocation count is ⚠ unverified.

### Grammar initiative

- Waves 1–4 established five-language generation (`a434ea4`, `cb1c275`, `56b8386`, `8cab18b`), including the correction from European to Brazilian Portuguese (`b45841d`).
- The curriculum/dashboard shipped in `535bcba`/`37044d0`; code now has 67 active curriculum units and zero planned units, while four static explainer topics bring the live stats view to 71 topic rows.
- Ten reviewed banks contain 938 entries (`149c2d1`); F3 (`a0badfb`), bank units (`94bf847`), verifier tuning (`4aa9839`), promotions (`0da8a73`), German declension/passive (`dc412a9`), and F4 (`97c524e`) are implemented.
- Live personalized content is 91 F3 cards and 60 F4 cards; the live F4 registry has 164 active pairs, of which 104 still say `needs_conversion`.
- All 12 authored explainers are rendered and included in the grammar packages—ES 3, FR 4, DE 2, PT 3—via `3c0b53b`; the older strategy checkbox saying delivery is open is stale.
- Research/content capacity also landed: 35 reader chapters (`aad9cbe`), a 91-unit curriculum candidate map (`dfae96b`), five 50-item F2 banks (`96b195f`), and four SUBTLEX weight files (`4298ea0`, German deliberately omitted); F2 and weighting are not wired into runtime.
- Latest grammar packages are DE 101 cards/#1170, ES 288/#1192, FR 185/#1193, IT 156/#1287, and PT 165/#1286, all acknowledged `ok`.

### Podcast cards

- The renderer/model and five-card pilot landed in `55fd2bd`, with SVG normalization in `93b01bd` and loudness repair in `acc7832`.
- Episodes 1 and 3–9 landed across `01fa795`, `55fd2bd`, `46ff685`, `0452c5c`, `319f2ad`, `965b2b4`, `cf9e181`, and `39faaa8`: 8 episodes, 40 notes/cards, 80 SVG sides, 80 staged audio sides, and no generated images.
- The matching eight long-form MP3s—109.3 minutes—were rendered in `e5616d9`; episodes 2 and 10 are the only absent season files.

### Exercises 2.0

- The 13,377-note legacy tree was audited in `4fcb62e`; it proved the 2,612-note Italian branch was French, found 30 Spanish-backed PT notes, and judged the 94-note ES FALSE_FRIENDS deck roughly half toxic.
- The approved 42-note ES pilot landed in `adda362`; the frozen 17-field/two-template model and delivery path landed in `0537b63`.
- The Italian source was rebuilt in 27/27 chunks—2,589 renderings, zero French items, zero structural gate failures—in `bf9f642`/`9a59ace`.
- CONNECTING finished in five languages through `f72ce22`, `4fa6ab6`, `e111b0b`, `eb81726`, and `79523b5`: 953 notes/1,906 cards; latest apkgs DE #1356, ES #1337, FR #1340, IT #1396, PT #1355.
- Wave-3 evidence mining landed in `807c79d`/`06cd4c8`: 14,267 old whole-paradigm tense cards, 176,218 card reps, 178,942 actual revlog rows and 16,143 lapses became five profiles plus 300 machine-readable verb×tense priors; a per-person/paradigm/fork/history-strip review artifact is awaiting the user's verdict, and no TENSES deck has shipped.

### Translation decks

- The frozen one-template translation family landed in `e111b0b`: 732 eligible grammar drills, 732 existing target-language audio clips, and 732 cached English fronts across five languages.
- Sentence-only back audio was rebuilt in `0761c96`; latest packages are DE 79/#1391, ES 250/#1390, FR 146/#1392, IT 130/#1393, and PT 127/#1394.

### Incidents

- YouTube auto-dub defenses and purge/requeue support shipped in `c5fbfc6`; the local July archive names 62 decks and 3,800 GUIDs, but complete remote cleanup is ⚠ unverified.
- The July 31 web hangs were traced to synchronous ffmpeg work on the event loop and fixed with thread offload, per-language serialization, and per-card failure isolation in `46a118f`, `2af34cc`, and `95821d9`.
- The August 4 ENOSPC repair shipped orphan APKG sweeping, 30→12-day retention, and disk observability in `8d1e2ef`, `a7992c7`, `de1b6a0`, and `8f89ff6`; the six package builds documented by the incident were rebuilt, but video 9059 remains failed with ENOSPC.
- Wrong-profile recovery gained `/admin/reset-acks` in `a2b2766` and was recorded in `502a7ec`; local collection evidence shows that reset/import recovery did not restore profile isolation.

## 3. Live inventory

Base inventory snapshot: 2026-08-05 14:48 +08; Rescue state refreshed at 15:07 +08. Each language cell is `notes/cards · latest apkg id`. “Syllabus” means `evgeny@the-syllabus.com`; “+2” means `evgeny.morozov+2@gmail.com`.

| Deck family | DE | ES | FR | IT | PT | Local placement (intended) |
|---|---:|---:|---:|---:|---:|---|
| Grammar | 101/101 · #1170 | 288/288 · #1192 | 185/185 · #1193 | 156/156 · #1287 | 165/165 · #1286 | Syllabus (as intended) |
| Exercises 2.0 | 179/358 · #1356 | 207/414 · #1337 | 191/382 · #1340 | 201/402 · #1396 | 175/350 · #1355 | Syllabus + stale +2 copies (intended Syllabus) |
| Translation | 79/79 · #1391 | 250/250 · #1390 | 146/146 · #1392 | 130/130 · #1393 | 127/127 · #1394 | Both (intended Syllabus) |
| Podcast lessons | 10/10 · #1303 | 5/5 · #1301 | 10/10 · #1300 | 10/10 · #1305 | 5/5 · #1306 | Syllabus (as intended) |
| Idioms didactic pool | 591/591 · #1442 | 430/430 · #1430 | 431/431 · #1437 | 778/778 · #1414 | 502/502 · #1419 | Both family types observed (intended +2) |
| Fluency-expression pool | 3,546/3,546 · #1443 | 2,580/2,580 · #1431 | 2,586/2,586 · #1438 | 4,668/4,668 · #1415 | 3,006/3,006 · #1420 | Both family types observed (intended +2) |
| Idiom audio T→E / E→T | 591/591 each · #1444/#1445 | 430/430 each · #1432/#1433 | 431/431 each · #1439/#1440 | 778/778 each · #1416/#1417 | 502/502 each · #1421/#1422 | Both family types observed (intended +2) |
| Latest per-video deck | 5/5 · #1447 | 4/4 · #1435 | 5/5 · #1436 | 4/4 · #1413 | 8/8 · #1418 | Both family types observed; latest placement ⚠ unverified (intended +2) |

All 40 latest rolling rows and the five latest video rows above are acknowledged `ok` by the sole agent, `fedora-laptop`. The current expression catalog is DE 601, ES 440, FR 431, IT 778, PT 507; didactic pools are smaller where audio-ready cards cannot be built, while expression pools hold six sentence notes per included idiom.

Read-only local inspection found all current syllabus families in Syllabus, while +2 also contains all 732 translation notes and 763 stale Exercises notes (DE 188, ES 207, FR 193, PT 175, no IT), including 11 notes beyond the current packages. Syllabus contains substantial video/pool note types intended for +2. Exact current package placement and the remote AnkiWeb/iPad mirror are ⚠ unverified.

## 4. Open loops & unfinished business

Effort is hands-on engineering/content time: XS <2 hours, S <1 day, M 1–3 days, L 3–5 days.

| Rank | What it is | Why it is parked / evidence | Concrete next action | Effort |
|---:|---|---|---|---:|
| 1 | Make delivery profile-safe and finish cleanup | One agent serves both profiles, `/apkgs/pending` does not expose or route by `kind`, and acks do not locate imports. The old purge never fired: +2 still has all 11 fake-IT leaf decks/2,612 notes, all 91 PT BIG_TECH_PHRASES notes including the 30 contaminants, and all 94 ES FALSE_FRIENDS notes. No cleanup job is pending; today's `cleanup.done.json` is an unrelated 3,465-GUID Syllabus orphan job. | Choose canonical ownership; add kind-aware agent routing or separate agents/tokens; make cleanup jobs queued and uniquely archived; dry-run and re-arm the already-approved legacy purge; then reconcile duplicate current families without deleting studied state. | M, plus decision |
| 2 | Productize grammar telemetry and the weekly planner | This is the last unchecked strategy pillar. The new Rescue autopilot performs scheduled AnkiWeb ingestion but selects only failed `pool_expr` cards for Rescue; it does not persist general per-topic Again/Hard/confusion metrics or adjust grammar targets. | Reuse the safe download/GUID work to build incremental grammar review snapshots, per-topic metrics, orphan/adopted-note joins, and one read-only planner report before allowing automatic target changes. | L |
| 3 | Run CONDITIONALS Wave 2 | Fifteen chunk inputs are committed in `695470f`; each language has 299 prompts, but there are zero output/triage files. It is parked only on the user's “go.” | Say “go,” run the five-language/three-chunk jobs in parallel, gate and audit them, merge roughly 1,495 notes, then build roughly 2,990 cards. | M after one-word decision |
| 4 | Resolve disk architecture before the next large wave | Only 1.41 GB remains; current pools are 4.41 GB and package directories total 5,978.9 MB. The incident's own action threshold was about 1 GB. | Either upsize the Render disk now, or design delta/media-deduplicated pools; retain the orphan sweep and add an alert above 85% used or below 1.5 GB free. | XS for upsize; L for delta pools |
| 5 | Harvest deterministic grammar capacity | `pt_regencia_verbal` is 0 verified/48 rejected because bank metadata normalization and the Ø/leak check are broken. Separately, 104 reviewed F4 pairs await conversion: ES 32, FR 27, IT 10, PT 35. | Fix and test the PT verifier, regenerate its 12-card target, convert the 104 F4 pairs in small audited batches, and rebuild affected decks/translation packages. | S–M |
| 6 | Make the Rescue autopilot single-run safe | The 24-hour setting is only a read-then-write timestamp, not a lock; forced or overlapping workers can share an asset snapshot and multiply both the three-activation and $1.50-per-invocation caps. Moving 9 seeded items to 21 active requires at least four invocations; the exact count is ⚠ unverified. The current snapshot has 7 drafts/$0.2556 but `last_report:null`; paced image calls are awaited inside the video-worker loop. | Add an atomic DB lease and run ID with running/completed/failed states, a global daily spend limit and per-call asset recheck; move paid generation off video claiming, then review all seven drafts before further autonomous spending. | S–M |
| 7 | Reconcile video state and observability | Video 9059 is still failed from ENOSPC; video 8091 has remained `processing` since July 31 despite apkg 1118 being built/acked. There are 296 failed rows total, including 70 currently failed among videos first seen in the last 7 days, plus 34 queued; `/ui/api/videos` date filters return 500, `/health` says `ok`, and the UI digest says `stalled:false`. | Requeue 9059, reconcile 8091 idempotently, diagnose and fix the date-filter 500, classify recent failures, and make health fail or warn on any over-age processing row and low disk. | S |
| 8 | Close the error-aware generation loop | Phase 4 of the error-profile proposal is not implemented: personal errors do not enter generation prompts. F2 has 5×50 reviewed banks but no model/runtime/tests; frequency priors and private vocab weave lists are not consumed. | Implement F2 first, then add bounded prompt inputs for error counts, SUBTLEX weights, and reviewed vocab weave items with provenance and verifier tests; reconcile 55 slash-encoded Italian alternatives before weighting integration. | L |
| 9 | Let evidence choose the next grammar units | The roadmap has 91 candidates, but absent high-signal scopes remain: ES light verbs and numbers/dates; PT ser/estar/ficar; FR verb/infinitive prepositions, plural agreement, word order, negation, relatives, pronominal verbs and calques; DE n-declension, genitive and KII; IT subjunctive selection/imperfect/compound forms, hypothetical chains, article omission, and discourse connectives. | After telemetry, rank by observed failure/opportunity, promote one small unit at a time through the roadmap's source, uniqueness, deterministic-test, format, and telemetry gates. | M per unit |
| 10 | Continue Exercises 2.0 after CONDITIONALS | TENSES has ~300 prompts/lang, old-review profiles/priors, and a review artifact awaiting verdict, but no addendum, categories, runtime wiring, outputs, or deck. Its top 300 cells contain 46.37% of historical lapses but are exposure-biased and over-rank FR literary subjunctive/passé simple, IT passato remoto, and PT synthetic pluperfect. Later waves also remain unstarted. | Finish Wave 2; verdict the Tenses Rescue format and a practical-frequency/CEFR filter; add canonical tense/mood/person mappings and verifier fallbacks; reverify every form rather than copying old paradigms. | M–L per wave |
| 11 | Finish podcast season episodes 2 and 10 | Both cross-language source scripts already contain 97 explicit `TL: [lang]` lines and zero bare TL lines. The actual blocker is that `podcasts.py` hard-skips `lang: x`; podcast-card sources/SVGs for those episodes also do not exist. | Teach the parser/renderer to switch language per marked line, add mixed-language voice/cache tests, render the two MP3s, then author 10 cards/20 SVG sides if the format is still wanted. | M |
| 12 | Run the Mandarin Sentence-Walk pilot | The commission was executed, not ignored: 5,138 sentences, 3,050 films, 1,882 i+1 candidates, and 885 pilot-ready sentences were audited. P1 stopped deliberately before writes. | Approve the one-lesson/5-card pilot, choose its deck root, review the zh voice bake-off, and calibrate whether LingQ status-0 counts as “met.” | M after decisions |
| 13 | Expand F3 carefully and repair source gaps | Live F3 is only 91 cards against 3,319 private high-confidence candidates; exact remaining eligibility after dedupe is ⚠ unverified. The Teachee extract supplied 3,433 rather than the commissioned 3,502 rows, and `fr_genre_noyau` has only 19 exact personal nouns plus 21 proxies. | Reconcile the missing 69 source rows against the original store, replace the French proxies from the 297-row raw extract, then convert F3 in reviewed, telemetry-gated batches. | M |
| 14 | Repair the operating documents and two tiny tails | `FEATURES.md`, `GRAMMAR_STRATEGY.md`, the Changelog's superseded entries, and the error proposal disagree with live state; `unit-specs/README.md` contains raw merge-conflict markers; Rescue handoff says both that a paid glyph exists and that none was generated; `SYNTHESIS_V2.md` was never produced. Citation backfill has 2 rows left. | Resolve the conflict markers, close the two citations, regenerate the standing status sections from live endpoints, and replace stale checkboxes/counts with dated snapshots. | S |

### Commission execution ledger

- Executed end to end: CODEX A/B/C/D/E/F/H/I/J/K/L/N/Q; Grammar Frontend; Exercises pilot, batch, and Italian rebuild; Translation; Podcast Cards pilot and seven-episode batch; Rescue Lab; and the Mandarin Phase-0 audit. All ten individual bank-unit specs were implemented; the F3, F4, explainer, and podcast design files were consumed by shipped work.
- Executed as commissioned artifacts but not integrated into the product: CODEX G vocab mine, CODEX P F2 design/banks, and CODEX R frequency weights; R intentionally has no German file.
- Partially delivered relative to the broader product: CODEX M authored all 10 podcast scripts but rendered 8; ERROR_PROFILE_PROPOSAL's registries/banks/formats shipped but error-aware generation and the promised synthesis v2 did not.
- Never run: `EXERCISES2_CONDITIONALS_ADDENDUM` content generation—15 inputs exist, no outputs or triage files. The present State-of-Play commission is fulfilled by this report.
- Documentation acceptance state is not execution truth: Grammar Frontend's boxes remain unchecked despite live code, and the umbrella unit-spec README is damaged even though its ten child specs shipped.

### Corrections to the commissioned prior knowledge

- Confirmed: Exercises 2.0 counts/model, translation counts/model and sentence-only back audio, episodes 1/3–9, the web-hang fix, ENOSPC janitor/retention/disk endpoint, and local `_safe_refresh` implementation.
- Contradicted: the old-account purge did not fire; wrong-profile delivery is not resolved; local duplication is 11 extra demoted Exercises notes rather than “about 6”; one explicit ENOSPC video remains failed.
- Contradicted: Mandarin was fully engaged for its audit and stopped only at the approval gate.
- Contradicted: episodes 2/10 do not need language markers; they need parser/renderer support for markers already present.
- Contradicted: most named “never-created” units are live—`es_muy_mucho`, `pt_gender_core`, `pt_regencia_verbal`, four French bank units, `de_dativ_verben`, `de_adj_endings`, `de_passiv`, two Italian bank units, and Romance F4 successors. Portuguese regência exists but is functionally empty.
- Contradicted: explainer TTS/delivery is not open; all 12 authored explainers are in the current grammar packages.
- Scoped, not blanket-confirmed: the incident's six failed package builds were rebuilt, while one separate ENOSPC video remains failed; complete auto-dub cleanup and remote profile placement are ⚠ unverified.

## 5. Generation capacity map

| Source of more content | Ready capacity now | Gate / command path |
|---|---|---|
| Grammar target top-ups | Raw shortfall 45 across 19 units: ES 5 (`pres_irreg`, `subj_imp`, `clitics_dir`, `clitics_selo`, `muy_mucho`, each −1); DE 9 (`adj_endings` −1, `passiv` −3, `dativ_verben` −5); FR 10 (`subjonctif_conjonctions` −4, `prep_lieux` −5, `an_annee` −1); IT 6 (`presente`, `condizionale`, `clitici` −1 each, `reggenze` −2, F3 −1); PT 15 (`presente` −2, `clitic` −1, `regencia` −12). | 32 healthy F1 cards can generate immediately; fix PT regência to unlock 12; the IT F3 slot must come from registry conversion, leaving 44 F1 top-up slots in total. |
| Reviewed F4 pairs | 104 deterministic conversions: ES 32, FR 27, IT 10, PT 35; 60 are already live. | Convert in small batches through the existing F4 path, inspect output, rebuild. |
| Personal-error F3 | 3,319 high-confidence private candidates versus 91 live cards; exact post-dedupe remainder is ⚠ unverified. | Repair source/proxy gaps, select verbatim errors, convert through existing F3 machinery, and cap batches by telemetry. |
| Exercises 2.0 | CONDITIONALS: 299 notes/lang, 1,495 notes/2,990 cards potential, inputs ready. TENSES has ~300 prompts/lang plus 60 ranked verb×tense cells/lang mined from 14,267 old cards/176,218 card reps and a pilot review artifact; later sizes are FANCY_VOCAB 582, vocab trio 640, BIG_TECH_PHRASES 90, then FALSE_FRIENDS. | CONDITIONALS needs only “go.” TENSES needs the format/frequency verdict, a new addendum/categories, canonical person-tense adapters, and morphology revalidation; its source drilled whole paradigms and contains known errors. Later waves use the established generation → gate → audit → build path. |
| Translation | The current automatically derived stock is 732 cards; every new verified grammar drill with usable target audio is marginal capacity without new target-language synthesis. | Rebuild after grammar growth; English fronts cache, target backs reuse grammar audio. |
| F2 interpretation | 250 reviewed items, 50 per language. | Build and freeze the F2 note model/runtime/verifier/tests first; no production path exists today. |
| Vocab personalization | Private weave lists hold DE 36, ES 95, FR 200, IT 24, PT 200 reviewed terms; four language frequency priors are reproducible. | Wire bounded, provenance-tagged prompt inputs; resolve Italian alternative encoding; German needs a different frequency source by design. |
| Explainers and podcasts | All 12 commissioned explainers and eight single-language podcast episodes are built. Two marked cross-language scripts can add 2 MP3s; authoring the matching card lessons would add 10 cards/20 SVG sides. | Implement mixed-language parsing/voice switching and tests, then author/review the card sources. The 35 reader chapters are candidates for a separately commissioned season 2, not ready audio jobs. |
| New grammar units | The absent error-profile scopes in §4 are buildable through the existing generator; the broader roadmap adds 91 CEFR/evidence candidates. | Use telemetry and roadmap promotion gates before adding breadth; one small unit at a time. |
| Mandarin | 885 sentences are pilot-ready and the scalable P2 pool can grow from 885 toward 1,882 in 20-card batches. | P1 decisions first; then one 5-card/10-sentence pilot, scratch-profile import, and explicit format verdicts before P2 volume. |
| Rescue | At the current rollout snapshot there are 21 active items, 245 candidates, 15 active items without any asset, 7 drafts/0 approvals, and $0.2556 spent. Autopilot can activate up to 3 and spend $1.50 per invocation with Qwen 3.0 Pro at $0.037/image; the 245-candidate queue is at least 82 more three-item passes before replenishment. | Stop overlap first, verify the run report, and review every draft; auto-approval is deliberately forbidden, automatic recovery retirement is absent, and APKG export/building remains manual. |

## 6. Risks & watch items

| Risk | Current evidence | Watch / control |
|---|---|---|
| Disk exhaustion recurrence | 10.46 GB total, 9.04 GB used (86.4%), 1.41 GB free; current pools 4.41 GB; package dirs IT 1,579.0 MB, DE 1,282.0, PT 1,112.3, ES 1,064.0, FR 941.6; grammar staged audio 812.6 MB and media stage 200.8 MB. | The proposed 85%/1.5-GB alert is already breached; check the orphan sweep after every large build and settle upsize versus delta pools before CONDITIONALS delivery. |
| Profile/data integrity | One agent, no kind routing, duplicate translation and Exercises families in +2, pool/video types in Syllabus, legacy toxic decks intact, no pending cleanup job. | Do not use ack=`ok` as profile proof; inventory both collections after sync and use uniquely archived, profile-pinned cleanup manifests. |
| Pipeline state is greener than reality | `/health` says `ok` with 34 queued; the UI digest says `stalled:false` while showing 296 failed, 70 currently failed among videos first seen in 7 days, and 2 processing, including one five-day stale row and one current ENOSPC failure. | Add age- and failure-aware health signals, repair date filters, and reconcile stuck rows idempotently. |
| Portuguese regência quality | 0/48 accepted, versus a target of 12; 42 rejects are bank-metadata mismatches and 6 are answer-leak failures. | Block blind regeneration until deterministic verifier tests pass. |
| Content provenance/precision | Original Teachee count is short by 69; 21 French gender entries are proxies; exact F3 remaining eligibility is not exposed; Italian frequency alternatives include 55 slash-encoded cells. TENSES priors are 4–11 years old, exposure-biased whole-paradigm signals with corrupt forms and incomplete morphology coverage; their report calls 176,218 `cards.reps` “reviews” although revlog has 178,942 rows. | Preserve source labels, repair known gaps, frequency-filter/reverify tense forms, split persons, and require reviewed small batches before scale. |
| Documentation as an unsafe control plane | FEATURES says 61 units and old delivery statuses; strategy/checklists say shipped work is open; the unit-spec README has merge markers; Rescue handoff contradicts live spend. | Treat live endpoints plus code as truth until docs are repaired; generate future counts from the API where possible. |
| Single-machine operational dependency | The sole `fedora-laptop` agent serves all five languages and both profiles; local add-on hardening is not versioned in this repo. | Version or reproducibly package the add-on, split delivery identity, and keep full-sync conflicts human-approved. |
| Rescue autopilot spend/state | The configured maximum is $1.50 per invocation, not a global daily cap; moving 9 seeded actives to 21 requires at least four activation batches, exact count ⚠ unverified. The ledger is $0.2556 across 7 calls with 7 drafts/0 approvals, and `last_report:null`. A crash after the start stamp suppresses scheduled retry for 24 hours; overlapping runs can duplicate drafts/spend, and the main video worker awaits 1-RPM paid generation. File, asset-row, and ledger writes also lack one transaction. | Keep no-auto-approval; add an atomic lease/run state, global daily budget and immediate asset recheck; isolate generation from video claiming; make storage/ledger recovery explicit; add integration/concurrency tests and regenerate the dependency lockfile. |

## 7. Decisions owed by the user

1. Say **GO** on CONDITIONALS; this unlocks the 15 staged jobs and a five-language 1,495-note/2,990-card Wave 2.
2. Choose canonical profile ownership and kind-based routing—prefer separate delivery identities—and set the retention rule for studied duplicates; this unlocks safe reconciliation and re-arming the displaced legacy purge.
3. Choose a paid disk upsize now or fund the delta/media-deduplicated pool redesign; this unlocks the next large build without another ENOSPC gamble.
4. Confirm grammar-wide telemetry/planner as the next engineering milestone before broad new-unit work, or explicitly choose another priority; this unlocks evidence-driven targets beyond Rescue's narrow `pool_expr` signal.
5. Approve or reject purging the still-present 94-note legacy ES FALSE_FRIENDS deck; this removes a known-toxic study surface without using it as rebuild source.
6. Give Tenses Rescue №1 a format verdict and approve practical-frequency/CEFR filtering instead of literal lapse order; this unlocks Wave-3 authoring without reviving whole-paradigm or literary-tense bias.
7. Decide whether episodes 2/10 merit mixed-language parser work and ten more podcast cards now; this unlocks completion of season 1.
8. Approve the Mandarin P1 pilot and decide its deck root, voice bake-off, tone-color mapping, native-audio extension, and “status-0 means met” calibration; this unlocks the 5-card Sentence-Walk trial and later 885→1,882-card scale path.
9. Review the seven Rescue drafts and decide whether the autopilot remains enabled while its concurrency/run-state defects are repaired; if yes, confirm Qwen and the $1.50-per-invocation cap—which is not a global daily cap—to unlock safe tending and the APKG-builder commission.

### What this report could not see

⚠ unverified: the live Render database beyond what the read-only endpoints expose; Render logs and provider job internals; whether the stamped Rescue invocation completed, failed, or remained running; the original Teachee source needed to settle the 69-row discrepancy; the exact F3 remainder after deduplication; whether complete auto-dub cleanup occurred; and the Tenses Rescue review artifact itself, which is recorded in the Changelog but not stored in the repository.

⚠ unverified: whether the remote AnkiWeb and iPad collections exactly match the two local desktop collections, the review state of every duplicate/misdelivered note, and whether today's cleanup marker removed every intended note—the marker stores its input spec, not removal counts.

The private `idiomatic-data` artifacts and both local desktop collections were visible read-only for this audit; there was no server POST, direct production-DB query, git command, secret disclosure, or write other than this commissioned report.
