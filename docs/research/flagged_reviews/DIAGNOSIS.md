# Flagged European reviews — Phase 1 diagnosis

Date: 2026-08-12

Scope: the 17 notes in `flagged_euro_full.json` only

Status: diagnosis only; no database, media, Anki, or source-data mutation was performed

## Result

| Defect class | Count |
|---|---:|
| (a) Missing/empty audio field | 0 |
| (b) Audio present but wrong/truncated | 13 |
| (c) Target-language error in text | 3 |
| (d) Other | 1 |
| **Total** | **17** |

Every note has a non-empty Anki sound field: both audio fields on all 13 pool
notes and `Extra1` on all four grammar notes. Category (a) is therefore ruled
out at the card-field level. The media files and live database are unavailable
in this sandbox. Where the text is sound, category (b) is the operational
diagnosis: the owner flag is treated as evidence that the referenced clip is
wrong, truncated, or inaudible, and the clip is queued for re-TTS in Phase 2.
The exact pool-row/audio-path lookup for every pool note is in the corresponding
`verify_sql` field of `diagnosis.json`.

## Identity and DB mapping

All 17 supplied GUIDs were independently recomputed and match.

- Pool notes use
  `sha1("yt-pool::<norm(Idiom)>::<norm(Target)>")[:16]`. The offline DB key is
  therefore `(lang, idiom_text, target_text)` across
  `expression_idioms JOIN expression_examples`. The two numeric IDs are
  `BIGSERIAL` values and cannot truthfully be derived without the live DB, so
  `diagnosis.json` leaves them `null`, records the complete derived key, and
  supplies exact SQL that resolves both IDs and both stored example-audio paths.
  The SQL repeats the pool eligibility filters from `pool.py`, avoiding
  video-less adopted duplicates.
- Grammar notes expose `ItemId` as field 0 and use
  `sha1("idiomatic-grammar::<lang>::<ItemId>")[:16]`. Their DB IDs are therefore
  directly mapped to `grammar_items.id`: 400, 406, 789, and 1066.
- Grammar audio paths are not DB columns. They are deterministic filesystem
  paths from `grammar/audio.py`:
  `staged_audio/grammar/it/idg_it_<ItemId>.mp3`.

## Per-note diagnosis

| Note ID | DB row/key | Diagnosis | Proposed Phase 2 action |
|---:|---|---|---|
| 1776916081194 | `expression_examples` via `it / fare una figuraccia / Sono caduto…` | **(b)** Both sound tags exist; no unambiguous text defect. | Resolve with `verify_sql`, null both example audio paths, re-TTS both sides, rebuild IT pool. |
| 1777193962126 | `expression_examples` via `it / fruire di / Abbiamo fruito…` | **(b)** Both sound tags exist; `fruire di uno sconto` is grammatical, if formal. | Resolve, null both audio paths, re-TTS, rebuild IT pool. |
| 1777193963003 | `expression_examples` via `it / guarda caso / Guarda caso…` | **(b)** Both sound tags exist; sentence and expression agree. | Resolve, null both audio paths, re-TTS, rebuild IT pool. |
| 1777442639125 | `expression_examples` + `expression_idioms` via `es / palanquear / Están palanqueando…` | **(c)** The sentence uses `palanquear` as a direct equivalent of “leverage technology.” The DLE limits it to literal levering or, regionally, using personal influence; the latter regional list does not include Mexico. | Native-speaker gate the intended regional sense. Replace the example with a supported use or correct the expression/sentence (`aprovechar` or `apalancarse en`), re-TTS, rebuild ES pool, and explicitly handle the changed GUID. |
| 1783832893433 | `expression_examples` via `pt / fora de sintonia / Depois de tantos…` | **(b)** Both sound tags exist; the European-Portuguese construction is coherent. | Resolve, null both audio paths, re-TTS, rebuild PT pool. |
| 1783832893587 | `expression_examples` via `pt / cria ruídos / Mudar as regras…` | **(b)** Both sound tags exist; infinitive `criar` is a legitimate inflected use of the stored expression. | Resolve, null both audio paths, re-TTS, rebuild PT pool. |
| 1783832893597 | `expression_examples` via `pt / jogo combinado / A polícia…` | **(b)** Both sound tags exist; `jogo combinado` is attested for a fixed/manipulated match and fits this sports context. | Resolve, null both audio paths, re-TTS, rebuild PT pool. |
| 1783832893599 | `expression_examples` via `pt / jogo combinado / Nós perdemos o jogo de tabuleiro…` | **(c)** Semantic/context mismatch: a “secret pre-arranged deal” in a board game is rendered as the sports sense “fixed match,” with the unnatural `fizeram um jogo combinado`. | Replace with a natural fixed-match example, re-TTS, rebuild PT pool, and explicitly retire/migrate the old GUID. |
| 1783832893601 | `expression_examples` via `pt / jogo combinado / Não adianta…` | **(b)** Both sound tags exist; the collusion/setup sense is coherent. | Resolve, null both audio paths, re-TTS, rebuild PT pool. |
| 1783832893603 | `expression_examples` via `pt / abrir garrafas de champanhe / Não comemore…` | **(d)** The target is valid, but the English front is tautological: “celebrate … celebrate prematurely.” | Rewrite the English as “Don't celebrate before the final whistle; it's still too early to open the champagne.” Re-TTS only English and rebuild PT pool; GUID stays stable. |
| 1783834552882 | `expression_examples` via `es / una vez atravesada / Una vez atravesada…` | **(b)** Both sound tags exist; the absolute-participle construction agrees with `la línea`. | Resolve, null both audio paths, re-TTS, rebuild ES pool. |
| 1783834552886 | `expression_examples` + `expression_idioms` via `es / damos la curva / …al dar la curva` | **(c)** Wrong vehicle collocation. FundéuRAE gives `tomar una curva`; `dar la curva` does not mean “round the bend.” | Correct idiom and target to `tomar la curva`, re-TTS, rebuild ES pool, and explicitly retire/migrate the old GUID. |
| 1783834552902 | `expression_examples` via `es / llena hasta la bandera / En hora punta…` | **(b)** Both sound tags exist; agreement and capacity idiom are coherent. | Resolve, null both audio paths, re-TTS, rebuild ES pool. |
| 1785311850951 | `grammar_items.id = 400` | **(b)** `date` is the correct 2nd-person-plural present of `dare`; `dare` is in the unit's verb inventory. The sound tag exists. | Preserve text; regenerate `idg_it_400.mp3`, rebuild IT grammar deck. |
| 1785311850963 | `grammar_items.id = 406` | **(b)** `salite` is correct; `salire` is explicitly in the unit's irregular-verb inventory because of its singular/3rd-plural stem contrast. The sound tag exists. | Preserve text; regenerate `idg_it_406.mp3`, rebuild IT grammar deck. |
| 1785520109601 | `grammar_items.id = 789` | **(b)** The noun bank specifies feminine `opinione` with singular article `l'`; the answer is correct. The sound tag exists. | Preserve text; regenerate `idg_it_789.mp3`, rebuild IT grammar deck. |
| 1785722813973 | `grammar_items.id = 1066` | **(b)** The reggenza bank specifies `riuscire a + infinito`; the answer is correct. The sound tag exists. | Preserve text; regenerate `idg_it_1066.mp3`, rebuild IT grammar deck. |

Language references used for the two Spanish findings:

- [RAE/ASALE DLE: *palanquear*](https://dle.rae.es/palanquear)
- [FundéuRAE: *tomar una curva*, no *negociarla*](https://www.fundeu.es/recomendacion/tomar-una-curva-mejor-que-negociarla/)

## Phase 2 cautions

1. Run each `verify_sql` query before mutation and require exactly one eligible
   pool row. A zero- or multi-row result is a mapping failure, not permission to
   broaden an update.
2. Re-TTS both sides for category (b) pool notes because the dump cannot show
   which referenced clip failed. For the English-only category (d) correction,
   only `audio_en` needs replacement.
3. A pool target or idiom text change changes the GUID. The three category (c)
   fixes therefore cannot be treated as GUID-stable in-place Anki updates; Phase
   2 must explicitly retire/reconcile the old note and introduce the corrected
   note without silently orphaning the owner's scheduling state.
4. Do not clear any flag until the rebuilt card has landed in Anki and the owner
   has verified the replacement.
