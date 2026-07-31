# Learner Error Profile — Spanish (es)

> Mined 2026-07-31 from teacher-marked 1:1 lesson data, 2019–2024.
> Spanish is the RICHEST dataset of the five (1,693 items over ~6 years,
> no coverage gap) but has one structural caveat: only **62 rows carry
> the learner's verbatim wrong form**. Everything else is
> teacher-recorded *target* language (corrections whose wrong side went
> unrecorded, plus vocab expansion). Frequency claims below therefore
> mix two signals: hard error counts (n=62) and *reteach recurrence* —
> the same item being taught again and again across years, which for an
> advanced learner in year 5 is itself error/fossilization evidence.

## 1. Data inventory

| Source | Rows | With verbatim error | vocab flag | use flag | pron flag |
|---|---|---|---|---|---|
| `xlsx_es.jsonl` (2019-03 → 2022-11) | 1,389 | **62** | 656 | 713 | 11 |
| `teachee_es.jsonl` (2022-11 → 2024-12) | 304 notes / 39 lessons | **0** | ~304 (all) | — | IPA fragments on ~10 notes |

- Flag anatomy of the xlsx: use∧error = 55, vocab∧error = 6, unflagged∧error = 1
  (Σ 62 verbatim pairs); use without error = 658; vocab without error = 650;
  pron = 11 (one also use-flagged); 10 rows carry no flag at all.
- Date quality: 14 rows have `date=null`; 4 rows say `2010-08-01`
  (obvious typo for 2020-08-01 — neighbors are all Aug 2020); 15 rows use
  `13/2/2020` (unpadded). Continuous weekly coverage otherwise:
  2019: 544 rows, 2020: 310, 2021: 295, 2022: 207 (xlsx) → Teachee picks
  up Nov 2022 and runs to Dec 2024 with no gap. **This is the only
  language with 2023–2024 coverage.**
- Teachee note shape: `[EN prompt, ES answer(+partial IPA)]` for ~87
  notes; ~217 later notes are ES-only fluency sentences (EN field holds
  the duplicated ES text). None mark a wrong form — from Nov 2022 on the
  teacher stopped recording what the learner actually said, so the
  error taxonomy leans on 2019–2022, and 2023–24 contributes only
  reteach-recurrence and pronunciation signal.
- Teacher is Colombian (variety markers all over the data: *el
  computador, digitar, monitorear, los tips, riesgoso, los viáticos, el
  eje cafetero, la OTAM*). Generated drill sentences should stay
  LatAm-neutral; don't "correct" these to peninsular forms.

## 2. Grammar error taxonomy (n = 62 verbatim pairs, ranked)

Categories assigned by hand over all 62 pairs; a pair can count in two
categories when the error is genuinely double (e.g. *un otro ciudad* =
un otro calque + gender). Quotes verbatim (`error` → `correct`).

**1. Cross-Romance / English interference — 26/62 (42%).** The learner
studies pt, it, fr in parallel and imports word-forms wholesale. By
source language: Portuguese ≈ 14, Italian ≈ 6, English/French ≈ 6.
NO existing unit covers this — see §6.
- `inserir` → `insertar` — **twice** (2022-04-21, 2022-09-30), and
  *insertar* was (re)taught **16 times, 2019→2024**, the single most
  retaught item in the dataset (pt *inserir*).
- `quisemos` → `quisimos` (2021-10-25; pt *quisemos* is the correct
  1pl preterite in Portuguese — pure paradigm bleed)
- `exemplo` → `ejemplo` (pt), `longo` → `largo` (pt), `chines` →
  `chino` (pt), `isolado` → `aislado` (pt), `conosco` → `con nosotros`
  (pt), `holandês` → `holandesa` (pt), `financeiras` → `financieras`
  (pt), `pasaporto` → `pasaporte` (it), `Berlino` → `Berlín` (it),
  `nostro` → `nuestro` (it), `semplice` → `simple` (it),
  `resercar` → `investigar` (it *ricercare*), `critical` → `crítica/
  crítico` (en), `avergonzante` → `vergonzoso` (fr *embarrassant*-style
  coinage), `un otro ciudad` → `otra ciudad` (it *un altro* / fr *un
  autre*; Spanish takes bare *otro*)
- Derivational miscoins on Romance/English patterns: `la dictación` →
  `el dictado`, `la consumación` → `el consumo`, `similaridades` →
  `las similitudes`, `profundido` → `profundo`, `extensiva` → `muy
  extensa`, `cualidad` → `la calidad` (quality-of-output sense),
  `restar` → `anular / cancelar`, `mensales` → `mensuales`,
  `veros` → `verdaderos`, `investieron` → `invirtieron` (pt/it
  *investiram/investirono* — no e→ie diphthong).

**2. muy vs mucho — 7/62, both directions, 2019→2022.** The one error
the strategy doc already knew about (`mucho de moda`) is the tip of a
real cluster:
- `mucho de moda` → `muy de moda`; `mucho dificil` → `muy difícil`;
  `mucho importante` → `muy importante`; `mucho profesional` → `muy
  profesional` (adjective side, all 2019)
- `muy tráfico` → `Hubo mucho tráfico` (2019); `muy frio` → `mucho
  frío` (2019); `muy` → `hacía mucho calor` (2022-04-14 — still live
  in year 4; *mucho calor* retaught again 2022-07 and correct in
  Teachee 2023, so trending fixed but drill-worthy)

**3. Motion/location preposition (a vs en vs para) — 7/62, all
2019.** Portuguese uses *em* for arrival-location and *para* for
destination; the learner mapped both into Spanish:
- `viajar para` → `viajar a un lugar` (pt *viajar para*)
- `fui en Londres` → `me fui a Londres`; `me voy en` → `en tres días
  voy a Francia`; `regreso en` → `yo regreso a Italia`; `llegue en` →
  `cuando llegue a ...`
- Reverse direction: `una noche a` → `pasar una noche en ...` (fr/it
  *à/a* for location)
- `en` → `seguimos a cualquier parte del mundo`
- Not observed after 2019 in the (thin) error record; Teachee 2023 has
  correct *viajar a Noruega*, *he pasado tres días en Bélgica*. Treat
  as fossilization-risk, not active fire.

**4. Verb morphology (strong preterites & stem changes) — 5/62.**
- `pune` → `yo puse` (2019); `investieron` → `invirtieron` (2019);
  `quisemos` → `quisimos` (2021); `me fue` → `me fui a Francia` (2019)
- `yo no fue*` → `Yo no iba hace un año` (2019 — person error AND
  preterite-for-imperfect selection in one)

**5. Light-verb collocation calques — 3/62 + strong recurrence.**
- `hacer estas decisiones` → `tomar estas decisiones` (2019; en "make
  decisions" / pt *tomar* exists but the learner said *hacer*);
  *tomar decisiones* retaught 2022-03; *la toma de decisiones* 2019,
  2021 — 4 touches over 4 years
- `hacer` → `tomar fotos` (2019)
- `hacer errores` → `cometer errores` (2020-08); *cometer un error*
  taught 2019 AND drilled again in Teachee 2022-11 (*Sí yo cometo un
  error*) — 3 touches over 4 years

**6. Fixed-phrase prepositions — 3/62.**
- `sobre control` → `tener algo bajo control` (2021-03-13) and
  **verbatim again** `sobre control` → `tengo todo bajo control`
  (2022-10-07); *bajo control* then drilled in Teachee 2024-03
  (*Tenemos todo bajo control*) — the cleanest fossilization specimen
  in the dataset (en "over control"/"under control" mapping)
- `al fin` → `al final va a costar mucho menos` (2019)

**7. Gender / article — 4/62 direct** (+ systemic evidence).
- `esta carga` → `este cargo` (position vs load); `la dictación` → `el
  método del dictado`; `la consumación` → `el consumo`; `un otro
  ciudad` → `en otra ciudad`
- Systemic: a whole lesson row-pair on 20/06/2019 — `"La" "el"
  sustantivos masculinos o femeninos` and `"Lo" (adjetivos, posesivos o
  verbos en participio)` — plus the teacher's habit of recording nearly
  every noun WITH its article (≈600 of 656 vocab rows) says gender was
  worked constantly even when errors weren't logged. `Los dosis`
  (2021-05-15, vocab row) may record a live gender error (la dosis).

**8. Clitic pronouns — 1/62 but high-value.**
- `quiero comprar le lo` → `Quiero comprárselo / Se lo quiero comprar`
  (2022-07-29) — the textbook le+lo→se lo failure, in year 4. Same
  lesson taught the full mini-paradigm (*comprarle un carro a mi hijo /
  comprarlo para mi hijo / Lo quiero*), i.e. the teacher treated it as
  a gap, not a slip. Directly validates `es_clitics_selo`.

**9. One-offs — ser/estar, polarity, numerals, spelling — 6/62.**
- `ser en contacto` → `estar en contacto` (2019) — the ONLY ser/estar
  error in six years of data
- `también` → `Mi esposa tampoco` (2019, negative-polarity *tampoco*)
- `cinco cientos` → `quinientos metros` (2019); hundreds stayed shaky:
  *quinientos* (re)taught 2019 use + 2019 (500 términos), misspelled
  `quinnientos` in the 2022 vocab log, drilled in Teachee 2023
  (*Quinientos mil dólares*, *doscientas entrevistas*, *setecientas
  páginas*, *mil novecientos sesenta y dos* 2022)
- Pure spelling/performance slips (excluded from all category counts
  above): `necetarias`, `patrolcinado`

**Explicitly ABSENT from the error record** (relevant given the
existing curriculum): subjunctive selection (0 errors; plenty of
correct triggered examples taught: *espero que... no nos desilucione*,
*el riesgo de que... envíe*, *que no se vendan los derechos*),
por/para (0 pure confusions — the one *para* error is the pt
destination calque above), future/conditional forms (0), compound
tenses (0 — Teachee shows fluent *he estado estructurando*, *hubo*,
*habría*-free but correct usage), commands (0 — but the corpus is
podcast/work narration; imperatives simply never occur in it, so this
is absence of evidence).

## 3. Recurring structural patterns (fossilization candidates)

Ranked by (recurrence × span of years). "Touches" counts errors +
reteaches across xlsx and Teachee.

1. **pt *inserir* → insertar** — 16 touches, 2019/20/21/22/23/24; 2
   verbatim errors. The learner talks about Anki/software weekly.
2. **muy/mucho** — 7 verbatim errors 2019–2022, both directions.
3. **en/a/para after motion verbs** (ir/viajar/llegar/regresar a;
   pasar la noche en) — 7 errors in 2019, then apparently controlled.
4. ***sobre* control → *bajo* control** — same error verbatim 19
   months apart (2021→2022), drilled again 2024.
5. **hacer → tomar/cometer** (decisiones, fotos, errores) — 3 errors +
   reteaches spanning 2019→2022.
6. **Strong preterites & e→ie/e→i stems** (*pune, quisemos,
   investieron, me fue*) — 2019→2021; *invertir* itself touched 7×
   overall (plus *invertí - invertir* explicitly contrasted 2019).
7. **Hundreds & dates** — *cinco cientos*, *quinnientos*; *enero*
   taught 7× (2019/20/22/23); *el primero de mayo/junio* drilled
   2023/2024; *tres de octubre*, *hasta mediados de octubre* 2021.
8. **Portuguese lexical bleed set** (exemplo, longo, chines, isolado,
   conosco, holandês, financeiras, rolo) — 2019→2022, at least 8
   distinct items.
9. **Italian lexical bleed set** (semplice, nostro, Berlino, pasaporto,
   resercar) — 2019→2020.
10. **Derivational overgeneration** (dictación, consumación,
    similaridades, profundido, avergonzante, extensiva, mensales) —
    inventing Latinate forms instead of retrieving the Spanish one;
    2019→2022, 7 distinct coins.
11. **calidad vs cualidad** — error 2019, *la calidad* retaught 2019,
    2020-08, 2020-11 (pron-flagged), Teachee 2023 (*un audio que no fue
    de buena calidad*).
12. **le lo → se lo** clitic cluster (2022) — single but late-stage
    and paradigm-level.
13. **suscriptores morphology** — `sucriptores` (misspelled 2019),
    `suscritos` → `suscriptores` (2019), retaught 2020, Teachee 2024
    (*los enviamos a los suscriptores*).
14. **desilusionar family** — *desilucionada/desilucione* (teacher's
    own spelling wobbles) taught 3× in 2019, again Teachee 2023 (*me
    sentía un poco desilusionado*), 2024 (*Fue una desilusión*).
15. **tampoco after negation** — one error 2019; *tampoco* retaught
    2019 (*que tampoco ha sido publicado todavía*).
16. **ser/estar in fixed PPs** (*estar en contacto, estar de acuerdo,
    estar desconectado*) — 1 error + the teacher repeatedly logging
    estar-collocations (estoy muy en desacuerdo 2019, estar confundido
    2021, estar tranquilo 2021, estar de pie 2024).
17. **también/además/incluso cluster** — *incluso si* taught 3×
    (2019 ×2, 2021), *aún cuando* 2021 — concessives keep needing
    reinforcement.
18. **Reflexive-motion verbs** (*me fui*, *irse* vs *ir*) — error
    2019 (`me fue`), *ella se fue a Austria* taught 2019, *me voy en*
    2019.
19. **al final (de)** — error 2019 (*al fin*), then *al final* logged
    8× 2019–2023 including Teachee — high-frequency discourse marker
    the learner leans on.
20. **-ción gender is SAFE** (never one error) but -ción noun
    *formation* is not (dictación, consumación, anticipacióon,
    temporización for "timing") — the learner reaches for -ción when
    Spanish wants a different derivation.

## 4. Vocabulary profile (656 xlsx vocab rows + 304 Teachee notes)

Domains, by rough share of vocab+use teaching volume:
- **Current affairs / geopolitics** (~30%): elections, protests,
  coups (*el golpe de estado*), EU/NATO (*la OTAM*), 2020–21 pandemic
  (17 *vacuna\** touches, *confinamiento, cuarentena, mascarillas*),
  2022 war (*bombardeos, tanques, embajadas, exiliados, el paro*).
  Matches the idiom-pipeline channel mix — themed sentence generation
  is already aligned.
- **Media/podcast production** (~20%, grows over time; dominant in
  Teachee): *el guión, los suscriptores, el lanzamiento, grabar,
  los subtítulos, la transcripción, el bosquejo, las notas de pie de
  página, los efectos de sonido, la edición, el episodio, la audiencia,
  los derechos*.
- **Business/finance** (~15%): *los inversionistas, la inversión, el
  presupuesto, la bancarrota, los fondos especulativos, las tasas de
  interés, rentable, el monto, los viáticos, sin ánimo de lucro*.
- **Language-learning tooling** (~10%): *las tarjetas, los dictados,
  insertar, la pronunciación, los audífonos/auriculares, la jerga,
  los tips* — Anki-about-Anki vocabulary.
- **Travel/family/admin** (~10%): visas, *la solicitud, el
  certificado de nacimiento, el pasaporte*, kinship terms retaught
  chronically (*el sobrino* 5×, *la sobrina* 3×, *el tío, la tía, el
  primo* — 2019→2024!), country names (*Noruega* 4×, *Hungría* 3×,
  *Bélgica*, *Suiza*, *Ucrania* 6×, *Dinamarca*, *Chequia*).
- Word classes: ~60% nouns (recorded with article — gender scaffold),
  ~25% verbs (often given with a conjugated exemplar: *persiguen -
  perseguir*, *comienzo - comenzar*), ~10% adjectives/adverbs, plus
  discourse connectors (*a pesar de, incluso si, en cuanto a, con
  respecto a, mientras tanto, por medio de*).
- Register: neutral-to-formal journalistic Spanish; near-zero
  colloquialisms; synonym doublets taught deliberately (*meta/objetivo,
  reto/desafío, confinamiento/cuarentena, auriculares/audífonos,
  lo contrario/el opuesto, aclarar/dilucidar*). Vocabulary is NOT the
  weak front — the learner operates comfortably at C1 lexis; the
  taught items are precision/nuance upgrades.

## 5. Pronunciation profile

Thin but consistent: 11 pron-flagged xlsx rows (no wrong form
recorded) + ~10 Teachee notes with embedded IPA fragments.
- Flagged items: *pasado mañana, el objetivo principal, la calidad,
  las respuestas pueden ser dadas, paso a paso, tendencias
  perturbadoras, todas las lecturas, una agencia gubernamental, más de
  cien, estar tranquilo, la situación está empeorando* — multiword
  stretches, mostly stress placement + linking, clustered 2020-11 and
  2021-11.
- Teachee IPA fragments mark: `aoɾa` (ahora — silent h), `aβɾil`,
  `aktiβiðað(es)`, `axenθja` (agencia), `aiɾe akondiθjonaðo`,
  `alkanθaβle`, `aeɾopweɾto`. Pattern: vowel-initial words and the
  lenited approximants [β ð ɣ] — plus velar /x/ (agencia) and the
  b/v merger. Every IPA-marked word is a cognate the learner would
  anglicize.
- Verdict: too thin for a dedicated unit now; when audio formats (A1/
  A2, §4 of the strategy doc) arrive, seed the ES beep-cloze pool with
  -ción/-dad cognates and vowel-initial words rather than random
  sentences.

## 6. Curriculum mapping

Existing 18 active units + 1 planned. Evidence = verbatim errors
mappable to the unit + recurrence signal. Actions are relative to
current per-unit target_size.

| Unit | Evidence from this dataset | Action |
|---|---|---|
| es_pres_irreg | 0 errors; present-tense production fluent everywhere in Teachee | LOWER (maintenance trickle) |
| es_preterito | 4 errors (*pune, quisemos, investieron, me fue*) — strong preterites + stem-changers exactly as the unit guidance predicts | RAISE; bias generation toward poner/querer/invertir-class stems |
| es_imperfecto | 1 combined error (*yo no fue* → *iba*); correct imperfects appear in Teachee (*intentaba, necesitaba, me sentía*) | KEEP |
| es_futuro | 0 errors; learner uses *ir a* + inf natively, simple future only in Teachee reteaches (*tendremos, podré, viajaré*) | KEEP small (form practice still useful — learner avoids the tense) |
| es_condicional | 0 errors, 1 correct usage (*sería un problema*) | LOWER |
| es_subj_pres | 0 errors; triggers taught with correct examples 5+ times — no evidence of failure, some of avoidance | KEEP (production insurance) |
| es_subj_imp | 0 errors, 0 attempts visible — likely total avoidance | KEEP |
| es_perfecto | 0 errors; fluent in Teachee (*he grabado, he pasado, hemos tenido*) | LOWER |
| es_cmd_tu / es_cmd_usted / es_cmd_neg | 0 errors BUT 0 opportunities — corpus is narration, commands never occur. Genre gap, not mastery | KEEP (only source of practice the learner gets) |
| es_cond_perf | 0 errors, 0 attempts | LOWER |
| es_plusc_subj | 0 errors, 0 attempts | LOWER |
| es_clitics_dir | Indirect: 2022-07-29 lesson drilled *comprarlo / Lo quiero* | KEEP |
| es_clitics_ind | Indirect: same lesson, *comprarle un carro a mi hijo* | KEEP |
| es_clitics_selo | **1 verbatim year-4 error** (`comprar le lo`) — the exact le+lo→se lo rule the unit hard-codes | RAISE |
| es_verb_prep | 7 motion-prep errors map here IF the bank covers ir/viajar/llegar/regresar/volver a + pasar tiempo en. Audit `es_verb_prep.json`; add these regimes if absent | RAISE (with bank audit) |
| es_por_para | 0 true por/para confusions in 6 years; only the pt *viajar para* calque | LOWER to maintenance; the destination-*para* trap belongs to the motion-prep drills |
| es_ser_estar (planned) | 1 error in 6 years (*ser en contacto*), fixed-PP flavored | Activate SMALL (target ~8-10), estar+PP/location focus, not the full ser/estar catechism |

**New units the data justifies** (in priority order):

1. **`es_interferencia`** — cluster **"8 Interferencias"** (new).
   The #1 category (26/62) with zero coverage. Format F3
   (error-correction, §4 of strategy doc) + F4 (cross-language
   contrast) — both formats exist on paper precisely for this; seed
   pairs in §7. Verification: blind (answer_set n/a) or F3-style
   fixed-pair items which need no morph lookup. Start with the
   pt set (inserir/exemplo/longo/isolado/conosco/quisemos) — 2024-live.
2. **`es_muy_mucho`** — cluster "8 Interferencias" or standalone in a
   **"9 Grado y cantidad"** cluster. 7 verbatim errors. Closed class →
   Tier B blind verification, answer_set = [muy, mucho, mucha, muchos,
   muchas, mucho más, tan, tanto]. Modeled on es_por_para (same shape:
   one blank, rule nameable in one line).
3. **`es_light_verbs`** (tomar/cometer/hacer/dar collocations) —
   cluster "8 Interferencias" (they ARE calques) or "6 Preposiciones"
   sibling cluster **"10 Colocaciones"**. Blind-verified,
   answer_set = [tomar, hacer, cometer, dar, poner, sacar] + tense
   tolerance. 3 verbatim errors + 4-year recurrence.
4. **`es_numeros_fechas`** — hundreds morphology + date ordinals
   (*el primero de junio*, *mil novecientos...*). Low glamour, clearly
   unfixed after 5 years (2019 error → 2023/24 still being drilled).
   F1-style cloze, answers verifiable against a deterministic
   number-speller — no LLM verification needed at all.
5. NOT recommended despite temptation: a *tampoco*/polarity unit
   (n=1) and a pronunciation unit (no error data) — fold both into F3
   seeds / future audio formats respectively.

Cluster naming note: keep "7 Ser/Estar" as-is; propose "8
Interferencias" (es_interferencia, es_muy_mucho, es_light_verbs) and
"9 Números y fechas" (es_numeros_fechas) so Anki sorts the new decks
after the existing seven. Cluster strings are FINAL once shipped
(subdeck-orphaning rule in curriculum.py) — decide before Wave 5 wiring.

## 7. F3 seed list — 40 verbatim error pairs (machine-readable)

Reconstruction policy: `wrong` is the learner's recorded form, embedded
in the teacher's recorded correct frame where the source logged only a
fragment (insertions marked by the frame itself, never invented
content). `right` is the teacher's correction verbatim (accents
normalized).

```json
[
  {"wrong": "mucho de moda", "right": "muy de moda", "why": "muy + adjective/adverbial phrase; mucho only quantifies nouns/verbs", "category": "muy_mucho"},
  {"wrong": "mucho difícil", "right": "muy difícil", "why": "muy + adjective", "category": "muy_mucho"},
  {"wrong": "mucho importante", "right": "muy importante", "why": "muy + adjective", "category": "muy_mucho"},
  {"wrong": "mucho profesional", "right": "muy profesional", "why": "muy + adjective", "category": "muy_mucho"},
  {"wrong": "hubo muy tráfico", "right": "hubo mucho tráfico", "why": "mucho quantifies nouns; muy never modifies a noun", "category": "muy_mucho"},
  {"wrong": "hace muy frío", "right": "hace mucho frío", "why": "frío/calor/hambre are nouns in weather idioms → mucho", "category": "muy_mucho"},
  {"wrong": "hacía muy calor", "right": "hacía mucho calor", "why": "hacer calor takes mucho (noun), not muy", "category": "muy_mucho"},
  {"wrong": "viajar para un lugar", "right": "viajar a un lugar", "why": "destination takes a in Spanish; para-destination is Portuguese", "category": "prep_motion"},
  {"wrong": "fui en Londres", "right": "me fui a Londres", "why": "motion → a; en marks location, not destination (pt 'em' calque)", "category": "prep_motion"},
  {"wrong": "en tres días me voy en Francia", "right": "en tres días voy a Francia", "why": "motion → a Francia", "category": "prep_motion"},
  {"wrong": "yo regreso en Italia", "right": "yo regreso a Italia", "why": "regresar a + destination", "category": "prep_motion"},
  {"wrong": "cuando llegue en Madrid", "right": "cuando llegue a Madrid", "why": "llegar a, never llegar en (pt 'chegar em' calque)", "category": "prep_motion"},
  {"wrong": "pasar una noche a París", "right": "pasar una noche en París", "why": "static location → en; a marks motion (fr/it calque)", "category": "prep_motion"},
  {"wrong": "ser en contacto", "right": "estar en contacto", "why": "estar for states and locative/PP predicates", "category": "ser_estar"},
  {"wrong": "hacer estas decisiones", "right": "tomar estas decisiones", "why": "tomar decisiones — 'make decisions' is an English calque", "category": "light_verb"},
  {"wrong": "hacer fotos", "right": "tomar fotos", "why": "LatAm Spanish: tomar fotos (hacer fotos is peninsular/It. calque)", "category": "light_verb"},
  {"wrong": "hacer errores", "right": "cometer errores", "why": "cometer un error — 'make mistakes' is an English calque", "category": "light_verb"},
  {"wrong": "tener algo sobre control", "right": "tener algo bajo control", "why": "bajo control — 'under control'; sobre is a false mapping", "category": "fixed_prep"},
  {"wrong": "al fin va a costar mucho menos", "right": "al final va a costar mucho menos", "why": "al final = in the end; al fin = at last (relief)", "category": "fixed_prep"},
  {"wrong": "mi esposa también no fue", "right": "mi esposa tampoco fue", "why": "negative agreement: tampoco replaces también under negation", "category": "polarity"},
  {"wrong": "quiero comprar le lo", "right": "quiero comprárselo", "why": "le + lo → se lo; clitics attach enclitic to the infinitive", "category": "clitics"},
  {"wrong": "yo no fue hace un año", "right": "yo no iba hace un año", "why": "1sg is fui, and habitual past → imperfect iba", "category": "verb_morph"},
  {"wrong": "me fue a Francia", "right": "me fui a Francia", "why": "irse 1sg preterite = me fui (fue is 3sg)", "category": "verb_morph"},
  {"wrong": "yo pune algunas de sus cartas", "right": "yo puse algunas de sus cartas", "why": "poner strong preterite: puse, pusiste, puso", "category": "verb_morph"},
  {"wrong": "quisemos", "right": "quisimos", "why": "querer preterite 1pl = quisimos (quisemos is Portuguese)", "category": "verb_morph"},
  {"wrong": "investieron", "right": "invirtieron", "why": "invertir is e→i in the preterite 3pl: invirtieron (pt/it calque)", "category": "verb_morph"},
  {"wrong": "cinco cientos metros", "right": "quinientos metros", "why": "500 = quinientos, irregular hundred", "category": "numerals"},
  {"wrong": "un otro ciudad", "right": "otra ciudad", "why": "no article before otro, and ciudad is feminine → otra", "category": "interference"},
  {"wrong": "esta carga", "right": "este cargo", "why": "el cargo = post/position; la carga = load", "category": "gender_lexeme"},
  {"wrong": "la dictación", "right": "el dictado", "why": "dictation = el dictado; 'dictación' is a false derivation", "category": "derivation"},
  {"wrong": "la consumación", "right": "el consumo", "why": "consumption = el consumo; consumación = consummation", "category": "derivation"},
  {"wrong": "similaridades", "right": "las similitudes", "why": "similarity = similitud (pt similaridade / en calque)", "category": "derivation"},
  {"wrong": "muy avergonzante", "right": "muy vergonzoso", "why": "embarrassing = vergonzoso; 'avergonzante' is a coinage", "category": "derivation"},
  {"wrong": "algo profundido", "right": "algo profundo", "why": "profound = profundo; 'profundido' is not a Spanish form", "category": "derivation"},
  {"wrong": "la cualidad de las publicaciones", "right": "la calidad de las publicaciones", "why": "calidad = quality (grade); cualidad = attribute/trait", "category": "gender_lexeme"},
  {"wrong": "inserir", "right": "insertar", "why": "insert = insertar; inserir is Portuguese (recorded twice, 2022)", "category": "interference"},
  {"wrong": "exemplo", "right": "ejemplo", "why": "pt exemplo → es ejemplo", "category": "interference"},
  {"wrong": "el viaje no es muy longo", "right": "el viaje no es muy largo", "why": "pt longo → es largo", "category": "interference"},
  {"wrong": "trabajo muy isolado", "right": "trabajo muy aislado", "why": "pt isolado → es aislado", "category": "interference"},
  {"wrong": "trabajar conosco", "right": "trabajar con nosotros", "why": "pt conosco → es con nosotros", "category": "interference"}
]
```

Left out of the 40 (usable as second-batch seeds): `semplice→simple`,
`nostro→nuestro`, `Berlino→Berlín`, `pasaporto→pasaporte`,
`chines→chino`, `holandês→holandesa`, `financeiras→financieras`,
`mensales→mensuales`, `resercar→investigar`, `restar→anular`,
`extensiva→extensa`, `critical→crítico`, `candidaturas→candidatos`,
`rolo→rol`, `veros→verdaderos`, plus the spelling slips.

## 8. Capture-channel note

The verbatim-error supply died in Nov 2022 when lessons moved to
Teachee (the teacher records only targets there). The es profile is
strong enough to build on, but Wave 5's personalization loop should
add a live error-capture path (add-on side or a teacher convention like
`wrong → right` in the Teachee field) — same recommendation as the it
profile, where the gap is fatal rather than merely annoying.
