# Anki estate inventory

Study snapshot: 2026-08-07. This is an evidence report, not an executed migration. Every collection query below used an immutable SQLite connection to a decompressed **copy** of the newest automatic backup. The live `collection.anki2` was never opened or queried, and no live collection, pipeline, add-on, or media file was changed.

## Snapshot and reproducibility

| Evidence item | Value |
|---|---|
| Newest automatic backup | `backup-2026-08-07-10.18.10.colpkg` |
| Backup modification time | 2026-08-07 10:18:10.779841676 +0800 |
| Backup bytes / SHA-256 | 15,286,386 / `0ca3c881ec2117cb6531dcc5f9b8bb480b19b7a4ad3a01e1171d9c305595210d` |
| Decompressed copied DB bytes / SHA-256 | 78,802,944 / `c8410d43ee8183bb1e25cf316717366572d2f5607fa0e5e9f4e4a3d6c2a7e59e` |
| SQLite validation | `PRAGMA quick_check` = `ok` |
| Reader | Python `anki` 25.9.2; SQLite immutable/query-only mode |
| Reproducer | `anki_reorg_scripts/00_inventory.py` |

The `.colpkg` archive passed an archive test and contained `collection.anki21b`, the compatibility `collection.anki2`, `meta`, and a nine-byte media-name map. It carried no media payload. The compressed collection was decompressed under `docs/research/anki_reorg_work/`; that entire scratch tree is ignored by the local `docs/research/.gitignore` and is not a deliverable.

## Executive inventory

- 1,031 deck rows contain 74,805 notes and 82,738 cards. There are 218 decks with no direct cards and 67 completely empty subtrees; many are valid container/system decks, so neither number is a deletion list.
- Scheduling investment is material: 4,623 cards have intervals over 21 days, 10,713 cards are in review state, current cards record 61,195 reps, and the revlog has 62,314 rows. Of those revlog rows, 62,167 refer to current cards and 147 refer to deleted cards.
- The snapshot has 71,776 new cards, 249 learning/relearning cards, eight suspended cards, no buried cards, and no card currently occupying a filtered deck. All eight suspensions are Mandarin Props relearning cards; together they carry 419 reps and must remain suspended.
- There are 56 note types. Their exact stored field order and templates appear in the generated model catalog; the `Mxx` codes cross-reference every current deck that uses each type in the full tree.
- Five notes have no cards, all using `ChinesePod Word v3`. Two long-audio notes span Spanish and Portuguese decks even though their content/tag is Portuguese (`por parte de`); subtree note totals are consequently not always additive.
- All 1,030 normal decks use the `Default` deck options group. `Custom Study Session` is an empty filtered deck. No source template has a real target-deck override; all 56 note types carry a nonzero but explicitly unused/dangling target-deck value. The collection's `curModel` UI setting is also stale.
- Three archive paths (`de`, `fr`, `it`) lack an explicit intermediate parent row. Anki APIs understand the hierarchy; raw string/SQL renames are therefore unsafe.

## Where the scheduling mass lives

The estate is lopsided: most new pipeline material is unseen, while the legacy, Mandarin, and two Pimsleur branches hold nearly all mature investment.

| Current subtree | Notes | Cards | Mature (`ivl > 21`) | Review-state cards | Card reps |
|---|---:|---:|---:|---:|---:|
| `Idiomatic::German` | 5,940 | 6,814 | 0 | 0 | 1 |
| `Idiomatic::Spanish` | 4,489 | 5,386 | 0 | 0 | 1 |
| `Idiomatic::French` | 4,343 | 5,128 | 0 | 0 | 0 |
| `Idiomatic::Italian` | 8,079 | 9,551 | 84 | 689 | 1,343 |
| `Idiomatic::Portuguese` | 5,188 | 6,163 | 6 | 156 | 310 |
| `Idiomatic::z-archive` | 236 | 236 | 0 | 2 | 18 |
| `Languages::German` | 947 | 1,179 | 310 | 935 | 2,591 |
| `Languages::Spanish` | 527 | 527 | 53 | 512 | 1,099 |
| `Languages::French` | 1,153 | 1,503 | 380 | 1,114 | 3,544 |
| `Languages::Italian` | 1,214 | 1,494 | 957 | 1,212 | 6,025 |
| `Languages::Portuguese` | 884 | 989 | 416 | 860 | 3,451 |
| `Languages::Mandarin` | 2,600 | 2,614 | 12 | 161 | 270 |
| Generated grammar/exercises/tenses/translation/rescue families | 3,559 | 5,391 | 0 | 254 | 283 |
| `Pimsleur` (all languages) | 34,211 | 34,211 | 1,776 | 3,005 | 14,184 |

Pimsleur's mature cards are concentrated entirely in Mandarin (1,278) and Italian (498). Course placement counts are:

| Pimsleur course | Cards | Mature | Reps |
|---|---:|---:|---:|
| Danish | 612 | 0 | 0 |
| Dutch | 609 | 0 | 0 |
| French | 4,693 | 0 | 0 |
| German | 5,311 | 0 | 11 |
| Italian | 5,344 | 498 | 1,892 |
| Mandarin | 3,043 | 1,278 | 12,271 |
| Norwegian | 1,216 | 0 | 0 |
| Portuguese | 4,344 | 0 | 9 |
| Spanish (Spain) | 4,378 | 0 | 1 |
| Spanish (Latin America) | 4,051 | 0 | 0 |
| Swedish | 610 | 0 | 0 |

The standalone Mandarin families must only acquire a common parent. Their current direct mass is:

| Mandarin family | Notes | Cards | Mature | Reps | Revlog rows on current cards |
|---|---:|---:|---:|---:|---:|
| Actors | 55 | 55 | 45 | 1,091 | 1,091 |
| Characters 2026-06-20 | 222 | 222 | 1 | 366 | 366 |
| China Provinces | 34 | 204 | 0 | 9 | 15 |
| Locations | 13 | 13 | 0 | 67 | 68 |
| Palace | 339 | 339 | 0 | 1 | 1 |
| Props | 599 | 599 | 583 | 26,391 | 26,890 |
| Zones | 65 | 65 | 0 | 73 | 73 |

## Pipeline generations and discontinued audio

The current Idiomatic expression branches contain 348 nonempty per-video decks holding 2,428 Cloud-v2 cards. Every one is still new with zero reviews: DE 477, ES 421, FR 383, IT 744, PT 403. The `z-archive` adds 236 Cloud source cards, including 201 older Cloud-v1 cards.

The long Idioms Audio projections are not disposable even though they should stop appearing in study. They contain 12,629 cards across 6,657 notes. The EN→target model has 6,064 cards and 324 mature cards; target→EN has 6,565 cards and 255 mature cards. The proposed migration therefore suspends and demotes these cards while retaining every note, field, GUID, interval, and revlog row.

## Provenance and tag taxonomy

The database registers 701 tag names; 688 are assigned to at least one note, and 929 notes are untagged. The dominant assigned tags are `pimsleur` (34,211 notes), `youtube` (33,054), `quickmatch` (20,860), `fluency-pool` (20,231), `flashcard` (13,351), and `idiom-audio` (6,657). Language, system/family, lesson, level, video-ID-like, slug-like, and hierarchical namespaces are counted in the generated taxonomy below.

All 33,054 `youtube` notes have a nonempty `Source` field, covering 3,287 distinct source strings and 425 parsed YouTube IDs. Only 2,664 notes already carry a raw video-ID tag (370 distinct IDs), so deck collapse cannot rely on existing tags alone. The provenance draft adds, before any move:

- `youtube` where absent;
- `lang::<code>`;
- `source::youtube::<video-id>` when the Source URL yields one;
- `estate::origin::<12-hex>` with a journaled hash-to-original-deck map.

On this copy that phase would add tags to 3,261 notes, creating 413 origin mappings. Raw titles and URLs remain in existing Source fields. All 34,211 Pimsleur notes already have complete source/lesson provenance.

## Duplicate and collision census

The conservative comparison strips media/HTML, HTML-unescapes, applies Unicode NFKC, normalizes curly quote/dash variants, collapses whitespace, and case-folds while preserving accents and punctuation. An automatic collision requires both normalized target text and English gloss to match. A target-only match is a review candidate, never deletion evidence.

Across 4,725 unambiguously classified legacy notes and 28,271 Idiomatic notes, exactly four primary bilingual expression keys cross generations; no primary fluency-sentence key does. Counts include the source/pool/audio representations attached to one semantic expression.

| Language | Exact bilingual key | Legacy notes / cards / reviews / mature | Idiomatic notes / cards / reviews / mature |
|---|---|---:|---:|
| ES | `más bien` ↔ `rather / more like` | 1 / 1 / 1 / 0 | 4 / 6 / 0 / 0 |
| IT | `quando si tratta di` ↔ `when it comes to` | 3 / 5 / 6 / 1 | 4 / 6 / 0 / 0 |
| PT | `afinal de contas` ↔ `after all / at the end of the day` | 2 / 3 / 2 / 0 | 4 / 6 / 0 / 0 |
| PT | `tanto que` ↔ `so much so that` | 2 / 3 / 3 / 0 | 4 / 5 / 0 / 0 |
| **Total** | **4 keys** | **8 / 12 / 12 / 1** | **16 / 23 / 0 / 0** |

No YouTube source ID is shared across generations for these keys: the expressions recur in different videos rather than being reimports of the same source. The only secondary exact sentence atom is `Ella hizo frente a sus miedos y habló en público.` ↔ `She faced her fears and spoke in public.` It is example reuse inside larger notes, not safe note-level dedupe.

Strict target-only matching produces 23 cross-generation candidates; punctuation relaxation adds one. They cover 53 legacy and 95 Idiomatic notes. Legacy carries 129 reviews and 24 mature cards across them; Idiomatic carries none. The complete manual-review queue is:

- DE: `durchgesickert`; `leer stehen`.
- ES: `al margen de`; `hacer frente a`; `más bien` (exact); `sin duda alguna`.
- FR: `compte tenu du`; `ne cesse de`; `pour le coup`; `remise en cause`; `à deux doigts de`.
- IT: `a che punto siamo?` / `a che punto siamo` (punctuation-only); `al di là di`; `guarda caso`; `in funzione di` (likely polysemy); `in parole povere`; `nel senso che`; `quando si tratta di` (exact); `se non fosse che`.
- PT: `afinal de contas` (exact); `dar certo`; `desde o primeiro momento`; `recorrer a`; `tanto que` (exact).

The larger deterministic collision is inside the current pipeline: Cloud source notes use a per-video GUID, while pooled notes use a language/expression GUID. Exact source-versus-pool overlap is:

| Language | Exact keys | Source notes | Pool notes | Source reviews | Pool reviews | Mature either side |
|---|---:|---:|---:|---:|---:|---:|
| DE | 586 | 586 | 586 | 8 | 0 | 0 |
| ES | 417 | 417 | 417 | 0 | 0 | 0 |
| FR | 417 | 417 | 417 | 3 | 0 | 0 |
| IT | 753 | 754 | 753 | 5 | 0 | 0 |
| PT | 448 | 448 | 448 | 2 | 0 | 0 |
| **Total** | **2,621** | **2,622** | **2,621** | **18** | **0** | **0** |

This covers 92.0% of 2,849 pool notes and 98.4% of 2,664 per-video/archive source notes. All 201 Cloud-v1 archive notes match a pool note. Sixteen source groups hold the 18 reviews; they are archive cards. A schedule-first dry run selects 2,621 winners and 2,626 loser notes (the extra notes are cross-generation and one duplicated Italian source). The draft only tags and suspends losers; it never deletes notes, rewrites GUIDs, merges revlog, or converts Cloud-v1 to Cloud-v2.

## Media reference and orphan estimate

The backup itself contains no media payload, so it can establish references but cannot prove live presence or orphanhood. Copied-note fields contain 147,859 local-media occurrences and 137,554 unique filenames across 74,651 notes: 145,323 `[sound:...]`, 1,427 video `src`, and 1,109 image `src` occurrences. Unique extensions are 135,540 mp3, 954 jpg, 816 webm, 136 png, 100 mp4, seven jpeg, and one webp. No template/config contains a hard-coded local media reference.

To provide the requested estimate, one ancillary comparison read **only directory-entry names and stat metadata** from the live `collection.media` at approximately 2026-08-07 10:38:42 +0800. It did not open file contents or the live database. That directory had 295,889 regular files / 17.760 GiB:

- 137,553 of 137,554 copied-DB references had an exact filename match.
- The one missing reference is `\-2qnze5hq.webm`, on Mandarin Prop note `1775530298029` (`Video` field). Its card has a 2,163-day interval, 28 reps, and 28 revlog rows; companion `420_bs.jpg` is present. This must be repaired, not cleaned away.
- The raw unreferenced upper bound was 158,336 files / 6.501 GiB. Excluding 47 underscore-prefixed static files and 158 files modified after the collection snapshot leaves **158,131 orphanable candidates / 6.482 GiB**: 53.44% of files and 36.49% of bytes.
- Of those candidates, 7,037 files / 1.628 GiB reduce to a referenced basename after removing a trailing `-<40 hex>` collision suffix, strong name-level evidence of historical collision-renamed residue.

The 158,131 figure is deliberately an upper bound, not a deletion list. Backup/live skew, unreliable mtimes, live-only notes, add-on references, and collision-renamed files can all produce false positives. Any later media cleanup needs a fresh backup copy, preservation of candidates, content hashing, and Anki's own media checker. No media deletion script is part of this commission.

## Inventory caveats

- Revlog deck attribution uses each surviving card's current deck. Historical filtered/cram reviews account for 17,815 revlog rows, but past deck locations cannot be reconstructed from revlog alone.
- Mature means the stored `ivl` is greater than 21 days, exactly as commissioned. It is not an FSRS stability estimate.
- Parent subtree note totals are distinct-note counts and are intentionally non-additive when a note has cards in more than one deck.
- Stored deck names use Anki's `\x1f` separator. The report renders it as `::`; draft mutations use public Anki APIs.
- The complete generated tables below are the source of truth for every deck/model/tag count. Human summaries above are derived from the same copied SHA-256.

## Generated collection totals

| Metric | Count |
|---|---:|
| decks | 1,031 |
| empty_direct_decks | 218 |
| empty_subtree_decks | 67 |
| notes | 74,805 |
| notes_with_cards | 74,800 |
| cards | 82,738 |
| new_cards | 71,776 |
| learning_or_relearning_cards | 249 |
| review_state_cards | 10,713 |
| suspended_cards | 8 |
| buried_cards | 0 |
| filtered_deck_cards | 0 |
| mature_cards | 4,623 |
| card_reps | 61,195 |
| revlog_rows | 62,314 |
| revlog_rows_for_current_cards | 62,167 |
| orphaned_revlog_rows | 147 |
| orphan_notes | 5 |
| note_models | 56 |
| registered_tags | 701 |
| used_tags | 688 |
| notes_without_tags | 929 |
| referenced_media_files | 137,554 |
| media_reference_occurrences | 147,859 |

## Generated full deck tree

Counts are attributed to each card's current deck. `Mature` means `ivl > 21`; `revlog` is joined to cards that still exist. Parent rows show subtree totals, while `direct` columns show only cards physically assigned to that deck.

| Current deck | Direct notes | Direct cards | Subtree notes | Subtree cards | Mature subtree | Reps subtree | Revlog subtree | Models on direct cards |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Custom Study Session | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| Default | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| EXPERIMENTS-YT | 0 | 0 | 27 | 27 | 0 | 43 | 43 | — |
| ↳ EXPERIMENTS-YT::Ciumes do Uber | 27 | 27 | 27 | 27 | 0 | 43 | 43 | M39 |
| ↳ EXPERIMENTS-YT::Dia Util | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ EXPERIMENTS-YT::Webtest | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ EXPERIMENTS-YT::Webtest::CIÚMES DO UBER | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| Idiomatic | 0 | 0 | 28,273 | 33,278 | 90 | 1,673 | 1,673 | — |
| ↳ Idiomatic::de | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ Idiomatic::fr | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ Idiomatic::French | 0 | 0 | 4,343 | 5,128 | 0 | 0 | 0 | — |
| ↳ ↳ Idiomatic::French::2026-07-11 · Comment Bally Bagayoko est intervenu en faveur de deux frères condamnés pour trafic de drogue | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-11 · Mondial 2026 : la FIFA SOUS INFLUENCE DE TRUMP | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-11 · MORTALITÉ périnatale : les ALERTES sans réponse | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-11 · SYRIE : continuer à RECONSTRUIRE après Assad | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · 10 ans de l'attentat de Nice : la colère d'un grand-père | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Afrique du Sud : pourquoi les violences contre les migrants africains se multiplient-elles ? | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Air Force One : panique sécuritaire autour de Trump | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Attentat de Nice : le récit de l'attaque du 14-Juillet 2016, minute par minute | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Attentat Nice : 10 ans après, des milliers de personnes défilent en hommage aux victimes | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · En France, les sans abris, les oubliés de cette canicule • FRANCE 24 | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Hommage à Alfred Dreyfus : Emmanuel Macron appelle à la vigilance face à l'antisémitisme | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · La Crimée, cible des Ukrainiens | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · L’Union Européenne va pouvoir accéder à vos messages privés, explications | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Monaco : la suspecte de l'attentat retrouvée morte | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Netanyahu manipule-t-il Trump ? | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Présomption de légitime défense pour les forces de l'ordre : la LDH dénonce "un permis de tuer" | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Rokia Traoré : prison, combat judiciaire et retour sur scène avec Fifty-Fifty • FRANCE 24 | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Sommet sur les minerais critiques à Abidjan : l'Afrique veut transformer davantage • FRANCE 24 | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Trump, cible numéro 1 de l’Iran | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Un tournant majeur vient de se dérouler au Moyen-Orient | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-12 · Violences faites aux femmes en hausse pendant la canicule : comment protéger les victimes ? | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-13 · Jordan Bardella: « Marine Le Pen aspire à présider la France. Je souhaite la gouverner. » | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-13 · Jordan Bardella: « Marine Le Pen aspire à présider la France. Je souhaite la gouverner » | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-13 · La tapisserie de Bayeux à Londres : un prêt controversé • FRANCE 24 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-18 · Finale du mondial 2026 : Roja contre Albiceleste, qui soutenir ? • FRANCE 24 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-18 · Visite éclair pour Macky Sall qui sollicite l'appui du Sénégal pour sa candidature à l'ONU | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-19 · La solution à la canicule dont personne ne veut | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-19 · Mondial 2026 : "Gianni Infantino s'est comporté comme un laquais de Donald Trump" • FRANCE 24 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-19 · Quel bilan pour les équipes africaines au Mondial 2026 de football ? • FRANCE 24 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-19 · Septembre 2026 : une rentrée politique sous tension • FRANCE 24 | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-20 · Bernard Arnault : enquête sur la première fortune de France | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-20 · Le président gabonais Brice Oligui Nguéma entame une visite d'état de 3 jours en France • FRANCE 24 | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-21 · La France veut couper les réseaux sociaux aux moins de 15 ans | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-28 · Iran : la stratégie de Trump en question | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-28 · Ukraine : la nouvelle relation Zelensky-Trump | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-28 · Zinédine Zidane, une légende à la tête des Bleus | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · "Ce sont nos rockstars", l'un des animateurs de "Princesse Mononoke" à Paris pour la Japan Expo | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · "La colère monte" deux semaines après le séisme au Venezuela | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Baisse des subventions pour la culture : "Des méthodes inadmissibles", pour Florence Portelli | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Cameroun : séjour d'une longueur record pour Paul Biya en Suisse • FRANCE 24 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Infanticides : les mécanismes d'un drame | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · L'auteure-compositrice-interprète Yoa : "On ne demande pas aux hommes s'ils sont misogynes" | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Le dîner des correspondants | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Le plan de Poutine pour fabriquer des armes vient d’être révélé | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Poutine s'énerve | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Quels peuvent être les effets des pesticides sur la santé ? | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Trump : la polémique ICE rebondit | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-29 · Zinédine Zidane est "une incarnation parfaite de ce que doit représenter l'équipe de France", affirm | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-31 · Climat : "On va dépasser les 1,5°C", "la question est de savoir de combien", affirme Robert Vautard | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-07-31 · Des zones d'ombre persistent après l'explosion de la distillerie Montebello en Guadeloupe | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-01 · Ceuta : que révèlent ces images d'arrivées massives de jeunes partant depuis le Maroc ? | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-01 · Darmon, Bruel interdits de scène : la victoire des féministes ? | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-01 · Forêts en feu, multiples canicules : un été français compliqué | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-01 · Les politiques vont-ils enfin écouter le GIEC ? | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-01 · L’IA vient encore d’échapper à ses créateurs, explications | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-01 · Mali, les indépendantistes du FLA diffuse une vidéo de plus de 200 militaires capturés • FRANCE 24 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-02 · Ces Américains qui en ont assez de Donald Trump | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-02 · Pourquoi certains États veulent quitter la Cour Pénale internationale • FRANCE 24 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-02 · Pourquoi le Mali, le Burkina Faso, le Niger et le Tchad quittent-ils la Cour pénale internationale ? | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-04 · RD Congo : le plus grand centre de traitement contre Ebola du pays en construction à Bunia | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-04 · Soudan : 45 combattants ont déserté les rangs des FSR avec leurs armes lourdes • FRANCE 24 | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-04 · Trump dans un scandale, il vient de dévoiler son nouveau business | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-05 · Ebola : le directeur général de l'OMS en visite en RDC • FRANCE 24 | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-05 · Incendie en Gironde : notre journaliste raconte ce feu immense | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::2026-08-05 · La guerre vient de franchir un cap : l’Arabie Saoudite rejoint Trump et frappe | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::Fluency Expressions | 2,640 | 2,640 | 2,640 | 2,640 | 0 | 0 | 0 | M40 |
| ↳ ↳ Idiomatic::French::Idioms | 440 | 440 | 440 | 440 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::French::Idioms Audio (EN → target) | 440 | 803 | 440 | 803 | 0 | 0 | 0 | M41 |
| ↳ ↳ Idiomatic::French::Idioms Audio (target → EN) | 440 | 862 | 440 | 862 | 0 | 0 | 0 | M42 |
| ↳ Idiomatic::German | 0 | 0 | 5,940 | 6,814 | 0 | 1 | 1 | — |
| ↳ ↳ Idiomatic::German::2026-07-11 · Fußfessel für Marine Le Pen: Was das Urteil bedeutet | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · Kahlschlag bei VW? So könnte es weitergehen | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · Sachsen-Anhalt: AfD stellt vor Landtagswahl 100-Tage-Programm vor | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · Spargesetz statt Reform: Das ändert sich jetzt im Gesundheitssystem | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · tagesschau 20:00 Uhr, 14.06.2026 | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · tagesschau in Einfacher Sprache 19:00 Uhr, 10.07.2026 | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · Trump greift Iran an – und zeigt der Nato seine Verachtung | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-11 · US-Börsenexperte Koch: „Die Aktien von Meta ziehen weiter an“ | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · ARD-Sommerinterview: Linken-Chefin Schwerdtner im Faktencheck | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · Fünf Jahre Ahrtalflut: Daran hakt der Wiederaufbau | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · heute 19 Uhr vom 12.07.2026 Steinmeier im ZDF-Sommerinterview, Iran-Eskalation, Klimaanlagen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · heute journal vom 10.07.2026 Umstrittene Gesundheitsreform, Waldbrand in Südspanien | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · heute journal vom 11.07.2026 Waldbrände in Spanien, AfD-Landesparteitag, Norwegen im WM-Fieber | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · Livestream: Wie verkauft der Kanzler seine Reformen dem Parlament? \| DER SPIEGEL | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-12 · Pharma, Apotheken, Krankenhäuser: wie mächtig ist die Gesundheitslobby? \| PolitiX | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-13 · Irankrieg: Weltmacht in der Falle / BASF: Rekordbewertung für Agrarsparte | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-13 · So gefährlich ist die AfD in Sachsen-Anhalt | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-13 · tagesschau in Einfacher Sprache 19:00 Uhr, 13.07.2026 | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-13 · US-Börsenexperte Koch: Apple reicht Klage gegen OpenAI | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-13 · Wie Online-Wetten Leben zerstören: Südafrikas Glücksspielkrise | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · Deutsch-französisches Verhältnis: Außen Einigkeit, innen Krise | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · Fünf Jahre nach der Flut hat sich im Ahrtal viel getan | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · heute journal vom 14.07.2026 Ahrtal-Flut, Iran-Krieg, Straße von Hormus | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · Kürzerer Unterhaltsvorschuss? / Klimaanlagen-Tipps / Neue Fluggastrechte \| "15 Minuten" | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · Rassismus gegen Frankreichs Elf bei der WM: So groß ist das Problem im Fußball \| ZDFheute live | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · tagesschau in Einfacher Sprache 19:00 Uhr, 14.07.2026 | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · Ukraine: Koalition der Unwilligen / Nahost: Eine Alternative zu Hormus | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-14 · US-Börsenexperte Koch: IBM erlebt größten Kurseinbruch in fast 40 Jahren | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-15 · Krise: Müssen Auto-Arbeiter auf ihre Privilegien verzichten? | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-18 · Italiens Erntehelfer: Mordfall enthüllt System aus Ausbeutung und Angst \| Fokus Europa | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-18 · Was Hitze wirklich kostet | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-19 · heute 19:00 Uhr vom 19.07.2026 Merz im Sommerinterview, Iran-Konflikt, WM-Finale | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-19 · Von der Fußball-WM bleibt ein Generalverdacht | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-19 · Warum es viele junge Türken ins Ausland zieht \| DW Reporter | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-20 · Bei Spahn fehlte dem Kanzler das Gespür für seine Partei | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-20 · US-Börsenexperte Koch: Vorsichtige Erholung bei den Chip-Werten | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-21 · Debatte um Leihmutterschaft: Brosius-Gersdorf fordert Legalisierung | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-21 · Trump hat im Iran-Krieg zwei Optionen – beide sind schlecht | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-22 · Zehn Jahre nach dem Anschlag von München · Streit über Leihmutterschaft · Louvre-Galerie öffnet w... | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-28 · Brände in Spanien: Es ist noch nicht vorbei | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-28 · Loyalität oder Kalkül? Warum Söder jetzt dem Kanzler den Rücken stärkt \| PolitiX | 2 | 2 | 2 | 2 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-28 · tagesschau in Einfacher Sprache 19:00 Uhr, 28.07.2026 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Immobilien-Irrsinn: Leerstand ohne Ende in Leipzig \| SPIEGEL TV | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Iran und Saudi-Arabien kämpfen um die Vormacht im Nahen Osten | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Militärmanöver der „Koalition der Willigen“ • Social-Media-Verbot • Günther Jauch wird 70 | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Stimmungstest für Friedrich Merz / Wie zwei Kriege zu einem strategischen Problem werden | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Stimmungstest für Merz · Fed entscheidet über Leitzins · Neuer Spider-Man im Kino | 2 | 2 | 2 | 2 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Studium, Nebenjob, Burnout: Warum viele junge Menschen am Limit sind I akkurat | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · tagesschau in Einfacher Sprache 19:00 Uhr, 29.07.2026 | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · US-Börsenexperte Koch: Zurückhaltung vor der Fed-Sitzung | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Weg von Donald Trump: US-Amerikaner wagen den Neuanfang in Europa \| auslandsjournal | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-29 · Wer folgt auf Jens Spahn? • Spanien ist Weltmeister • Iran-Konflikt spitzt sich zu | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-30 · Märkte reagieren nach Fed-Entscheidung nervös / Microsoft wächst, Meta verschreckt | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-31 · Apple: Starke Zahlen, schwacher Ausblick / Rheinenergie schluckt EnBW-Sparte | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-31 · ARD-Brennpunkt zur Lage in Ceuta: Ansturm Hunderttausender Migranten | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-31 · Boykott der Fußball-WM? / Recht auf Reparatur von Elektrogeräten / Sitzbänke im Wald \| "15 Minuten" | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-31 · Israel und die US-Demokraten: Eine Partei in der Identitätskrise | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-31 · Rhein vor Rekordtief · Anspruch auf Ganztagsbetreuung · Streit um KI-Musik | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-07-31 · tagesschau in Einfacher Sprache 19:00 Uhr, 31.07.2026 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-01 · heute journal vom 01.08.2026 CSD in Hamburg, Waldbrände in Südeuropa, Migranten zurück in Marokko | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-01 · Migranten verlassen Ceuta und kehren nach Marokko zurück | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-01 · Nach Ansturm auf Ceuta: Migranten kehren zurück, Europa diskutiert | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-01 · Warum in Italien Demonstrierende unter Druck geraten  \| Fokus Europa | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-02 · heute 19:00 Uhr vom 02.08.2026 KI-Kennzeichnungspflicht, Rente, deutsche Feuerwehr hilft in Spanien | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-02 · So lief die Krise in Ceuta ab – Eindrücke von vor Ort | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-03 · Ceuta: Migrationskrise oder hybrider Angriff? / Börsen zwischen Angst und Euphorie | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-03 · Migranten in Ceuta / Azubi-Wohnheime gegen hohe Mieten / Ärger mit Park-Angeboten an Flughäfen | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-04 · CSD-Attentat: „Unbequeme Fragen“ im Bundestags-Innenausschuss – ARD-Korrespondent aus Berlin | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-04 · Das Geschäft mit rassistischen Erotik-Videos \| rabbit hole | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-04 · US-Börsenexperte Koch: „Die Rally geht ungebrochen weiter“ | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-05 · Russland vor der Duma-Wahl: Hat die Opposition eine Chance? | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-05 · tagesschau in Einfacher Sprache 19:00 Uhr, 05.08.2026 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::2026-08-05 · Wie die Ukraine Russland in der Todeszone angreift | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::Fluency Expressions | 3,642 | 3,642 | 3,642 | 3,642 | 0 | 1 | 1 | M40 |
| ↳ ↳ Idiomatic::German::Idioms | 607 | 607 | 607 | 607 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::German::Idioms Audio (EN → target) | 607 | 1,044 | 607 | 1,044 | 0 | 0 | 0 | M41 |
| ↳ ↳ Idiomatic::German::Idioms Audio (target → EN) | 607 | 1,044 | 607 | 1,044 | 0 | 0 | 0 | M42 |
| ↳ Idiomatic::it | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ Idiomatic::Italian | 0 | 0 | 8,079 | 9,551 | 84 | 1,343 | 1,343 | — |
| ↳ ↳ Idiomatic::Italian::2026-07-11 · Caracciolo a Mappa Mundi: Vogliamo la guerra totale? / Prima parte | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-11 · Gerusalemme, città involucro - di Laura Canali | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-11 · Vaccinare invertebrati | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · (1/3) Carlo Galli - Il discorso della tecnica: storia, filosofia, politica | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Caldo e RITARDI RECORD, come cambiano i treni per resistere alle estati a 55 gradi \| The Essential | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli - Democrazia ultimo atto? Crisi del Neoliberismo | 23 | 23 | 23 | 23 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli - La fine della globalizzazione? | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli - Quale necessità della politica? A partire da Platone | 2 | 2 | 2 | 2 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · CARLO GALLI - «Che cos'è l'ideologia?» | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli \| Fare politica con le parole | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli \| Il nomos della terra di Carl Schmitt | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli \| Il principe di Niccolò Machiavelli | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli \| Leviatano di Thomas Hobbes | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Galli, Antonio Gnoli: Machiavelli e la filosofia politica | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg - Il vincolo della vergogna | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg - La lettera uccide | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg - Rivelazioni involontarie. Leggere la storia | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg e Adriano Prosperi - Sulla riedizione di Giochi di pazienza | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg e il mestiere di storico | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg e il metodo storico | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg, I benandanti, cinquant'anni dopo | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Carlo Ginzburg. Dialogo su Cesare Pavese | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · CHAT CONTROL torna al Parlamento UE: a rischio la PRIVACY dei messaggi \| The Essential | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Diagnosi di una crisi politica. Dialogo con Carlo Galli | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Discorsi sul metodo con Carlo Ginzburg | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · History Lab incontra... CARLO GINZBURG | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Il Parlamento Ue indaga sui SOVRANISTI, Le Pen CANDIDATA nonostante la condanna \| The Essential | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Il premio Balzan per Carlo Ginzburg, intervista | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Il soggetto fra letteratura e politica. Su Romanticismo politico | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Incontro con Carlo Ginzburg, Miti emblemi spie | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Intervento del prof. Carlo Ginzburg | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Intervista a Carlo Galli \| festivalfilosofia 2012 | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · L'ODISSEA di Christopher Nolan e le polemiche su Lupita Nyong'o come nuova Elena \| The Essential | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Marine Le Pen ESCLUSA dalle prossime elezioni? La decisione e l'ipotesi Bardella \| The Essential | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · POSTDEMOCRAZIA ARMATA: ultimo atto dell'Oligarchia? Intervista a Carlo Galli | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Putin minaccia la POLONIA: sale la tensione tra Russia e NATO \| The Essential | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-12 · Tradurre l'ambiguità. Appunti sulla ricezione di Genesi 3,22 | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-13 · Ep.905 - La lingua di chi ascolta | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-13 · Hormuz senza tregua | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-13 · Perché è ricominciata la guerra tra Stati Uniti e Iran? | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-13 · Riarmo Germania: dall'auto ai cannoni. Le ripercussioni per l'Europa e l'Italia | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-14 · L'avanzata dei socialisti. La battaglia tra i democratici per le elezioni di midterm negli Usa | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-14 · L’incredibile alleanza tra il Mossad e Ahmadinejad | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-14 · Quanto guadagnerebbero gli Stati Uniti dai pedaggi nello stretto di Hormuz | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-15 · Il bidone della spazzatura che può sconfiggere Farage | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-16 · Un confine per Israele - di Lucio Caracciolo | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-20 · Ep.910 - LMDelVecchio. Il cane e la lepre | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-20 · Scontri tra polizia e manifestanti a Bologna al presidio per morte di Fakir: bombe carta e idranti | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-20 · Trump è sotto la grandinata iraniana e non ha ripari | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-22 · Cosa è successo davvero a Bologna: le piazze e la strumentalizzazione politica | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-23 · Il cortocircuito di Hormuz - di Fabrizio Maronta | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-28 · Panama Project | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-28 · Perché il governo ha tagliato le accise sul gasolio e non sulla benzina | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Corno d'Africa e nuove alleanze in Medio Oriente. Mar rosso e Stretto di Hormuz. Israele vs Turchia | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Cos’è Super El Niño e cosa dobbiamo aspettarci nel 2027, tra ondate di caldo e instabilità climatica | 2 | 2 | 2 | 2 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Dalle mascherine cinesi all'audizione di Conte, su cosa si è acceso lo scontro in Commissione Covid | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Ep.72: Spendere meno per spendere meglio | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Ep.73: La storia dell'alta velocità in Cina | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Fibromialgia, malattia invisibile inserita nei Lea solo se grave: "Dolore non è nella nostra testa" | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Guerra Iran-USA: a che punto è il conflitto dopo gli ultimi attacchi \| The Essential | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · I dubbi dell’intelligence USA sul piano iraniano per fare fuori  Donald Trump | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Il PENTAGONO vuole misurare il TESTOSTERONE di tutti i soldati \| The Essential | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Il video AI di Vannacci nell’antica Roma: cos’è la slopaganda | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Legge elettorale, maggioranza battuta sulle preferenze. Crisi per il governo Meloni? \| The Essential | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Lo Spazio è il nuovo fronte del riarmo tedesco. La competizione con la Francia e il ruolo degli Usa | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Lo “scudo” per gli agenti, l’indagine dell’Ausl: cosa sappiamo della morte di Abderrahim Fakir | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Muore durante un fermo della polizia a Bologna, il caso di Abderrahim Fakir \| The Essential | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Quanto è probabile una crisi di governo dopo il caos sulle preferenze? | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Turchia nuova potenza del Mediterraneo. La strategia degli Stretti e il rapporto con l'Italia | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Ucraina, l'Europa prepara uno scudo antimissile comune \| The Essential | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-07-29 · Vannacci GLADIATORE con l'AI contro la sinistra: è la nuova propaganda politica? \| The Essential | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-01 · Milei potrà ESPELLERE chi diffonde messaggi d'ODIO sull'Argentina \| The Essential | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-03 · Crisi di Ceuta e l'UE: quali responsabilità per Spagna e Marocco? \| The Essential | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-04 · I viaggi di Brunori Sas, parte 2 | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-04 · Tutti i problemi degli hub per migranti che l’Europa vuole costruire in Africa | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-05 · Cosa è successo tra Schlein e Conte: i progressisti alla prova dell'unità sulle spese militari | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-05 · I viaggi di Brunori Sas, parte 3 | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-05 · Naziskin assediano l’hotel di un gruppo di adolescenti ebrei italiani a Sofia \| The Essential | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-06 · Chi è ABDUL EL-SAYED, il “nuovo Mamdani” che ha vinto le primarie Dem in Michigan \| The Essential | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-06 · Gli Stati Uniti stanno davvero finendo missili e munizioni per la guerra in Iran? | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-06 · I viaggi di Brunori Sas, parte 4 | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-07 · Crans-Montana, perché la Svizzera ha ESCLUSO l’Italia dal processo sulla strage \| The Essential | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::2026-08-07 · Ep.920 - Francesco Guccini | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::Fluency Expressions | 4,890 | 4,890 | 4,890 | 4,890 | 84 | 1,241 | 1,241 | M40 |
| ↳ ↳ Idiomatic::Italian::Idioms | 815 | 815 | 815 | 815 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Italian::Idioms Audio (EN → target) | 815 | 1,477 | 815 | 1,477 | 0 | 0 | 0 | M41 |
| ↳ ↳ Idiomatic::Italian::Idioms Audio (target → EN) | 815 | 1,625 | 815 | 1,625 | 0 | 102 | 102 | M42 |
| ↳ Idiomatic::Portuguese | 0 | 0 | 5,188 | 6,163 | 6 | 310 | 310 | — |
| ↳ ↳ Idiomatic::Portuguese::2026-07-11 · 'Solos têm que ser causa nacional': o balanço de quem participou da Escola de Bioinsumos na China | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-11 · Hamas dissolve governo em Gaza após 20 anos e transfere poder a comitê técnico da ONU | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-11 · Inteligência artificial e o futuro do trabalho \| Aaron Benanav | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-11 · Privatizações de Tarcísio podem provocar a criação de 'milícias', diz Haddad \| Entrevista | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · BRASIL ELIMINADO, INTIMIDADE DE BOLSONARO EXPOSTA E NINGUÉM AGUENTA O FLÁVIO \| RESUMÃO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · Cessar-fogo ou anexação? Israel já controla 70% de Gaza e avança sem parar | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · Cessar-fogo, governança e acesso: as condições básicas para o futuro de Gaza | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · ENTENDA COMO A APENDICITE LEVOU BONNIE TYLER \| ABDUÇÃO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · MAÍRA CARDI TOMA MEDIDA DRÁSTICA COM REFRIGERANTE DO MARIDO E ATITUDE DELE CHOCA INTERNET \| PLANTÃO | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · MICHELLE CRIA NOVA ESTRATÉGIA POLÍTICA INDEPENDENTE DO PARTIDO DO JAIR \| PLANTÃO | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · PAI É PRESO APÓS CONFESSAR QUE CHUTOU FILHA DE 3 ANOS PORQUE ELA ESTAVA CHORANDO  \| PLANTÃO | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-12 · VALDEMAR É SUSPEITO DE INDICAÇÃO IRREGULAR DE EMENDAS  \| PLANTÃO | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-15 · CABO DACIOLO DEFENDE CONSPIRAÇÃO BIZARRA CONTRA O LULA \| PLANTÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-24 · O casarão que ninguém via no Centro de São Paulo \| Reportagem | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-24 · O descumprimento dos EUA que agrava a guerra contra o Irã - Rodamundo | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · A "internet socialista" de Allende que a CIA ajudou a destruir, com Cian Barbosa | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · ANÁLISE EM ESQUELETO SUGERE QUE PRINCESAS EGÍPCIAS ERAM GRANDES GUERREIRAS \| ABDUÇÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · Argentina na Copa reabriu a discussão sobre arbitragem e política - Breno Altman | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · CASO PIETRA BERTOLOZZI E BTS CHEGA À COREIA DO SUL E METEORO BRASIL É CITADO \| FORA DE ÓRBITA | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · CASOS DE CÂNCER PODEM QUASE DOBRAR ATÉ 2050, ALERTA OMS \| ABDUÇÃO | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · CIENTISTA HOMENAGEIA GOLEIRO DE CABO VERDE COM NOME DE MOLUSCO \| ABDUÇÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · CONVERSANDO COM DANIELA LIMA, JANJA PRESTA SOLIDARIEDADE A MICHELLE BOLSONARO \| PLANTÃO | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · Cuba espera por mudanças profundas: Frei Betto sobre os desafios da nova economia | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · DELEGADA REVELA DETALHE PERTURBADOR SOBRE CASO DO “MANÍACO DO CONDOMÍNIO” \| PLANTÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · DEMISSÕES NO ICL, CARTA DE BOLSONARO VIRA TIRO NO PÉ E FOTO COMPROMETEDORA PARA FLÁVIO VEM À TONA | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · ERIKA HILTON ACUSA SBT DE MENTIR PARA JUIZ EM PROCESSO ENVOLVENDO O RATINHO \| PLANTÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · ESCÂNDALO LIGADO A PRIMO DE VORCARO, O DO CARRINHO DE GOLFE, PREJUDICOU 160 FAMÍLIAS | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · EXÉRCITO DOS EUA ADOTA PSEUDOCIÊNCIA DOS REDPILL \| ABDUÇÃO | 2 | 2 | 2 | 2 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · Frei Betto denuncia "bloqueio genocida" dos EUA: Cuba há 5 meses sem petróleo | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · FRUSTRAÇÃO NO FUTEBOL VIRA VIOLÊNCIA CONTRA MULHERES \| ABDUÇÃO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · HOUVE UMA CAMPANHA DE DESINFORMAÇÃO NO ESCÂNDALO LIGADO A PRIMO DE VORCARO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · IDOSA SOFRE COM EFEITO COLATERAL DO OZEMPIK E É SALVA PELA COCA-COLA \| ABDUÇÃO | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · JOSÉ GERALDO EXPLICA MIGUEL REALE E O DIREITO USADO POR BOLSONARO E GOLPISTAS | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · KAKAY DEFENDE MEDIDA DRÁSTICA CONTRA BOLSONARO APÓS CARTINHA: "PAPUDA NELE!" \| PLANTÃO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · LEANDRO DEMORI É DESLIGADO DO ICL NOTÍCIAS \| PLANTÃO | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · MILEI SE ENCRENCA NA ARGENTINA POR APOIO A FLÁVIO BOLSONARO \| PLANTÃO | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · O COMPLICADO CASO DA 4RMA DE BOLSONARO, SEGUNDO SERRANO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · O PIX cai na conta da prefeitura e você nem vê -  Amanda Miranda. | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · O segredo por trás da aliança da FIFA com os bilionários do futebol - Breno Altman | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · OS DIREITOS ESTÃO EM RISCO, ALERTA SERRANO | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · PASTOR REVELA SEGREDO DE FIEL NO PÚLPITO E ACABA CONDENADO \| FORA DE ÓRBITA | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · PORQUE OS TUBARÕES ESTÃO CHEIOS DE DROGAS \| ABDUÇÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · Povo iraniano exige vingança contra EUA após funeral de Khamenei: o que vem agora? | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · PRINT DE ZAP DE ASSESSOR DE MICHELLE CAUSA GUERRA NO BOLSONARISMO \| PLANTÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-29 · Tom Altman testemunhou o clamor por vingança no Irã | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-31 · JULIANO FLOSS APARECE DE CUECA DE RENDA E ATINGE A MACHOSFERA EM CHEIO \| FORA DE ÓRBITA | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-07-31 · MENDONÇA AUTORIZA NOVA INVESTIGAÇÃO CONTRA LULINHA, APÓS CASO DO INSS NÃO DAR EM NADA \| PLANTÃO | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-01 · Da clandestinidade à luz do sol: a emoção do reencontro após a anistia de 1979 - Ladislau Dowbor | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-01 · MILEI E BOLSONARO NA CONVENÇÃO DO PL; FIGUEIREDO ATACA JORNALISTAS E TORNADO NO RS \| RESUMÃO | 2 | 2 | 2 | 2 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-01 · PESQUISADORES ANUNCIAM DOIS CASOS DE CURA DA AIDS; CURA VAI CHEGAR PARA A POPULAÇÃO? \| ABDUÇÃO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-01 · POLÍCIA PRENDE HOMEM INOCENTE POR CONFUNDIR NOME EM SKYRIM \| PLANTÃO | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-02 · EMPRESAS DE IA SÃO ACUSADAS DE DESTRUIR MILHÕES DE LIVROS RAROS PARA TREINAR IAS \| ABDUÇÃO | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-03 · JOSÉ GERALDO DIZ QUE A EXTREMA DIREITA DECIDIU ATACAR A PÉRSIA | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-03 · O mito que a história revelou: o relacionamento conturbado entre Israel e o Hamas - Os Altmans | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-04 · COMO FOI A PALESTRA DO METEORO E DO DROPS DE JOGOS EM SALVADOR? \| PLANTÃO | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-04 · PODCAST MAROMBA E CRENTE TEM TRETA GENERALIZADA COM KOGOS E BILYNSKYJ \| PLANTÃO | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-05 · AGÊNCIA PÚBLICA RESPONDE INQUÉRITO POLICIAL POR ACUSAÇÃO DE R4C1SMO REVERSO  \| PLANTÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-05 · JOSÉ GERALDO DIZ COMO O SOCIAL, INDÍGENAS E DIVERSIDADE ESTÃO REVOLUCIONANDO O DIREITO | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-05 · LULA QUER ACABAR COM O TETO DE GASTOS | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-05 · MICHELLE BOLSONARO USA ATESTADO PARA FICAR LONGE DE FLÁVIO BOLSONARO \| FORA DE ÓRBITA | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-06 · ENTENDA A PEGADINHA POR TRÁS DA CRÍTICA DE MALAFAIA A VICE DE FLÁVIO \| PLANTÃO | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::2026-08-07 · LULA 3XPLODE E REPERCUTE COM ENTREVISTA AO METEORO BRASIL \| PLANTÃO | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::Fluency Expressions | 3,186 | 3,186 | 3,186 | 3,186 | 6 | 310 | 310 | M40 |
| ↳ ↳ Idiomatic::Portuguese::Idioms | 535 | 535 | 535 | 535 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Portuguese::Idioms Audio (EN → target) | 532 | 988 | 532 | 988 | 0 | 0 | 0 | M41 |
| ↳ ↳ Idiomatic::Portuguese::Idioms Audio (target → EN) | 532 | 1,051 | 532 | 1,051 | 0 | 0 | 0 | M42 |
| ↳ Idiomatic::Spanish | 0 | 0 | 4,489 | 5,386 | 0 | 1 | 1 | — |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · ADA FERRER, historiadora cubana: "La gente suele hablar de cuba en lemas" \| EL PAÍS | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · Cuba: cinco años después del 11J, persisten la crisis y el exilio | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · DIRECTO SAN FERMÍN 2026 \| Quinto encierro de los Sanfermines 2026 con Escolar Gil \| EL PAÍS | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · Por qué hay temor de una guerra civil en Líbano tras el acuerdo de paz | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · Por qué la IA está empujando a muchas personas a emprender e invertir | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · 🔴 DIRECTO SAN FERMÍN \| Quinto encierro de los Sanfermines 2026 hoy 11 de julio | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-11 · 🟢 Apple demanda a OpenAI por robo de secretos comerciales | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-12 · Las noticias del DOMINGO 12 de JULIO en 10 minutos \| RTVE Noticias | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-12 · Las noticias del SÁBADO 11 de JULIO en 10 minutos \| RTVE Noticias | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-12 · Por qué Estados Unidos necesita a Corea del Sur para hacer frente a la gigantesca armada china | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-12 · 📡 SUSANA ACOSTA, COORDINADORA CIC  - QUIRÓFANO MÓVIL DURANTE TODO EL MES DE JULIO EN EL CIC ROTARY | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-12 · 🔴DW Noticias 11 de julio: Inicia censo biométrico en Venezuela | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-12 · 🟢 Las principales noticias económicas de la semana | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-13 · Cómo la adicción al juego online destruye vidas en Sudáfrica \| El Reportero | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-13 · Las noticias del LUNES 13 de JULIO en 10 minutos \| RTVE Noticias | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-13 · 🔴 DW Noticias 12 de julio: Irán vuelve a anunciar cierre del estrecho de Ormuz | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-14 · Venezuela promete entregar viviendas a damnificados por los terremotos | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-14 · Volkswagen necesita recortar 50.000 empleos más | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-14 · ¿Sabías que hacen falta animales para fabricar tests de embarazo? Una startup busca cambiarlo | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-14 · 🟢 La tensión en Ormuz dispara el crudo casi un 10 % | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-18 · Por qué todo el mundo habla de La Odisea | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-18 · 🟢 La otra final del Mundial: turismo, consumo y un negocio multimillonario | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-18 · 🟢 Las principales noticias económicas de la semana | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-19 · Las noticias del DOMINGO 19 de JULIO en 10 minutos \| RTVE Noticias | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-19 · 🔴 DW Noticias 18 de julio: Teherán amenaza con una "ofensiva total" | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-20 · Las noticias del lunes 20 de julio en 10 minutos \| RTVE Noticias | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-20 · 🔴DW Noticias 19 de julio: La Roja vence a la Albiceleste en una final de infarto | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-21 · Última Hora de los incendios \| 4 comunidades autónomas afectadas por las llamas \| RTVE Noticias | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-21 · 🟢Alemania vende menos autos a China | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-22 · Por qué el estrecho de Malaca, la puerta de Asia por mar, puede asfixiar la economía de China | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-22 · Un hombre asesina a su exmujer en su vivienda de Málaga \| RTVE Noticias | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-28 · Incendios \| Marlaska dice que el fuego ha dejado de avanzar \| Los vecinos vuelven a sus casas \|RTVE | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-28 · Las noticias del martes 28 de julio en 10 minutos \| RTVE Noticias | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · Arkano, el adolescente que descubrió su identidad gracias al rap \| Pensemos el mañana (episodio 2) | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · Dentro del incendio letal de Los Gallardos | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · Dentro del mayor incendio de la historia de España | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · ENTREVISTA con la gobernadora Marina del Pilar Ávila \| EL PAÍS | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · España reina en el mundo | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · Incendios \| Miles de evacuados regresan a sus hogares en 15 municipios de Madrid y Ávila \| RTVE | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · Incendios \| Se reaviva el fuego de La Vall d'Uixò (Castellón) con varios rebrotes \| RTVE Noticias | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · Pedro Sánchez visita el puesto de mando de Navalcarnero \| RTVE Noticias | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · ☎️ JORGE “LOCOMOTORA” CASTRO - CONFLICTO FAMILIAR POR LA VENTA DE UNA VIVIENDA EN CALETA OLIVIA | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · 📡 MG. CLAUDIO FERNANDEZ, DECANO UNPA-UACO - TRABAJO EN CONJUNTO ENTRE UNIVERSIDAD Y MUNICIPIO. | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · 📡 MÓVIL CON FELIPE GOGOL - ACAMPE EN EL PREDIO DE LA UNIDAD REGIONAL ZONA NORTE DE CALETA OLIVIA | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · 🔴 DIRECTO \| Juanma Moreno comparece ante los medios desde Los Gallardos | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-29 · 🟢Keiko Fujimori enfrenta el reto de fortalecer la economía y reducir la informalidad en Perú | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-30 · Cuarta ola de calor: por qué, hasta cuándo y cómo afecta a los incendios | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · Crisis migratoria en Ceuta \| Italia suspende el acuerdo de libre circulación Schengen con España | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · Crisis migratoria en Ceuta \| ¿Qué explicación política hay detrás del suceso? \| RTVE Noticias | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · Del opio al fentanilo: ¿seguimos cayendo en la misma mentira? | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · La crisis migratoria deja 19 muertos en Ceuta mientras continúan las entradas por el Tarajal \| RTVE | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · Las noticias del  viernes  31 de julio en 10 minutos \| RTVE Noticias | 3 | 3 | 3 | 3 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · ¿Nos molestan los niños? El auge del 'adults only' | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-07-31 · 📡 MÓVIL CON MAURICIO VENEGAS, ATRAVIESA UNA DIFÍCIL SITUACIÓN TRAS LA AMPUTACIÓN DE SU PIE IZQUIERDO | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-01 · Las noticias del sábado 1 de agosto en 10 minutos \| RTVE Noticias | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-01 · 🟢 El coste económico de volver a levantar fronteras en Europa | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-01 · 🟢 Las principales noticias económicas de la semana | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-02 · Las noticias del domingo 2 de agosto en 10 minutos \| RTVE Noticias | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-03 · 🔴 DW Noticias 2 de agosto:  Al menos 5 muertos tras atentado con bomba en un restaurante de Moscú | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-04 · Crisis migratoria en Ceuta \| ¿Qué requisitos se necesitan para ser asilado? \| RTVE Noticias | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-04 · Las noticias del martes 4 de agosto en 10 minutos \| RTVE Noticias | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-05 · Las noticias del miércoles 5 de agosto en 10 minutos \| RTVE Noticias | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-05 · ☎️ JULIO BUJER, AGVP - INTENSIFICAN DESPEJE DE NIEVE PARA GARANTIZAR LA TRANSITABILIDAD DE LAS RUTAS | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-05 · 🟢Récord de trabajadores en España | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::2026-08-06 · 🟢Siemens anuncia récord de ventas y beneficios | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::Fluency Expressions | 2,712 | 2,712 | 2,712 | 2,712 | 0 | 1 | 1 | M40 |
| ↳ ↳ Idiomatic::Spanish::Idioms | 452 | 452 | 452 | 452 | 0 | 0 | 0 | M05 |
| ↳ ↳ Idiomatic::Spanish::Idioms Audio (EN → target) | 452 | 890 | 452 | 890 | 0 | 0 | 0 | M41 |
| ↳ ↳ Idiomatic::Spanish::Idioms Audio (target → EN) | 452 | 911 | 452 | 911 | 0 | 0 | 0 | M42 |
| ↳ Idiomatic::z-archive | 0 | 0 | 236 | 236 | 0 | 18 | 18 | — |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Der deutsche Außenminister Johann Wadephul wirbt für europäische Einheit | 12 | 12 | 12 | 12 | 0 | 8 | 8 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::EU berät über China-Kurs · Iran-Gespräche in der Schweiz · Deutschland trifft auf Elfenbeinküste | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M05 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::EU-Asylregeln: Was sich in Deutschland ändert | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Haben im Bosnienkrieg auch ausländische Kriegstouristen Zivilisten getötet? | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Hat Trump den Iran-Krieg verloren? \| Stabile Zeitenlage | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Iran und USA: Bringt Trump den Frieden mit zum G-7-Gipfel? | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Iran: Gefährdet Netanjahu Trumps Frieden? | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Rassistische Gewalt in Belfast: Woher kommt die Wut? | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::Space-X: Was macht Elon Musk mit seiner Billion? | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::tagesschau in Einfacher Sprache 19:00 Uhr, 18.06.2026 | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::de::WM: America first, Fußball second? | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::fr::En 20 ans, il a arnaqué des dizaines de femmes : enquête sur Frédérick Q | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::fr::GUERRE DE L’IA : Trump impose ses règles à Anthropic | 9 | 9 | 9 | 9 | 0 | 3 | 3 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::fr::Masculinistes incels : une nouvelle menace terroriste | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::fr::THÉORIE DE LA SIMULATION : pourquoi la Silicon Valley croit que notre monde est virtuel | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::it::Ep.889 - Cara Roxane, avevi ragione tu | 9 | 9 | 9 | 9 | 0 | 5 | 5 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::it::L&#39;era degli imperi \| The market dispatch | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ Idiomatic::z-archive::pt | 0 | 0 | 54 | 54 | 0 | 2 | 2 | — |
| ↳ ↳ ↳ Idiomatic::z-archive::pt::A Revolução dos Trabalhadores nas Páginas dos Gibis de Laerte | 9 | 9 | 9 | 9 | 0 | 2 | 2 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::pt::Breno Altman analisa: Como seria a queda dos EUA e o que aconteceria com o mundo | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M05 |
| ↳ ↳ ↳ Idiomatic::z-archive::pt::Breno Altman: o tiro no pé de Flávio Bolsonaro em Washington | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M05 |
| ↳ ↳ ↳ Idiomatic::z-archive::pt::Glauber Braga revela os bastidores da luta contra o orçamento secreto | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M04 |
| ↳ ↳ ↳ Idiomatic::z-archive::pt::Laerte abre o jogo sobre os desafios de ser artista no Brasil atual | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M04 |
| Idiomatic Exercises DE | 0 | 0 | 342 | 684 | 0 | 0 | 0 | — |
| ↳ Idiomatic Exercises DE::Konditionalsätze | 163 | 326 | 163 | 326 | 0 | 0 | 0 | M06 |
| ↳ Idiomatic Exercises DE::Konnektoren | 179 | 358 | 179 | 358 | 0 | 0 | 0 | M06 |
| Idiomatic Exercises ES | 0 | 0 | 375 | 750 | 0 | 6 | 6 | — |
| ↳ Idiomatic Exercises ES::Condicionales | 168 | 336 | 168 | 336 | 0 | 0 | 0 | M06 |
| ↳ Idiomatic Exercises ES::Conectores | 207 | 414 | 207 | 414 | 0 | 6 | 6 | M06 |
| Idiomatic Exercises FR | 0 | 0 | 353 | 706 | 0 | 1 | 1 | — |
| ↳ Idiomatic Exercises FR::Conditionnels | 162 | 324 | 162 | 324 | 0 | 0 | 0 | M06 |
| ↳ Idiomatic Exercises FR::Connecteurs | 191 | 382 | 191 | 382 | 0 | 1 | 1 | M06 |
| Idiomatic Exercises IT | 0 | 0 | 367 | 734 | 0 | 0 | 0 | — |
| ↳ Idiomatic Exercises IT::Connettivi | 201 | 402 | 201 | 402 | 0 | 0 | 0 | M06 |
| ↳ Idiomatic Exercises IT::Periodo ipotetico | 166 | 332 | 166 | 332 | 0 | 0 | 0 | M06 |
| Idiomatic Exercises PT | 0 | 0 | 335 | 670 | 0 | 0 | 0 | — |
| ↳ Idiomatic Exercises PT::Condicionais | 160 | 320 | 160 | 320 | 0 | 0 | 0 | M06 |
| ↳ Idiomatic Exercises PT::Conectores | 175 | 350 | 175 | 350 | 0 | 0 | 0 | M06 |
| Idiomatic Grammar DE | 0 | 0 | 111 | 111 | 0 | 0 | 0 | — |
| ↳ Idiomatic Grammar DE::0 Hören | 2 | 2 | 12 | 12 | 0 | 0 | 0 | M07 |
| ↳ ↳ Idiomatic Grammar DE::0 Hören::05 Die Fälle | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M08 |
| ↳ ↳ Idiomatic Grammar DE::0 Hören::06 Adjektivendungen | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M08 |
| ↳ Idiomatic Grammar DE::1 Genus | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar DE::2 Präpositionen | 34 | 34 | 34 | 34 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar DE::3 Adjektive | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar DE::4 Verben | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar DE::5 Kasus | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar DE::9 Meine Fehler | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M07 |
| Idiomatic Grammar ES | 0 | 0 | 293 | 293 | 0 | 7 | 7 | — |
| ↳ Idiomatic Grammar ES::0 Escucha | 3 | 3 | 8 | 8 | 0 | 0 | 0 | M07 |
| ↳ ↳ Idiomatic Grammar ES::0 Escucha::01 El subjuntivo | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M08 |
| ↳ Idiomatic Grammar ES::1 Tiempos | 71 | 71 | 71 | 71 | 0 | 6 | 6 | M07 |
| ↳ Idiomatic Grammar ES::10 Interferencias | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::2 Subjuntivo | 23 | 23 | 23 | 23 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::3 Condicionales | 24 | 24 | 24 | 24 | 0 | 1 | 1 | M07 |
| ↳ Idiomatic Grammar ES::4 Imperativo | 45 | 45 | 45 | 45 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::5 Pronombres | 40 | 40 | 40 | 40 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::6 Preposiciones | 24 | 24 | 24 | 24 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::7 Ser/Estar | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::8 Grado y cantidad | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar ES::9 Mis errores | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M07 |
| Idiomatic Grammar FR | 0 | 0 | 195 | 195 | 0 | 128 | 128 | — |
| ↳ Idiomatic Grammar FR::0 Écoute | 4 | 4 | 14 | 14 | 0 | 6 | 6 | M07 |
| ↳ ↳ Idiomatic Grammar FR::0 Écoute::03 Beaucoup de | 5 | 5 | 5 | 5 | 0 | 5 | 5 | M08 |
| ↳ ↳ Idiomatic Grammar FR::0 Écoute::04 Le genre | 5 | 5 | 5 | 5 | 0 | 1 | 1 | M08 |
| ↳ Idiomatic Grammar FR::1 Temps | 58 | 58 | 58 | 58 | 0 | 81 | 81 | M07 |
| ↳ Idiomatic Grammar FR::10 Interférences | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar FR::2 Conditionnel | 11 | 11 | 11 | 11 | 0 | 17 | 17 | M07 |
| ↳ Idiomatic Grammar FR::3 Subjonctif | 20 | 20 | 20 | 20 | 0 | 24 | 24 | M07 |
| ↳ Idiomatic Grammar FR::4 Pronoms | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar FR::5 Prépositions | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar FR::6 Genre & accord | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar FR::7 Articles & quantités | 26 | 26 | 26 | 26 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar FR::9 Mes erreurs | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M07 |
| Idiomatic Grammar IT | 0 | 0 | 166 | 166 | 0 | 113 | 113 | — |
| ↳ Idiomatic Grammar IT::0 Ascolto | 0 | 0 | 10 | 10 | 0 | 0 | 0 | — |
| ↳ ↳ Idiomatic Grammar IT::0 Ascolto::07 Il congiuntivo | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M08 |
| ↳ ↳ Idiomatic Grammar IT::0 Ascolto::08 Plurali bugiardi | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M08 |
| ↳ Idiomatic Grammar IT::1 Tempi | 68 | 68 | 68 | 68 | 0 | 27 | 27 | M07 |
| ↳ Idiomatic Grammar IT::10 Interferenze | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar IT::2 Condizionale | 11 | 11 | 11 | 11 | 0 | 17 | 17 | M07 |
| ↳ Idiomatic Grammar IT::3 Congiuntivo | 18 | 18 | 18 | 18 | 0 | 22 | 22 | M07 |
| ↳ Idiomatic Grammar IT::4 Clitici | 11 | 11 | 11 | 11 | 0 | 14 | 14 | M07 |
| ↳ Idiomatic Grammar IT::5 Genere e plurali | 12 | 12 | 12 | 12 | 0 | 15 | 15 | M07 |
| ↳ Idiomatic Grammar IT::6 Reggenze | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar IT::9 I miei errori | 11 | 11 | 11 | 11 | 0 | 18 | 18 | M07 |
| Idiomatic Grammar PT | 0 | 0 | 170 | 170 | 0 | 0 | 0 | — |
| ↳ Idiomatic Grammar PT::0 Escuta | 3 | 3 | 8 | 8 | 0 | 0 | 0 | M07 |
| ↳ ↳ Idiomatic Grammar PT::0 Escuta::09 Futuro do subjuntivo | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M08 |
| ↳ Idiomatic Grammar PT::1 Tempos | 52 | 52 | 52 | 52 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar PT::10 Interferência | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar PT::2 Condicional | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar PT::3 Subjuntivo | 30 | 30 | 30 | 30 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar PT::4 Clíticos | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar PT::5 Gênero & Artigos | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M07 |
| ↳ Idiomatic Grammar PT::9 Meus erros | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M07 |
| Idiomatic Rescue Comics | 0 | 0 | 10 | 10 | 0 | 28 | 28 | — |
| ↳ Idiomatic Rescue Comics::DE | 2 | 2 | 2 | 2 | 0 | 4 | 4 | M09 |
| ↳ Idiomatic Rescue Comics::ES | 4 | 4 | 4 | 4 | 0 | 14 | 14 | M09 |
| ↳ Idiomatic Rescue Comics::IT | 1 | 1 | 1 | 1 | 0 | 2 | 2 | M09 |
| ↳ Idiomatic Rescue Comics::PT | 3 | 3 | 3 | 3 | 0 | 8 | 8 | M09 |
| Idiomatic Tenses DE | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses DE::liegen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses DE::lügen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses DE::schaffen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| Idiomatic Tenses ES | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses ES::decir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses ES::saber | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses ES::ver | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| Idiomatic Tenses Exercises DE | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses Exercises DE::liegen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises DE::lügen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises DE::schaffen | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| Idiomatic Tenses Exercises ES | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses Exercises ES::decir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises ES::saber | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises ES::ver | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| Idiomatic Tenses Exercises FR | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses Exercises FR::obéir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises FR::valoir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises FR::vouloir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| Idiomatic Tenses Exercises IT | 0 | 0 | 17 | 17 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses Exercises IT::sapere | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M10 |
| ↳ Idiomatic Tenses Exercises IT::volere | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M10 |
| Idiomatic Tenses Exercises PT | 0 | 0 | 14 | 14 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses Exercises PT::vir | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M10 |
| Idiomatic Tenses FR | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses FR::obéir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses FR::valoir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses FR::vouloir | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| Idiomatic Tenses IT | 0 | 0 | 17 | 17 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses IT::sapere | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M11 |
| ↳ Idiomatic Tenses IT::volere | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M11 |
| Idiomatic Tenses PT | 0 | 0 | 14 | 14 | 0 | 0 | 0 | — |
| ↳ Idiomatic Tenses PT::vir | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M11 |
| Idiomatic Translation DE | 0 | 0 | 79 | 79 | 0 | 0 | 0 | — |
| ↳ Idiomatic Translation DE::1 Genus | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation DE::2 Präpositionen | 34 | 34 | 34 | 34 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation DE::3 Adjektive | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation DE::4 Verben | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation DE::5 Kasus | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M12 |
| Idiomatic Translation ES | 0 | 0 | 250 | 250 | 0 | 0 | 0 | — |
| ↳ Idiomatic Translation ES::1 Tiempos | 71 | 71 | 71 | 71 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::2 Subjuntivo | 23 | 23 | 23 | 23 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::3 Condicionales | 24 | 24 | 24 | 24 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::4 Imperativo | 45 | 45 | 45 | 45 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::5 Pronombres | 40 | 40 | 40 | 40 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::6 Preposiciones | 24 | 24 | 24 | 24 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::7 Ser/Estar | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation ES::8 Grado y cantidad | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M12 |
| Idiomatic Translation FR | 0 | 0 | 146 | 146 | 0 | 0 | 0 | — |
| ↳ Idiomatic Translation FR::1 Temps | 58 | 58 | 58 | 58 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation FR::2 Conditionnel | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation FR::3 Subjonctif | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation FR::4 Pronoms | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation FR::5 Prépositions | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation FR::6 Genre & accord | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation FR::7 Articles & quantités | 26 | 26 | 26 | 26 | 0 | 0 | 0 | M12 |
| Idiomatic Translation IT | 0 | 0 | 130 | 130 | 0 | 0 | 0 | — |
| ↳ Idiomatic Translation IT::1 Tempi | 68 | 68 | 68 | 68 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation IT::2 Condizionale | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation IT::3 Congiuntivo | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation IT::4 Clitici | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation IT::5 Genere e plurali | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation IT::6 Reggenze | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M12 |
| Idiomatic Translation PT | 0 | 0 | 127 | 127 | 0 | 0 | 0 | — |
| ↳ Idiomatic Translation PT::1 Tempos | 52 | 52 | 52 | 52 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation PT::2 Condicional | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation PT::3 Subjuntivo | 30 | 30 | 30 | 30 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation PT::4 Clíticos | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M12 |
| ↳ Idiomatic Translation PT::5 Gênero & Artigos | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M12 |
| Languages | 0 | 0 | 7,325 | 8,306 | 2,128 | 16,980 | 17,445 | — |
| ↳ Languages::French | 0 | 0 | 1,153 | 1,503 | 380 | 3,544 | 3,544 | — |
| ↳ ↳ Languages::French::Fluency Expressions | 746 | 746 | 746 | 746 | 129 | 2,329 | 2,329 | M40 |
| ↳ ↳ Languages::French::Idioms Audio (EN → target) | 175 | 350 | 175 | 350 | 116 | 533 | 533 | M41 |
| ↳ ↳ Languages::French::Idioms Audio (target → EN) | 175 | 350 | 175 | 350 | 119 | 595 | 595 | M42 |
| ↳ ↳ Languages::French::YouTube | 0 | 0 | 57 | 57 | 16 | 87 | 87 | — |
| ↳ ↳ ↳ Languages::French::YouTube::"Le monde est une grande boutique", dénonce le socialiste Boris Vallaud | 0 | 0 | 13 | 13 | 0 | 18 | 18 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::"Le monde est une grande boutique", dénonce le socialiste Boris Vallaud::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::"Le monde est une grande boutique", dénonce le socialiste Boris Vallaud::1 Full (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::"Le monde est une grande boutique", dénonce le socialiste Boris Vallaud::Idioms | 13 | 13 | 13 | 13 | 0 | 18 | 18 | M44 |
| ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE | 0 | 0 | 12 | 12 | 0 | 12 | 12 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::01 Introduction - Artemis 2, Trump, and the return of the Unit… | 2 | 2 | 2 | 2 | 0 | 2 | 2 | M39 |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::01 Introduction - Artemis 2, Trump, and the return of the Unit… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::02 Introduction of guests - Isabelle Verger and the IFRI expert | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::02 Introduction of guests - Isabelle Verger and the IFRI expert (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::03 Editorial from Le Monde - The Moon, a new battleground for… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::03 Editorial from Le Monde - The Moon, a new battleground for… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::04 Artemis 2 - Technical success, but what impact on the publi… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::04 Artemis 2 - Technical success, but what impact on the publi… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::05 The Artemis program - an American initiative with aligned a… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::05 The Artemis program - an American initiative with aligned a… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::06 Lunar resources - Eldorado or speculation? | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::06 Lunar resources - Eldorado or speculation? (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::07 Three possible uses - scientific, industrial, geopolitical | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::07 Three possible uses - scientific, industrial, geopolitical (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::08 The Artemis Accords - imposing an American vision of lunar… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::08 The Artemis Accords - imposing an American vision of lunar… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::09 China in the race - lunar program, deadlines, and rivalry w… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::09 China in the race - lunar program, deadlines, and rivalry w… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::10 American fear - what if China sets foot on the Moon before… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::10 American fear - what if China sets foot on the Moon before… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::11 Does the Moon really belong to us? American rhetoric irrita… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::11 Does the Moon really belong to us? American rhetoric irrita… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::12 SpaceX, Musk, and NASA - agendas that don't always align | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::12 SpaceX, Musk, and NASA - agendas that don't always align (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::13 Editorial cartoon - the Artemis capsule flies over the war-… | 3 | 3 | 3 | 3 | 0 | 3 | 3 | M39 |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::13 Editorial cartoon - the Artemis capsule flies over the war-… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::14 Space and the realities of the world - the dream cannot ign… | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::14 Space and the realities of the world - the dream cannot ign… (EN→FR) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::LA LUNE COMME ENJEU GÉOPOLITIQUE : ÉTATS-UNIS CONTRE CHINE, LA NOUVELLE COURSE À L'ESPACE::Idioms | 7 | 7 | 7 | 7 | 0 | 7 | 7 | M44 |
| ↳ ↳ ↳ Languages::French::YouTube::Le litre de gasoil à 2,50 euros tout l'été ? - Le débat éco | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::Le litre de gasoil à 2,50 euros tout l'été ? - Le débat éco::Idioms | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ Languages::French::YouTube::Peter Pan est-il vraiment l’ami des enfants ? | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::Peter Pan est-il vraiment l’ami des enfants ?::Idioms | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ Languages::French::YouTube::Pourrquoi la GUERRE au SOUDAN dure depuis TROIS ANS | 0 | 0 | 16 | 16 | 0 | 21 | 21 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::Pourrquoi la GUERRE au SOUDAN dure depuis TROIS ANS::Idioms | 16 | 16 | 16 | 16 | 0 | 21 | 21 | M51 |
| ↳ ↳ ↳ Languages::French::YouTube::Reem Kherici, réalisatrice du film “Pour le plaisir” - Nouvelles têtes | 0 | 0 | 16 | 16 | 16 | 36 | 36 | — |
| ↳ ↳ ↳ ↳ Languages::French::YouTube::Reem Kherici, réalisatrice du film “Pour le plaisir” - Nouvelles têtes::Idioms | 16 | 16 | 16 | 16 | 16 | 36 | 36 | M51 |
| ↳ Languages::German | 0 | 0 | 947 | 1,179 | 310 | 2,591 | 3,042 | — |
| ↳ ↳ Languages::German::Fluency Expressions | 512 | 512 | 512 | 512 | 158 | 1,485 | 1,936 | M40 |
| ↳ ↳ Languages::German::Idioms Audio (EN → target) | 116 | 232 | 116 | 232 | 91 | 320 | 320 | M41 |
| ↳ ↳ Languages::German::Idioms Audio (target → EN) | 116 | 232 | 116 | 232 | 61 | 485 | 485 | M42 |
| ↳ ↳ Languages::German::YouTube | 0 | 0 | 203 | 203 | 0 | 301 | 301 | — |
| ↳ ↳ ↳ Languages::German::YouTube::Brüchige Waffenruhe: Tote nach israelischen Angriffen im Libanon | 0 | 0 | 12 | 12 | 0 | 16 | 16 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Brüchige Waffenruhe: Tote nach israelischen Angriffen im Libanon::Idioms | 12 | 12 | 12 | 12 | 0 | 16 | 16 | M48 |
| ↳ ↳ ↳ Languages::German::YouTube::Erstmals Militär-Strategie: Pistorius will Bundeswehr stärken \| tagesthemen-interview | 0 | 0 | 48 | 48 | 0 | 59 | 59 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Erstmals Militär-Strategie: Pistorius will Bundeswehr stärken \| tagesthemen-interview::1 Full | 28 | 28 | 28 | 28 | 0 | 30 | 30 | M39 |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Erstmals Militär-Strategie: Pistorius will Bundeswehr stärken \| tagesthemen-interview::1 Full (EN→DE) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Erstmals Militär-Strategie: Pistorius will Bundeswehr stärken \| tagesthemen-interview::Idioms | 20 | 20 | 20 | 20 | 0 | 29 | 29 | M44 |
| ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs | 0 | 0 | 13 | 13 | 0 | 21 | 21 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs::1 Full (EN→DE) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs::Idioms | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs::Idioms (ElevenLabs Flash) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs::Idioms (Gemini Flash) | 12 | 12 | 12 | 12 | 0 | 19 | 19 | M46 |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Gipfeltreffen auf Zypern: Die EU ringt um ihren Nahost-Kurs::Idioms (Piper) | 1 | 1 | 1 | 1 | 0 | 2 | 2 | M47 |
| ↳ ↳ ↳ Languages::German::YouTube::Hollywood-Regisseur Emmerich zu den Chancen von KI in der Filmproduktion \| tagesthemen-Interview | 0 | 0 | 28 | 28 | 0 | 42 | 42 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Hollywood-Regisseur Emmerich zu den Chancen von KI in der Filmproduktion \| tagesthemen-Interview::Idioms | 28 | 28 | 28 | 28 | 0 | 42 | 42 | M48 |
| ↳ ↳ ↳ Languages::German::YouTube::ifo-Index: Darum ist die deutsche Wirtschaft so verunsichert | 0 | 0 | 10 | 10 | 0 | 17 | 17 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::ifo-Index: Darum ist die deutsche Wirtschaft so verunsichert::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::ifo-Index: Darum ist die deutsche Wirtschaft so verunsichert::1 Full (EN→DE) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::ifo-Index: Darum ist die deutsche Wirtschaft so verunsichert::Idioms | 10 | 10 | 10 | 10 | 0 | 17 | 17 | M44 |
| ↳ ↳ ↳ Languages::German::YouTube::SPD-Fraktionschef Miersch über Reformpolitik \| tagesthemen-Interview | 0 | 0 | 7 | 7 | 0 | 9 | 9 | — |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::SPD-Fraktionschef Miersch über Reformpolitik \| tagesthemen-Interview::Idioms | 7 | 7 | 7 | 7 | 0 | 9 | 9 | M48 |
| ↳ ↳ ↳ Languages::German::YouTube::Trump verlängert Waffenruhe: Folgen Verhandlungen zwischen USA und Iran? \| tagesthemen-Interview | 59 | 59 | 79 | 79 | 0 | 123 | 123 | M39 |
| ↳ ↳ ↳ ↳ Languages::German::YouTube::Trump verlängert Waffenruhe: Folgen Verhandlungen zwischen USA und Iran? \| tagesthemen-Interview::Idioms | 20 | 20 | 20 | 20 | 0 | 25 | 25 | M44 |
| ↳ ↳ ↳ Languages::German::YouTube::Trump verlängert Waffenruhe: Folgen Verhandlungen zwischen USA und Iran? \| tagesthemen-Interview (EN→DE) | 6 | 6 | 6 | 6 | 0 | 14 | 14 | M37 |
| ↳ Languages::Italian | 0 | 0 | 1,214 | 1,494 | 957 | 6,025 | 6,037 | — |
| ↳ ↳ Languages::Italian::Fluency Expressions | 840 | 840 | 840 | 840 | 765 | 4,951 | 4,963 | M40 |
| ↳ ↳ Languages::Italian::Idioms Audio (EN → target) | 140 | 280 | 140 | 280 | 117 | 458 | 458 | M41 |
| ↳ ↳ Languages::Italian::Idioms Audio (target → EN) | 140 | 280 | 140 | 280 | 75 | 491 | 491 | M42 |
| ↳ ↳ Languages::Italian::YouTube | 0 | 0 | 94 | 94 | 0 | 125 | 125 | — |
| ↳ ↳ ↳ Languages::Italian::YouTube::"Trump non finirà il suo mandato" - Caracciolo a Otto e Mezzo | 0 | 0 | 20 | 20 | 0 | 27 | 27 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::"Trump non finirà il suo mandato" - Caracciolo a Otto e Mezzo::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::"Trump non finirà il suo mandato" - Caracciolo a Otto e Mezzo::1 Full (EN→IT) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::"Trump non finirà il suo mandato" - Caracciolo a Otto e Mezzo::Idioms | 20 | 20 | 20 | 20 | 0 | 27 | 27 | M44 |
| ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo a Otto e Mezzo: Meloni, Trump e la remigrazione | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo a Otto e Mezzo: Meloni, Trump e la remigrazione::Idioms | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo a Otto e Mezzo: Meloni-Trump e la remigrazione in Europa. Guerra Iran e vertice Usa-Cina | 0 | 0 | 1 | 1 | 0 | 1 | 1 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo a Otto e Mezzo: Meloni-Trump e la remigrazione in Europa. Guerra Iran e vertice Usa-Cina::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo a Otto e Mezzo: Meloni-Trump e la remigrazione in Europa. Guerra Iran e vertice Usa-Cina::1 Full (EN→IT) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo a Otto e Mezzo: Meloni-Trump e la remigrazione in Europa. Guerra Iran e vertice Usa-Cina::Idioms | 1 | 1 | 1 | 1 | 0 | 1 | 1 | M44 |
| ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo: L'Italia e la guerra all'Iran. In Trappola /2. Il nuovo volume di Limes in edicola | 0 | 0 | 7 | 7 | 0 | 9 | 9 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Caracciolo: L'Italia e la guerra all'Iran. In Trappola /2. Il nuovo volume di Limes in edicola::Idioms | 7 | 7 | 7 | 7 | 0 | 9 | 9 | M54 |
| ↳ ↳ ↳ Languages::Italian::YouTube::Iran e Libano, Israele contro la tregua. Trump sottomesso a Netanyahu - Caracciolo a Otto e mezzo | 0 | 0 | 13 | 13 | 0 | 21 | 21 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Iran e Libano, Israele contro la tregua. Trump sottomesso a Netanyahu - Caracciolo a Otto e mezzo::Idioms | 13 | 13 | 13 | 13 | 0 | 21 | 21 | M53 |
| ↳ ↳ ↳ Languages::Italian::YouTube::Iran, Caracciolo: "La delegazione americana brilla per incompetenza" | 0 | 0 | 10 | 10 | 0 | 15 | 15 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Iran, Caracciolo: "La delegazione americana brilla per incompetenza"::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Iran, Caracciolo: "La delegazione americana brilla per incompetenza"::1 Full (EN→IT) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Iran, Caracciolo: "La delegazione americana brilla per incompetenza"::Idioms | 10 | 10 | 10 | 10 | 0 | 15 | 15 | M44 |
| ↳ ↳ ↳ Languages::Italian::YouTube::Iran, Trump si è messo in scacco da solo. La cultura russa alla Biennale - Caracciolo a Otto e mezzo | 0 | 0 | 9 | 9 | 0 | 10 | 10 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::Iran, Trump si è messo in scacco da solo. La cultura russa alla Biennale - Caracciolo a Otto e mezzo::Idioms | 9 | 9 | 9 | 9 | 0 | 10 | 10 | M54 |
| ↳ ↳ ↳ Languages::Italian::YouTube::L'attentato a Trump (a Washington D.C.). Le polemiche per il 25 aprile - Caracciolo a Otto e Mezzo | 0 | 0 | 10 | 10 | 0 | 11 | 11 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::L'attentato a Trump (a Washington D.C.). Le polemiche per il 25 aprile - Caracciolo a Otto e Mezzo::Idioms | 10 | 10 | 10 | 10 | 0 | 11 | 11 | M53 |
| ↳ ↳ ↳ Languages::Italian::YouTube::LimesReplay - Caracciolo a In altre Parole: Hormuz. Islamabad e i negoziati. Il papa e Trump | 0 | 0 | 24 | 24 | 0 | 31 | 31 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::LimesReplay - Caracciolo a In altre Parole: Hormuz. Islamabad e i negoziati. Il papa e Trump::1 Full | 4 | 4 | 4 | 4 | 0 | 5 | 5 | M39 |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::LimesReplay - Caracciolo a In altre Parole: Hormuz. Islamabad e i negoziati. Il papa e Trump::1 Full (EN→IT) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Italian::YouTube::LimesReplay - Caracciolo a In altre Parole: Hormuz. Islamabad e i negoziati. Il papa e Trump::Idioms | 20 | 20 | 20 | 20 | 0 | 26 | 26 | M44 |
| ↳ Languages::Mandarin | 0 | 0 | 2,600 | 2,614 | 12 | 270 | 270 | — |
| ↳ ↳ Languages::Mandarin::ChinesePod | 0 | 0 | 2,571 | 2,571 | 12 | 269 | 269 | — |
| ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2 | 0 | 0 | 989 | 989 | 0 | 19 | 19 | — |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Afraid of Dogs | 0 | 0 | 25 | 25 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Afraid of Dogs::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Afraid of Dogs::Words | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Bad Cell Reception | 0 | 0 | 25 | 25 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Bad Cell Reception::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Bad Cell Reception::Words | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Bank Hours | 0 | 0 | 26 | 26 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Bank Hours::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Bank Hours::Words | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Changing Class Time | 0 | 0 | 36 | 36 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Changing Class Time::Phrases | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Changing Class Time::Words | 26 | 26 | 26 | 26 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Directions with a Map #1 | 0 | 0 | 20 | 20 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Directions with a Map #1::Words | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Directions with a Map #2 | 0 | 0 | 24 | 24 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Directions with a Map #2::Words | 24 | 24 | 24 | 24 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Excited About Traveling | 0 | 0 | 27 | 27 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Excited About Traveling::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Excited About Traveling::Words | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Going to the Doctor | 0 | 0 | 20 | 20 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Going to the Doctor::Phrases | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Going to the Doctor::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Hanging Up the Phone | 0 | 0 | 19 | 19 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Hanging Up the Phone::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Hanging Up the Phone::Words | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Here is your change | 0 | 0 | 20 | 20 | 0 | 8 | 8 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Here is your change::Phrases | 4 | 4 | 4 | 4 | 0 | 4 | 4 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Here is your change::Words | 16 | 16 | 16 | 16 | 0 | 4 | 4 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Intermediate - Chinese Money | 0 | 0 | 21 | 21 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Intermediate - Chinese Money::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Intermediate - Chinese Money::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Intermediate - Pin Number | 0 | 0 | 25 | 25 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Intermediate - Pin Number::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Intermediate - Pin Number::Words | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases | 0 | 0 | 114 | 114 | 0 | 11 | 11 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Afraid of Dogs | 8 | 8 | 8 | 8 | 0 | 8 | 8 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Bad Cell Reception | 8 | 8 | 8 | 8 | 0 | 3 | 3 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Bank Hours | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Changing Class Time | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Excited About Traveling | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Going to the Doctor | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Hanging Up the Phone | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Here is your change | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Intermediate - Chinese Money | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Intermediate - Pin Number | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Tone Change Rule: Yi ’一 ’ | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Weather and Seasons | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Which friend? | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Which tone was that again? | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Why are You Studying Chinese? | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Phrases::Workout Frequency at the Gym | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Change Rule: Yi ’一 ’ | 0 | 0 | 26 | 26 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Change Rule: Yi ’一 ’::Phrases | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Change Rule: Yi ’一 ’::Words | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Rule: Changes for ’bu’ | 0 | 0 | 15 | 15 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Rule: Changes for ’bu’::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Rule: Two Third Tones | 0 | 0 | 10 | 10 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Tone Rule: Two Third Tones::Words | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Weather and Seasons | 0 | 0 | 41 | 41 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Weather and Seasons::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Weather and Seasons::Words | 35 | 35 | 35 | 35 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Which friend? | 0 | 0 | 28 | 28 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Which friend?::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Which friend?::Words | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Which tone was that again? | 0 | 0 | 32 | 32 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Which tone was that again?::Phrases | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Which tone was that again?::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Why are You Studying Chinese? | 0 | 0 | 28 | 28 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Why are You Studying Chinese?::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Why are You Studying Chinese?::Words | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words | 0 | 0 | 380 | 380 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Afraid of Dogs | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Bad Cell Reception | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Bank Hours | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Changing Class Time | 26 | 26 | 26 | 26 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Directions with a Map #1 | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Directions with a Map #2 | 23 | 23 | 23 | 23 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Excited About Traveling | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Going to the Doctor | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Hanging Up the Phone | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Here is your change | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Intermediate - Chinese Money | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Intermediate - Pin Number | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Tone Change Rule: Yi ’一 ’ | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Tone Rule: Changes for ’bu’ | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Tone Rule: Two Third Tones | 10 | 10 | 10 | 10 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Weather and Seasons | 35 | 35 | 35 | 35 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Which friend? | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Which tone was that again? | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Why are You Studying Chinese? | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Words::Workout Frequency at the Gym | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Workout Frequency at the Gym | 0 | 0 | 27 | 27 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Workout Frequency at the Gym::Phrases | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::Daily Life 2::Workout Frequency at the Gym::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary | 0 | 0 | 1,582 | 1,582 | 12 | 250 | 250 | — |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - A Simple Tour of the Office | 0 | 0 | 31 | 31 | 0 | 3 | 3 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - A Simple Tour of the Office::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - A Simple Tour of the Office::Words | 23 | 23 | 23 | 23 | 0 | 3 | 3 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - A Snake Discovery | 0 | 0 | 27 | 27 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - A Snake Discovery::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - A Snake Discovery::Words | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Asking About the New Job | 0 | 0 | 29 | 29 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Asking About the New Job::Phrases | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Asking About the New Job::Words | 25 | 25 | 25 | 25 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Asking for Sick Leave | 0 | 0 | 27 | 27 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Asking for Sick Leave::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Asking for Sick Leave::Words | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Borrowing Money From a | 0 | 0 | 21 | 21 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Borrowing Money From a::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Borrowing Money From a::Words | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Changing the Plate | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Changing the Plate::Phrases | 5 | 5 | 5 | 5 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Changing the Plate::Words | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Consoling the Bereaved | 0 | 0 | 21 | 21 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Consoling the Bereaved::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Consoling the Bereaved::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Dining and Dropping | 0 | 0 | 25 | 25 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Dining and Dropping::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Dining and Dropping::Words | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Don't Litter | 0 | 0 | 26 | 26 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Don't Litter::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Don't Litter::Words | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Full for Real | 0 | 0 | 30 | 30 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Full for Real::Phrases | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Full for Real::Words | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Giving up a Seat on the Bus | 0 | 0 | 31 | 31 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Giving up a Seat on the Bus::Phrases | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Giving up a Seat on the Bus::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - He Won't Carry My Handbag | 0 | 0 | 23 | 23 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - He Won't Carry My Handbag::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - He Won't Carry My Handbag::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Hospitality Series 5: Searching for | 0 | 0 | 31 | 31 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Hospitality Series 5: Searching for::Phrases | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Hospitality Series 5: Searching for::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - I Can't Afford Cake | 0 | 0 | 18 | 18 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - I Can't Afford Cake::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - I Can't Afford Cake::Words | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Morning and After-Work | 0 | 0 | 22 | 22 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Morning and After-Work::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Morning and After-Work::Words | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - My boss isn't satisfied | 0 | 0 | 15 | 15 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - My boss isn't satisfied::Phrases | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - My boss isn't satisfied::Words | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - No Bargaining | 0 | 0 | 23 | 23 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - No Bargaining::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - No Bargaining::Words | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - No Tampons?! | 0 | 0 | 19 | 19 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - No Tampons?!::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - No Tampons?!::Words | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Not Studious Enough | 0 | 0 | 22 | 22 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Not Studious Enough::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Not Studious Enough::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Picking Up a Friend at the | 0 | 0 | 30 | 30 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Picking Up a Friend at the::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Picking Up a Friend at the::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Shampoo and Cut | 0 | 0 | 26 | 26 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Shampoo and Cut::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Shampoo and Cut::Words | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Cycling Holiday | 0 | 0 | 31 | 31 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Cycling Holiday::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Cycling Holiday::Words | 24 | 24 | 24 | 24 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Dolphin Show at | 0 | 0 | 30 | 30 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Dolphin Show at::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Dolphin Show at::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The North Has Central | 0 | 0 | 36 | 36 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The North Has Central::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The North Has Central::Words | 29 | 29 | 29 | 29 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Year of the Horse | 0 | 0 | 24 | 24 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Year of the Horse::Phrases | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - The Year of the Horse::Words | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Toothache | 0 | 0 | 29 | 29 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Toothache::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Toothache::Words | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - What have you done in 2009? | 0 | 0 | 36 | 36 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - What have you done in 2009?::Phrases | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - What have you done in 2009?::Words | 28 | 28 | 28 | 28 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - What's your type? | 0 | 0 | 21 | 21 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - What's your type?::Phrases | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - What's your type?::Words | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Which country are you from? | 0 | 0 | 20 | 20 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Which country are you from?::Phrases | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Which country are you from?::Words | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Your First Mooncake | 0 | 0 | 29 | 29 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Your First Mooncake::Phrases | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Your First Mooncake::Words | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Your turn to pay! | 0 | 0 | 20 | 20 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Your turn to pay!::Phrases | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Intermediate - Your turn to pay!::Words | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases | 0 | 0 | 214 | 214 | 12 | 247 | 247 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - A Simple Tour of the Office | 8 | 8 | 8 | 8 | 3 | 22 | 22 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - A Snake Discovery | 8 | 8 | 8 | 8 | 1 | 15 | 15 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Asking About the New Job | 4 | 4 | 4 | 4 | 1 | 7 | 7 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Asking for Sick Leave | 6 | 6 | 6 | 6 | 1 | 8 | 8 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Borrowing Money From a | 8 | 8 | 8 | 8 | 1 | 12 | 12 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Changing the Plate | 5 | 5 | 5 | 5 | 0 | 10 | 10 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Consoling the Bereaved | 6 | 6 | 6 | 6 | 1 | 11 | 11 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Dining and Dropping | 7 | 7 | 7 | 7 | 0 | 10 | 10 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Don't Litter | 6 | 6 | 6 | 6 | 1 | 12 | 12 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Full for Real | 9 | 9 | 9 | 9 | 2 | 17 | 17 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Giving up a Seat on the Bus | 9 | 9 | 9 | 9 | 1 | 16 | 16 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - He Won't Carry My Handbag | 8 | 8 | 8 | 8 | 0 | 13 | 13 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Hospitality Series 5: Searching for | 9 | 9 | 9 | 9 | 0 | 10 | 10 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - I Can't Afford Cake | 6 | 6 | 6 | 6 | 0 | 10 | 10 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Morning and After-Work | 6 | 6 | 6 | 6 | 0 | 8 | 8 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - My boss isn't satisfied | 4 | 4 | 4 | 4 | 0 | 7 | 7 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - No Bargaining | 7 | 7 | 7 | 7 | 0 | 11 | 11 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - No Tampons?! | 8 | 8 | 8 | 8 | 0 | 10 | 10 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Not Studious Enough | 7 | 7 | 7 | 7 | 0 | 9 | 9 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Picking Up a Friend at the | 8 | 8 | 8 | 8 | 0 | 8 | 8 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Shampoo and Cut | 7 | 7 | 7 | 7 | 0 | 9 | 9 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - The Cycling Holiday | 7 | 7 | 7 | 7 | 0 | 8 | 8 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - The Dolphin Show at | 8 | 8 | 8 | 8 | 0 | 4 | 4 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - The North Has Central | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - The Year of the Horse | 9 | 9 | 9 | 9 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Toothache | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - What have you done in 2009? | 8 | 8 | 8 | 8 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - What's your type? | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Which country are you from? | 6 | 6 | 6 | 6 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Your First Mooncake | 7 | 7 | 7 | 7 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Phrases::Intermediate - Your turn to pay! | 4 | 4 | 4 | 4 | 0 | 0 | 0 | M02 |
| ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words | 0 | 0 | 577 | 577 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - A Simple Tour of the Office | 23 | 23 | 23 | 23 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - A Snake Discovery | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Asking About the New Job | 25 | 25 | 25 | 25 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Asking for Sick Leave | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Borrowing Money From a | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Changing the Plate | 13 | 13 | 13 | 13 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Consoling the Bereaved | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Dining and Dropping | 18 | 18 | 18 | 18 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Don't Litter | 20 | 20 | 20 | 20 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Full for Real | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Giving up a Seat on the Bus | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - He Won't Carry My Handbag | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Hospitality Series 5: Searching for | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - I Can't Afford Cake | 12 | 12 | 12 | 12 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Morning and After-Work | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - My boss isn't satisfied | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - No Bargaining | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - No Tampons?! | 11 | 11 | 11 | 11 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Not Studious Enough | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Picking Up a Friend at the | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Shampoo and Cut | 19 | 19 | 19 | 19 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - The Cycling Holiday | 24 | 24 | 24 | 24 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - The Dolphin Show at | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - The North Has Central | 29 | 29 | 29 | 29 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - The Year of the Horse | 15 | 15 | 15 | 15 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Toothache | 21 | 21 | 21 | 21 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - What have you done in 2009? | 28 | 28 | 28 | 28 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - What's your type? | 17 | 17 | 17 | 17 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Which country are you from? | 14 | 14 | 14 | 14 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Your First Mooncake | 22 | 22 | 22 | 22 | 0 | 0 | 0 | M03 |
| ↳ ↳ ↳ ↳ ↳ Languages::Mandarin::ChinesePod::HSK Level 3 Vocabulary::Words::Intermediate - Your turn to pay! | 16 | 16 | 16 | 16 | 0 | 0 | 0 | M03 |
| ↳ ↳ Languages::Mandarin::YouTube | 0 | 0 | 29 | 43 | 0 | 1 | 1 | — |
| ↳ ↳ ↳ Languages::Mandarin::YouTube::中國的三年抗疫：如何從「清零」走向「與病毒共存」－ BBC News 中文 | 0 | 0 | 29 | 43 | 0 | 1 | 1 | — |
| ↳ ↳ ↳ ↳ Languages::Mandarin::YouTube::中國的三年抗疫：如何從「清零」走向「與病毒共存」－ BBC News 中文::Phrases v3 | 29 | 43 | 29 | 43 | 0 | 1 | 1 | M19, M20 |
| ↳ Languages::Portuguese | 0 | 0 | 884 | 989 | 416 | 3,451 | 3,453 | — |
| ↳ ↳ Languages::Portuguese::Fluency Expressions | 630 | 630 | 630 | 630 | 385 | 3,065 | 3,065 | M40 |
| ↳ ↳ Languages::Portuguese::Idioms Audio (EN → target) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ Languages::Portuguese::Idioms Audio (target → EN) | 105 | 210 | 105 | 210 | 0 | 119 | 119 | M42 |
| ↳ ↳ Languages::Portuguese::Porta dos Fundos | 0 | 0 | 63 | 63 | 12 | 119 | 121 | — |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::BRASIL GARFADO NO OSCAR | 1 | 1 | 1 | 1 | 0 | 1 | 1 | M39 |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::FURTINHO | 28 | 28 | 28 | 28 | 0 | 33 | 33 | M39 |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::INTESTINO ESCROTO | 1 | 1 | 1 | 1 | 0 | 1 | 1 | M39 |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::LEI DO EX | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::ORTOGRAFIA | 31 | 31 | 31 | 31 | 12 | 81 | 82 | M39 |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::PENA MÁXIMA | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::PUXA SACO | 2 | 2 | 2 | 2 | 0 | 3 | 4 | M39 |
| ↳ ↳ ↳ Languages::Portuguese::Porta dos Fundos::WAGNER MOURA VAI PERDER | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ Languages::Portuguese::YouTube | 0 | 0 | 86 | 86 | 19 | 148 | 148 | — |
| ↳ ↳ ↳ Languages::Portuguese::YouTube::Breno Altman Critica Esquerda Liberal e Escola de Frankfurt | 0 | 0 | 18 | 18 | 10 | 37 | 37 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Breno Altman Critica Esquerda Liberal e Escola de Frankfurt::1 Full | 2 | 2 | 2 | 2 | 0 | 2 | 2 | M39 |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Breno Altman Critica Esquerda Liberal e Escola de Frankfurt::1 Full (EN→PT) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Breno Altman Critica Esquerda Liberal e Escola de Frankfurt::Idioms | 16 | 16 | 16 | 16 | 10 | 35 | 35 | M44 |
| ↳ ↳ ↳ Languages::Portuguese::YouTube::Helder Maldonado Analisa Por Que Esquerda Subestimou Olavo de Carvalho | 0 | 0 | 11 | 11 | 0 | 14 | 14 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Helder Maldonado Analisa Por Que Esquerda Subestimou Olavo de Carvalho::Idioms | 11 | 11 | 11 | 11 | 0 | 14 | 14 | M56 |
| ↳ ↳ ↳ Languages::Portuguese::YouTube::José Kobori Expõe o Prejuízo Bilionário dos Incentivos a Data Centers | 0 | 0 | 14 | 14 | 7 | 27 | 27 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::José Kobori Expõe o Prejuízo Bilionário dos Incentivos a Data Centers::Idioms | 14 | 14 | 14 | 14 | 7 | 27 | 27 | M55 |
| ↳ ↳ ↳ Languages::Portuguese::YouTube::José Kobori Revela Por Que Bolha da IA, Guerra e Preço do Petróleo Podem Levar o Mundo à Depressão | 0 | 0 | 20 | 20 | 2 | 40 | 40 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::José Kobori Revela Por Que Bolha da IA, Guerra e Preço do Petróleo Podem Levar o Mundo à Depressão::Idioms | 20 | 20 | 20 | 20 | 2 | 40 | 40 | M56 |
| ↳ ↳ ↳ Languages::Portuguese::YouTube::MIGUEL NICOLELIS - Sapiens de Yuval Harari é inteligência ou é artificial? | 0 | 0 | 3 | 3 | 0 | 4 | 4 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::MIGUEL NICOLELIS - Sapiens de Yuval Harari é inteligência ou é artificial?::Idioms | 3 | 3 | 3 | 3 | 0 | 4 | 4 | M55 |
| ↳ ↳ ↳ Languages::Portuguese::YouTube::Qual deve ser a política do Brasil para as terras raras? Embaixador Rubens Barbosa responde | 0 | 0 | 20 | 20 | 0 | 26 | 26 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Qual deve ser a política do Brasil para as terras raras? Embaixador Rubens Barbosa responde::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Qual deve ser a política do Brasil para as terras raras? Embaixador Rubens Barbosa responde::1 Full (EN→PT) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Portuguese::YouTube::Qual deve ser a política do Brasil para as terras raras? Embaixador Rubens Barbosa responde::Idioms | 20 | 20 | 20 | 20 | 0 | 26 | 26 | M44 |
| ↳ Languages::Spanish | 0 | 0 | 527 | 527 | 53 | 1,099 | 1,099 | — |
| ↳ ↳ Languages::Spanish::Fluency Expressions | 433 | 433 | 433 | 433 | 50 | 962 | 962 | M40 |
| ↳ ↳ Languages::Spanish::Idioms Audio (EN → target) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ Languages::Spanish::Idioms Audio (target → EN) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ Languages::Spanish::YouTube | 0 | 0 | 94 | 94 | 3 | 137 | 137 | — |
| ↳ ↳ ↳ Languages::Spanish::YouTube::Análisis \| Nuevo embajador de México en EE.UU.: los retos clave en la relación bilateral | 0 | 0 | 18 | 18 | 3 | 28 | 28 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::Análisis \| Nuevo embajador de México en EE.UU.: los retos clave en la relación bilateral::Idioms | 18 | 18 | 18 | 18 | 3 | 28 | 28 | M49 |
| ↳ ↳ ↳ Languages::Spanish::YouTube::El Pentágono plantea suspender a España de la OTAN por su falta de apoyo en Irán | 0 | 0 | 14 | 14 | 0 | 20 | 20 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::El Pentágono plantea suspender a España de la OTAN por su falta de apoyo en Irán::Idioms | 14 | 14 | 14 | 14 | 0 | 20 | 20 | M49 |
| ↳ ↳ ↳ Languages::Spanish::YouTube::Sánchez responde al plan del Pentágono de España en la OTAN: “España es un socio leal” | 0 | 0 | 24 | 24 | 0 | 29 | 29 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::Sánchez responde al plan del Pentágono de España en la OTAN: “España es un socio leal”::Idioms | 24 | 24 | 24 | 24 | 0 | 29 | 29 | M50 |
| ↳ ↳ ↳ Languages::Spanish::YouTube::Un 'servidor humano' expone la sed digital en Chile | 0 | 0 | 14 | 14 | 0 | 23 | 23 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::Un 'servidor humano' expone la sed digital en Chile::1 Full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::Un 'servidor humano' expone la sed digital en Chile::1 Full (EN→ES) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::Un 'servidor humano' expone la sed digital en Chile::Idioms | 14 | 14 | 14 | 14 | 0 | 23 | 23 | M44 |
| ↳ ↳ ↳ Languages::Spanish::YouTube::🟢Plan de Trump para escoltar buques en Ormuz no avanza | 0 | 0 | 24 | 24 | 0 | 37 | 37 | — |
| ↳ ↳ ↳ ↳ Languages::Spanish::YouTube::🟢Plan de Trump para escoltar buques en Ormuz no avanza::Idioms | 24 | 24 | 24 | 24 | 0 | 37 | 37 | M50 |
| Lex-Stage · German vocab/idiom mnemonics (prototype) | 18 | 28 | 18 | 28 | 0 | 34 | 34 | M13 |
| Mandarin Actors | 55 | 55 | 55 | 55 | 45 | 1,091 | 1,091 | M14 |
| Mandarin Characters 2026-06-20 | 222 | 222 | 222 | 222 | 1 | 366 | 366 | M15 |
| Mandarin China Provinces | 34 | 204 | 34 | 204 | 0 | 9 | 15 | M01 |
| Mandarin Locations | 13 | 13 | 13 | 13 | 0 | 67 | 68 | M16 |
| Mandarin Palace | 0 | 0 | 339 | 339 | 0 | 1 | 1 | — |
| ↳ Mandarin Palace::Characters | 100 | 100 | 100 | 100 | 0 | 1 | 1 | M17 |
| ↳ Mandarin Palace::Words | 239 | 239 | 239 | 239 | 0 | 0 | 0 | M17 |
| Mandarin Props | 599 | 599 | 599 | 599 | 583 | 26,391 | 26,890 | M21, M22, M23 |
| Mandarin Zones | 65 | 65 | 65 | 65 | 0 | 73 | 73 | M24 |
| Pimsleur | 0 | 0 | 34,211 | 34,211 | 1,776 | 14,184 | 14,185 | — |
| ↳ Pimsleur::Danish | 0 | 0 | 612 | 612 | 0 | 0 | 0 | — |
| ↳ ↳ Pimsleur::Danish::Level 1 | 612 | 612 | 612 | 612 | 0 | 0 | 0 | M25 |
| ↳ Pimsleur::Dutch | 0 | 0 | 609 | 609 | 0 | 0 | 0 | — |
| ↳ ↳ Pimsleur::Dutch::Level 1 | 609 | 609 | 609 | 609 | 0 | 0 | 0 | M26 |
| ↳ Pimsleur::French | 0 | 0 | 4,693 | 4,693 | 0 | 0 | 0 | — |
| ↳ ↳ Pimsleur::French::Level 1 | 727 | 727 | 727 | 727 | 0 | 0 | 0 | M27 |
| ↳ ↳ Pimsleur::French::Level 2 | 720 | 720 | 720 | 720 | 0 | 0 | 0 | M27 |
| ↳ ↳ Pimsleur::French::Level 3 | 730 | 730 | 730 | 730 | 0 | 0 | 0 | M27 |
| ↳ ↳ Pimsleur::French::Level 4 | 1,256 | 1,256 | 1,256 | 1,256 | 0 | 0 | 0 | M27 |
| ↳ ↳ Pimsleur::French::Level 5 | 1,260 | 1,260 | 1,260 | 1,260 | 0 | 0 | 0 | M27 |
| ↳ Pimsleur::German | 0 | 0 | 5,311 | 5,311 | 0 | 11 | 11 | — |
| ↳ ↳ Pimsleur::German::Level 1 | 755 | 755 | 755 | 755 | 0 | 2 | 2 | M28 |
| ↳ ↳ Pimsleur::German::Level 2 | 899 | 899 | 899 | 899 | 0 | 0 | 0 | M28 |
| ↳ ↳ Pimsleur::German::Level 3 | 1,143 | 1,143 | 1,143 | 1,143 | 0 | 2 | 2 | M28 |
| ↳ ↳ Pimsleur::German::Level 4 | 1,256 | 1,256 | 1,256 | 1,256 | 0 | 0 | 0 | M28 |
| ↳ ↳ Pimsleur::German::Level 5 | 1,258 | 1,258 | 1,258 | 1,258 | 0 | 7 | 7 | M28 |
| ↳ Pimsleur::Italian | 0 | 0 | 5,344 | 5,344 | 498 | 1,892 | 1,892 | — |
| ↳ ↳ Pimsleur::Italian::Level 1 | 788 | 788 | 788 | 788 | 0 | 1 | 1 | M29 |
| ↳ ↳ Pimsleur::Italian::Level 2 | 882 | 882 | 882 | 882 | 0 | 0 | 0 | M29 |
| ↳ ↳ Pimsleur::Italian::Level 3 | 1,145 | 1,145 | 1,145 | 1,145 | 498 | 1,864 | 1,864 | M29 |
| ↳ ↳ Pimsleur::Italian::Level 4 | 1,269 | 1,269 | 1,269 | 1,269 | 0 | 27 | 27 | M29 |
| ↳ ↳ Pimsleur::Italian::Level 5 | 1,260 | 1,260 | 1,260 | 1,260 | 0 | 0 | 0 | M29 |
| ↳ Pimsleur::Mandarin | 0 | 0 | 3,043 | 3,043 | 1,278 | 12,271 | 12,272 | — |
| ↳ ↳ Pimsleur::Mandarin::Level 1 | 600 | 600 | 600 | 600 | 425 | 2,197 | 2,198 | M30 |
| ↳ ↳ Pimsleur::Mandarin::Level 2 | 608 | 608 | 608 | 608 | 248 | 2,114 | 2,114 | M30 |
| ↳ ↳ Pimsleur::Mandarin::Level 3 | 604 | 604 | 604 | 604 | 349 | 2,632 | 2,632 | M30 |
| ↳ ↳ Pimsleur::Mandarin::Level 4 | 610 | 610 | 610 | 610 | 136 | 3,382 | 3,382 | M30 |
| ↳ ↳ Pimsleur::Mandarin::Level 5 | 621 | 621 | 621 | 621 | 120 | 1,946 | 1,946 | M30 |
| ↳ Pimsleur::Norwegian | 0 | 0 | 1,216 | 1,216 | 0 | 0 | 0 | — |
| ↳ ↳ Pimsleur::Norwegian::Level 1 | 607 | 607 | 607 | 607 | 0 | 0 | 0 | M31 |
| ↳ ↳ Pimsleur::Norwegian::Level 2 | 609 | 609 | 609 | 609 | 0 | 0 | 0 | M31 |
| ↳ Pimsleur::Portuguese | 0 | 0 | 4,344 | 4,344 | 0 | 9 | 9 | — |
| ↳ ↳ Pimsleur::Portuguese::Level 1 | 627 | 627 | 627 | 627 | 0 | 0 | 0 | M32 |
| ↳ ↳ Pimsleur::Portuguese::Level 2 | 601 | 601 | 601 | 601 | 0 | 0 | 0 | M32 |
| ↳ ↳ Pimsleur::Portuguese::Level 3 | 606 | 606 | 606 | 606 | 0 | 0 | 0 | M32 |
| ↳ ↳ Pimsleur::Portuguese::Level 4 | 1,254 | 1,254 | 1,254 | 1,254 | 0 | 6 | 6 | M32 |
| ↳ ↳ Pimsleur::Portuguese::Level 5 | 1,256 | 1,256 | 1,256 | 1,256 | 0 | 3 | 3 | M32 |
| ↳ Pimsleur::Spanish | 0 | 0 | 4,378 | 4,378 | 0 | 1 | 1 | — |
| ↳ ↳ Pimsleur::Spanish::Level 1 | 610 | 610 | 610 | 610 | 0 | 0 | 0 | M33 |
| ↳ ↳ Pimsleur::Spanish::Level 2 | 609 | 609 | 609 | 609 | 0 | 0 | 0 | M33 |
| ↳ ↳ Pimsleur::Spanish::Level 3 | 610 | 610 | 610 | 610 | 0 | 0 | 0 | M33 |
| ↳ ↳ Pimsleur::Spanish::Level 4 | 1,277 | 1,277 | 1,277 | 1,277 | 0 | 0 | 0 | M33 |
| ↳ ↳ Pimsleur::Spanish::Level 5 | 1,272 | 1,272 | 1,272 | 1,272 | 0 | 1 | 1 | M33 |
| ↳ Pimsleur::Spanish (Latin America) | 0 | 0 | 4,051 | 4,051 | 0 | 0 | 0 | — |
| ↳ ↳ Pimsleur::Spanish (Latin America)::Level 1 | 677 | 677 | 677 | 677 | 0 | 0 | 0 | M34 |
| ↳ ↳ Pimsleur::Spanish (Latin America)::Level 2 | 725 | 725 | 725 | 725 | 0 | 0 | 0 | M34 |
| ↳ ↳ Pimsleur::Spanish (Latin America)::Level 3 | 775 | 775 | 775 | 775 | 0 | 0 | 0 | M34 |
| ↳ ↳ Pimsleur::Spanish (Latin America)::Level 4 | 627 | 627 | 627 | 627 | 0 | 0 | 0 | M34 |
| ↳ ↳ Pimsleur::Spanish (Latin America)::Level 5 | 1,247 | 1,247 | 1,247 | 1,247 | 0 | 0 | 0 | M34 |
| ↳ Pimsleur::Swedish | 0 | 0 | 610 | 610 | 0 | 0 | 0 | — |
| ↳ ↳ Pimsleur::Swedish::Level 1 | 610 | 610 | 610 | 610 | 0 | 0 | 0 | M35 |

## Generated note-model catalog

The model code is used in the deck-tree table. Full per-deck use remains in the JSON output to keep this catalog readable.

| Code | Note model (ID) | Notes | Cards | Mature | Fields in stored order | Templates |
|---|---|---:|---:|---:|---|---|
| M01 | China Province (1887298010) | 34 | 204 | 0 | Key · NameEn · Pinyin · Chinese · Abbr · TypeLabel · Region · CapitalEn · CapitalPin · CapitalZh · PopNote · MapImg · HeaderBlock · CapitalBlock · History · Landmarks · Economy | 1-map-to-province · 2-province-to-capital · 3-capital-to-province · 4-province-to-history · 5-province-to-landmarks · 6-province-to-economy |
| M02 | ChinesePod Phrase v3 (EN→ZH, TTS front) (1820115014) | 656 | 656 | 12 | PhraseId · Speaker · Hanzi · Pinyin · English · EnglishAudio · ChineseAudio · Source | English → Mandarin |
| M03 | ChinesePod Word v3 (EN→ZH, TTS front) (1820115015) | 1,920 | 1,915 | 0 | WordId · Hanzi · Pinyin · English · EnglishAudio · ChineseAudio · Source | English → Mandarin |
| M04 | Idiomatic Cloud Card v1 (1820120000) | 201 | 201 | 0 | PhraseId · Phrase · English · StructuredHTML · ExamplesHTML · FrontAudio · BackAudio · Source | Idiom |
| M05 | Idiomatic Cloud Card v2 (1820120100) | 5,312 | 5,312 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source · StructuredHtml | Idiom practice |
| M06 | Idiomatic Exercises v1 (1820150001) | 1,772 | 3,544 | 0 | ItemId · Lang · Topic · Category · EN · TL · Alts · Register · Trap · ExampleTL · ExampleEN · ClozeFront · AudioTL · AudioExample · Extra1 · Extra2 · Extra3 | Production · Cloze |
| M07 | Idiomatic Grammar Drill v1 (1820130001) | 895 | 895 | 0 | ItemId · Lang · Topic · TenseLabel · Symbol · Sentence · Answer · SentenceFull · GlossEn · Why · Extra1 · Extra2 · Extra3 · Extra4 | Drill |
| M08 | Idiomatic Podcast Lesson v1 (1820140001) | 40 | 40 | 0 | LessonId · Episode · Seq · Lang · FrontHTML · BackHTML · FrontAudio · BackAudio · FrontImage · BackImage · Extra1 · Extra2 · Extra3 · Extra4 | Lesson |
| M09 | Idiomatic Rescue Comics v1 (1738264931) | 10 | 10 | 0 | ItemId · Lang · Idiom · Gloss · SentenceFront · SentenceBack · Image | Produce |
| M10 | Idiomatic Tenses Exercises v1 (1820170002) | 85 | 85 | 0 | ItemId · Lang · Verb · Gloss · Tense · Pronoun · Form · EN · TL · TLBlank · Paradigm · Trap · Fork · History · AudioAnswer · AudioSentence · Extra1 · Extra2 | Fill |
| M11 | Idiomatic Tenses v1 (1820170001) | 85 | 85 | 0 | ItemId · Lang · Verb · Gloss · Tense · Pronoun · Form · EN · TL · TLBlank · Paradigm · Trap · Fork · History · AudioAnswer · AudioSentence · Extra1 · Extra2 | Produce |
| M12 | Idiomatic Translation v1 (1820160001) | 732 | 732 | 0 | ItemId · Lang · Topic · TenseLabel · Symbol · EnText · EnAudio · TlHTML · TlAudio · Why · Extra1 · Extra2 · Extra3 · Extra4 | Translate |
| M13 | Lex-Stage Mnemo v0 (1820130000) | 18 | 28 | 0 | ItemId · Lemma · Gloss · Track · Concept · LearnFront · LearnBack · RetrieveFront · RetrieveBack · BleepFront · BleepBack | Learn · Retrieve · Bleep |
| M14 | Mandarin Actor (1887294010) | 55 | 55 | 45 | Trigger · Name · Photos | Sound → Actor |
| M15 | Mandarin Character - Video (1908275002) | 222 | 222 | 1 | Character · Pinyin · Meaning · Video | Character → Video |
| M16 | Mandarin Location (1887295010) | 13 | 13 | 0 | Ending · Name · Zones | Ending → Location |
| M17 | Mandarin Palace Learning (51379758807003) | 339 | 339 | 0 | Sort · Front · Comic · Back | Card 1 |
| M18 | Mandarin Phrase Mastery v1 (1820115000) | 0 | 0 | 0 | PhraseId · Hanzi · Pinyin · English · WordTable · Construction · Example1Hanzi · Example1Pinyin · Example1En · Example2Hanzi · Example2Pinyin · Example2En · Example3Hanzi · Example3Pinyin · Example3En · FrontAudio · BackAudio · Source · PickReason | Mandarin phrase |
| M19 | Mandarin Phrase Mastery v3 (audio-first) (1820115002) | 7 | 7 | 0 | PhraseId · Hanzi · Pinyin · English · FrontAudio · LessonAudio · Source | Mandarin phrase v3 |
| M20 | Mandarin Phrase Mastery v3.1 (audio-first + visual ref) (1820115003) | 22 | 36 | 0 | PhraseId · Hanzi · Pinyin · English · VocabTable · ConstructionPattern · ConstructionWalkthrough · ConstructionPitfall · ExamplesBlock · FrontAudio · LessonAudio · Source | Mandarin phrase v3.1 · Mandarin phrase v3 |
| M21 | Mandarin Prop (1887293010) | 589 | 589 | 579 | Character · Pinyin · EnName · RuName · Video · Composite | Character → Video + Images |
| M22 | Mandarin Prop - Images (1887293003) | 5 | 5 | 2 | Character · Pinyin · EnName · RuName · Composite | Character → Images |
| M23 | Mandarin Prop - Video (1887293002) | 5 | 5 | 2 | Character · Pinyin · EnName · RuName · Video | Character → Video |
| M24 | Mandarin Zone (1887296010) | 65 | 65 | 0 | Ending · ToneLabel · LocationName · TargetZone · OtherZones | Ending+Tone → Zone |
| M25 | Pimsleur Danish (EN→DA) (1808132000) | 612 | 612 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → DA |
| M26 | Pimsleur Dutch (EN→NL) (1808129000) | 609 | 609 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → DU |
| M27 | Pimsleur French (EN→FR) (1808128000) | 4,693 | 4,693 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → FR |
| M28 | Pimsleur German (EN→DE) (1808125000) | 5,311 | 5,311 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → GE |
| M29 | Pimsleur Italian (EN→IT) (1808127000) | 5,344 | 5,344 | 498 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → IT |
| M30 | Pimsleur Mandarin (EN→ZH) (1808123000) | 3,043 | 3,043 | 1,278 | English · Hanzi · Pinyin · EnglishAudio · MandarinAudio · Lesson · Source | EN → ZH |
| M31 | Pimsleur Norwegian (EN→NO) (1808130000) | 1,216 | 1,216 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → NO |
| M32 | Pimsleur Portuguese (EN→PT) (1808124000) | 4,344 | 4,344 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → PO |
| M33 | Pimsleur Spanish (EN→ES) (1808126000) | 4,378 | 4,378 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → SP |
| M34 | Pimsleur Spanish — Latin America (EN→ES) (1808133000) | 4,051 | 4,051 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → SP |
| M35 | Pimsleur Swedish (EN→SV) (1808131000) | 610 | 610 | 0 | English · Target · Transliteration · EnglishAudio · TargetAudio · Lesson · Source | EN → SW |
| M36 | YouTube Audio Phrase (1820114000) | 0 | 0 | 0 | PhraseId · Portuguese · English · TargetAudio · EnglishAudio · Source · Target | PT audio → EN · Target audio → EN |
| M37 | YouTube Audio Phrase Reverse v1 (1820114400) | 6 | 6 | 0 | PhraseId · Target · English · EnglishAudio · ReverseBackAudio · Source | English → Target (interleaved) |
| M38 | YouTube Audio Phrase v2 (1820114100) | 0 | 0 | 0 | PhraseId · Target · English · TargetAudio · EnglishAudio · Source | Target audio → EN |
| M39 | YouTube Audio Phrase v3 (1820114200) | 188 | 188 | 12 | PhraseId · Target · English · TargetAudio · BackAudio · Source | Target audio → EN (interleaved) |
| M40 | YouTube Expression Pool v1 (1820114700) | 20,231 | 20,231 | 1,577 | English · Target · EnglishAudio · TargetAudio · Idiom · IdiomEn · Source | EN → target |
| M41 | YouTube Idiom Audio EN→Target v1 (1820114801) | 3,276 | 6,064 | 324 | Target · English · FrontAudio · BackAudio · Source | EN audio → target audio · EN → target |
| M42 | YouTube Idiom Audio Target→EN v1 (1820114800) | 3,381 | 6,565 | 255 | Target · English · FrontAudio · BackAudio · Source | target audio → EN audio · target → EN |
| M43 | YouTube Idiom Card v1 (1820114500) | 0 | 0 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice |
| M44 | YouTube Idiom Card v2 (1820114600) | 171 | 171 | 10 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice |
| M45 | YouTube Idiom Card v2 (ElevenLabs Flash) (1820114603) | 0 | 0 | 0 | Idiom · IdiomEn · Explanation · Example1En · Example2En · Example3En · Example4En · Example5En · Example6En · Example1Tg · Example2Tg · Example3Tg · Example4Tg · Example5Tg · Example6Tg · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source · Example1Target · Example6Target · Example3Target · IdiomId · Example4Target · Example2Target · Example5Target | Idiom practice (Flash) |
| M46 | YouTube Idiom Card v2 (Gemini Flash TTS) (1820114604) | 12 | 12 | 0 | Idiom · IdiomEn · Explanation · Example1En · Example2En · Example3En · Example4En · Example5En · Example6En · Example1Tg · Example2Tg · Example3Tg · Example4Tg · Example5Tg · Example6Tg · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source · Example1Target · Example6Target · Example3Target · IdiomId · Example4Target · Example2Target · Example5Target | Idiom practice (Gemini Flash) |
| M47 | YouTube Idiom Card v2 (Piper) (1820114602) | 1 | 1 | 0 | Idiom · IdiomEn · Explanation · Example1En · Example2En · Example3En · Example4En · Example5En · Example6En · Example1Tg · Example2Tg · Example3Tg · Example4Tg · Example5Tg · Example6Tg · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source · Example1Target · Example6Target · Example3Target · IdiomId · Example4Target · Example2Target · Example5Target | Idiom practice (Piper) |
| M48 | YouTube Idiom Card v3 Structured (de) (1820114900) | 47 | 47 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M49 | YouTube Idiom Card v3 Structured (es) (1820114704) | 32 | 32 | 3 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M50 | YouTube Idiom Card v3 Structured (es)+ (1820114904) | 48 | 48 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M51 | YouTube Idiom Card v3 Structured (fr) (1820114701) | 32 | 32 | 16 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M52 | YouTube Idiom Card v3 Structured (fr)+ (1820114901) | 0 | 0 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M53 | YouTube Idiom Card v3 Structured (it) (1820114702) | 23 | 23 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M54 | YouTube Idiom Card v3 Structured (it)+ (1820114902) | 16 | 16 | 0 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M55 | YouTube Idiom Card v3 Structured (pt) (1820114703) | 17 | 17 | 7 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |
| M56 | YouTube Idiom Card v3 Structured (pt)+ (1820114903) | 31 | 31 | 2 | IdiomId · Idiom · IdiomEn · Explanation · Example1En · Example1Target · Example2En · Example2Target · Example3En · Example3Target · Example4En · Example4Target · Example5En · Example5Target · Example6En · Example6Target · SourcePhrase · SourceEn · FrontAudio · BackAudio · Source | Idiom practice (Structured) |

## Generated tag summary

| Taxonomy bucket | Note-tag assignments |
|---|---:|
| hierarchical::hsk | 225 |
| hierarchical::idiomatic | 10 |
| hierarchical::idiomatic-exercises | 1,772 |
| hierarchical::idiomatic-fossil | 40 |
| hierarchical::idiomatic-podcast | 40 |
| hierarchical::idiomatic-tenses | 170 |
| hierarchical::lang | 10 |
| hierarchical::region | 34 |
| hierarchical::tier | 339 |
| hierarchical::type | 34 |
| hierarchical::unlock | 339 |
| language | 33,433 |
| lesson | 36,787 |
| level | 34,211 |
| other-flat | 76,781 |
| system/family | 105,811 |
| video-slug-like | 534 |
| youtube-id-like | 2,785 |

Top 200 tags:

| Tag | Notes |
|---|---:|
| pimsleur | 34,211 |
| youtube | 33,054 |
| quickmatch | 20,860 |
| fluency-pool | 20,231 |
| flashcard | 13,351 |
| it | 8,549 |
| level-5 | 8,174 |
| level-4 | 7,549 |
| level-1 | 7,222 |
| idiom-audio | 6,657 |
| de | 6,410 |
| pt | 5,696 |
| level-2 | 5,653 |
| level-3 | 5,613 |
| italian | 5,344 |
| german | 5,311 |
| fr | 5,113 |
| french | 4,693 |
| es | 4,593 |
| spanish | 4,378 |
| portuguese | 4,344 |
| spanish-latam | 4,051 |
| t2e | 3,381 |
| e2t | 3,276 |
| mandarin | 3,043 |
| idiomatic-pool | 2,849 |
| idiomatic-cloud | 2,664 |
| chinesepod | 2,576 |
| vocab | 1,920 |
| idiomatic-exercises | 1,772 |
| norwegian | 1,216 |
| lesson-25 | 1,193 |
| lesson-15 | 1,182 |
| lesson-20 | 1,168 |
| lesson-10 | 1,163 |
| lesson-13 | 1,156 |
| lesson-21 | 1,156 |
| lesson-19 | 1,153 |
| lesson-26 | 1,152 |
| lesson-16 | 1,149 |
| lesson-05 | 1,147 |
| lesson-23 | 1,145 |
| lesson-24 | 1,142 |
| lesson-11 | 1,141 |
| lesson-28 | 1,141 |
| lesson-18 | 1,140 |
| lesson-22 | 1,139 |
| lesson-06 | 1,134 |
| lesson-14 | 1,134 |
| lesson-29 | 1,133 |
| lesson-12 | 1,132 |
| lesson-27 | 1,132 |
| lesson-30 | 1,132 |
| lesson-08 | 1,130 |
| lesson-17 | 1,127 |
| lesson-01 | 1,124 |
| lesson-02 | 1,117 |
| lesson-03 | 1,116 |
| lesson-04 | 1,113 |
| lesson-09 | 1,112 |
| lesson-07 | 1,108 |
| idiomatic-grammar | 895 |
| idiomatic-translation | 732 |
| danish | 612 |
| swedish | 610 |
| dutch | 609 |
| idiom | 430 |
| tier::core | 339 |
| gemini-flash | 258 |
| structured | 258 |
| unlock::0100 | 214 |
| idiomatic-exercises::es::connecting | 207 |
| idiomatic-exercises::it::connecting | 201 |
| idiomatic-exercises::fr::connecting | 191 |
| idiomatic-exercises::de::connecting | 179 |
| idiomatic-exercises::pt::connecting | 175 |
| idiomatic-tenses | 170 |
| idiomatic-exercises::es::conditionals | 168 |
| idiomatic-exercises::it::conditionals | 166 |
| idiomatic-exercises::de::conditionals | 163 |
| idiomatic-exercises::fr::conditionals | 162 |
| idiomatic-exercises::pt::conditionals | 160 |
| unlock::0050 | 125 |
| trump-verlngert-waffenruhe-folgen-verhandlungen-zwischen-usa | 85 |
| lesson-B0283 | 82 |
| lesson-B1591 | 72 |
| lesson-1307 | 72 |
| lesson-1323 | 72 |
| hsk::7 | 66 |
| lesson-B1436 | 64 |
| lesson-1394 | 62 |
| lesson-1795 | 62 |
| lesson-1868 | 62 |
| lesson-2611 | 62 |
| lesson-1282 | 60 |
| lesson-2355 | 60 |
| lesson-2666 | 60 |
| lesson-1504 | 58 |
| lesson-1550 | 58 |
| lesson-1852 | 58 |
| lesson-B1173 | 56 |
| lesson-B0341 | 56 |
| lesson-B0801 | 54 |
| lesson-B1725 | 54 |
| lesson-B1228 | 54 |
| lesson-1860 | 54 |
| lesson-2136 | 54 |
| lesson-B1248 | 52 |
| lesson-0773 | 52 |
| lesson-2301 | 52 |
| lesson-B0379 | 50 |
| lesson-B1109 | 50 |
| lesson-1187 | 50 |
| lesson-B0980 | 50 |
| lesson-1621 | 50 |
| hsk::2 | 50 |
| erstmals-militr-strategie-pistorius-will-bundeswehr-strken-t | 48 |
| lesson-2365 | 48 |
| lesson-2720 | 46 |
| lesson-2985 | 46 |
| lesson-3089 | 44 |
| lesson-2707 | 44 |
| pt_gender_core | 44 |
| lesson-0549 | 42 |
| lesson-0127 | 42 |
| lesson-0463 | 42 |
| lesson-2585 | 42 |
| es_cmd_tu | 42 |
| lesson-B0177 | 40 |
| lesson-B0371 | 40 |
| lesson-B0170 | 40 |
| lesson-0072 | 40 |
| lesson-0129 | 40 |
| idiomatic-podcast | 40 |
| lesson-B1080 | 38 |
| lesson-2468 | 38 |
| de_prep_wechsel | 38 |
| hsk::1 | 37 |
| lesson-3053 | 36 |
| lesson-2451 | 36 |
| de_gender | 36 |
| fr_present_irreguliers | 36 |
| pt_futuro_subjuntivo | 36 |
| pt_preterito_perfeito | 36 |
| it_congiuntivo_presente | 36 |
| it_passato_remoto | 36 |
| provinces | 34 |
| es_clitics_selo | 34 |
| fr_passe_compose | 34 |
| ortografia | 31 |
| lesson-B0453 | 30 |
| lesson-0101 | 30 |
| de_prep_fest | 30 |
| it_passato_prossimo | 30 |
| fr_quantites_de | 30 |
| audio-first | 29 |
| bbc-news | 29 |
| phrase-mastery | 29 |
| zh | 29 |
| furtinho | 28 |
| hollywood-regisseur-emmerich-zu-den-chancen-von-ki-in-der-fi | 28 |
| idiomatic-tenses::pt::vir | 28 |
| ciumes-do-uber | 27 |
| limesreplay-caracciolo-a-in-altre-parole-hormuz-islamabad-e- | 24 |
| sanchez-responde-al-plan-del-pentagono-de-espana-en-la-otan- | 24 |
| plan-de-trump-para-escoltar-buques-en-ormuz-no-avanza | 24 |
| es_condicional | 24 |
| es_futuro | 24 |
| es_imperfecto | 24 |
| es_perfecto | 24 |
| es_preterito | 24 |
| es_subj_pres | 24 |
| es_cmd_neg | 24 |
| es_cmd_usted | 24 |
| es_cond_perf | 24 |
| es_plusc_subj | 24 |
| es_clitics_ind | 24 |
| es_por_para | 24 |
| es_verb_prep | 24 |
| fr_imparfait | 24 |
| fr_subjonctif_present | 24 |
| pt_condicional_presente | 24 |
| pt_futuro_simples | 24 |
| pt_preterito_imperfeito | 24 |
| pt_subjuntivo_presente | 24 |
| it_futuro_semplice | 24 |
| it_imperfetto | 24 |
| it_genere_plurali | 24 |
| fr_pronoms_y_en | 24 |
| fr_genre_noyau | 24 |
| es_ser_estar | 24 |
| hsk::3 | 24 |
| type::province | 23 |
| 5rcms10g6h4 | 23 |
| v3.1 | 22 |
| es_pres_irreg | 22 |
| es_subj_imp | 22 |
| es_clitics_dir | 22 |
| fr_conditionnel_present | 22 |
| fr_futur_simple | 22 |
