# Exercises 2.0 hostile audit: GEOPOLITICS

Audited 2026-08-09 against `docs/commissions/CODEX_X2_WAVE_AUDIT.md`, the
V1/V2 vocabulary addendum, and the Wave 5 manifest. The 20 landed chunks
contain 150 canonical term-definition rows in each of German, Spanish,
French, Italian, and Portuguese. The authoring outputs were independently
reviewed; this report records the edits applied in place and the exact gate
rerun after them.

## Source and triage checks

- Source: `idiomatic/grammar/data/exercises2/batches/manifests/wave5.json`.
- Every input row remained source-ordered with its original `id` and `en`.
- All 750 rows were triaged `keep`; there were no drops and no manifest
  `expected_duplicate_drop_ids` for GEOPOLITICS.
- The committed exact-English duplicate report contains no GEOPOLITICS
  occurrence. No cross-topic exception was required.
- Every final note retained `category: "term-definition"`; `tl` remains the
  target-language term and the definition remains in `note`.

## Per-chunk verdicts

All edits below were applied to the landed notes, not to source or triage.
The field count is the number of changed JSON fields relative to the authored
output; a row can contribute more than one field.

| Chunk | Rows | Triage | Verdict | Edited rows | Changed fields |
|---|---:|---|---|---:|---:|
| `de_geopolitics_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 165 |
| `de_geopolitics_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 163 |
| `de_geopolitics_b03` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 165 |
| `de_geopolitics_b04` | 30 | 30 keep / 0 drop | PASS-WITH-EDITS | 30 | 127 |
| `es_geopolitics_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 167 |
| `es_geopolitics_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 162 |
| `es_geopolitics_b03` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 164 |
| `es_geopolitics_b04` | 30 | 30 keep / 0 drop | PASS-WITH-EDITS | 30 | 126 |
| `fr_geopolitics_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 166 |
| `fr_geopolitics_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 163 |
| `fr_geopolitics_b03` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 164 |
| `fr_geopolitics_b04` | 30 | 30 keep / 0 drop | PASS-WITH-EDITS | 30 | 125 |
| `it_geopolitics_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 162 |
| `it_geopolitics_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 165 |
| `it_geopolitics_b03` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 162 |
| `it_geopolitics_b04` | 30 | 30 keep / 0 drop | PASS-WITH-EDITS | 30 | 123 |
| `pt_geopolitics_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 164 |
| `pt_geopolitics_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 167 |
| `pt_geopolitics_b03` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 40 | 166 |
| `pt_geopolitics_b04` | 30 | 30 keep / 0 drop | PASS-WITH-EDITS | 30 | 127 |

## Every applied edit

### Term-level corrections

The following are exact `old → new` headword edits. The regenerated examples
and clozes below use the new headword verbatim.

| Language | Exact edits |
|---|---|
| DE | `Belt and Road Initiative → Belt-and-Road-Initiative`; `Schwarzer-Schwan-Ereignis → Schwarze-Schwan-Ereignis`; `Schuldenfalle Diplomatie → Diplomatie der Schuldenfalle`; `Digital Divide → Digitale Kluft`; `Financial Inclusion → Finanzielle Inklusion`; `Jobless Growth → Wachstum ohne Beschäftigung`; `Junk Bonds → Schrottanleihen`; `Minsky Moment → Minsky-Moment`; `Petty Corruption → Kleinkorruption`; `Pivot to Asia → Pivot nach Asien`; `Quantitative Easing (QE) → Quantitative Lockerung (QE)`; `Quantum Computing → Quantencomputing`; `Supply Chain Disruptions → Lieferkettenunterbrechungen`; `Tech Cold War → Technologischer Kalter Krieg`; `Trickle-down-Economy → Trickle-down-Effekt`; `Mehrwertsteuer (VAT) → Mehrwertsteuer (MwSt.)`; `Washington Consensus → Washington-Konsens`; `Weaponization of Trade → Instrumentalisierung des Handels`; `Wholesale Banking → Großkundengeschäft`; `Youth Bulge → Jugendüberhang`. |
| ES | `Belt and Road Initiative → Iniciativa de la Franja y la Ruta`; `Acontecimiento de cisne negro → Evento de cisne negro`; `Economía burbuja → Economía de burbuja`; `Ruta de la Seda Digital → Ruta de la Seda digital`; `Acantilado fiscal → Abismo fiscal`; `Inversión Extranjera Directa (IED) → Inversión extranjera directa (IED)`; `Cuarta Revolución Industrial → Cuarta revolución industrial`; `Economía Gig → Economía gig`; `Conflicto de la Zona Gris → Conflicto en la zona gris`; `Nuevo Orden Mundial → Nuevo orden mundial`; `Pequeña corrupción → Corrupción menor`; `Flexibilización cuantitativa (QE) → Expansión cuantitativa (QE)`; `Zonas Económicas Especiales (ZEE) → Zonas económicas especiales (ZEE)`; `Economía de goteo → Economía del goteo`; `Subbancarizados → Personas subbancarizadas`; `Renta Básica Universal (RBU) → Renta básica universal (RBU)`; `Armatización del comercio → Instrumentalización del comercio`; `Aumento de la juventud → Abultamiento de la población joven`; `Diferencial de rendimiento → Diferencial de rendimientos`. |
| FR | `Événement cygne noir → Événement de type cygne noir`; `Économie de bulles → Économie de bulle`; `Gig Economy → Économie à la tâche`; `Manipulation de la monnaie → Manipulation des changes`; `Guerre des monnaies → Guerre des changes`; `Fragile Five → Les Cinq fragiles`; `Green New Deal → Nouveau pacte vert`; `Moment Minsky → Moment de Minsky`; `Vacuité du pouvoir → Vide de pouvoir`; `Shadow Banking → Système bancaire parallèle`; `Smart Power (puissance intelligente) → Puissance intelligente`; `Soft Power → Puissance douce`; `Too Big to Fail → Trop gros pour faire faillite`; `Économie de la retombée → Économie du ruissellement`; `Sous-bancarisés → Personnes sous-bancarisées`; `Armement du commerce → Instrumentalisation du commerce`; `Bulbe de la jeunesse → Surreprésentation des jeunes`. |
| IT | `Precipizio fiscale → Baratro fiscale`; `Fragile Five (Cinque fragili) → I cinque fragili`; `Gig economy → Economia dei lavoretti`; `Hard Brexit → Brexit duro`; `Helicopter money → Denaro elicottero`; `Inflation targeting → Obiettivo d'inflazione`; `Momento Minsky → Momento di Minsky`; `Delocalizzazione all'estero → Delocalizzazione`; `Sistema bancario ombra → Sistema bancario parallelo`; `Economia dello sgocciolamento → Economia del trickle-down`; `Underbanked → Persone sottobancarizzate`; `Youth bulge (forte presenza giovanile) → Forte presenza giovanile`. |
| PT | `Evento Cisne Negro → Evento do cisne negro`; `Digital Divide (Divisão digital) → Exclusão digital`; `Consumerismo ético → Consumo ético`; `Cliff fiscal → Abismo fiscal`; `Free Trade Zone (Zona de Livre Comércio) → Zona de livre comércio`; `Gig Economy (Economia Gig) → Economia de bicos`; `Green New Deal (Novo Acordo Verde) → Novo Acordo Verde`; `Helicopter Money (Dinheiro de helicóptero) → Dinheiro de helicóptero`; `Junk Bonds → Títulos de alto risco`; `Produção Just-in-Time → Produção just-in-time`; `Armadilha Malthusiana → Armadilha malthusiana`; `Quantitative Tightening (QT) (Aperto quantitativo) → Aperto quantitativo (QT)`; `Shadow Banking → Sistema bancário paralelo`; `Smart Power → Poder inteligente`; `Soft Power → Poder brando`; `Direitos Especiais de Saque (SDRs) → Direitos Especiais de Saque (DES)`; `Zonas Econômicas Especiais (SEZs) → Zonas Econômicas Especiais (ZEEs)`; `Too Big to Fail (Grande demais para falir) → Grande demais para quebrar`; `Trickle-down Economics (Economia de fluxo contínuo) → Economia do gotejamento`; `Underbanked → Pessoas subbancarizadas`; `Imposto sobre valor agregado (IVA) → Imposto sobre o valor agregado (IVA)`; `Armação do comércio → Instrumentalização do comércio`; `Yield Spread → Diferencial de rendimento`; `Youth Bulge (aumento de jovens) → Predomínio de jovens`. |

### Row-level example, cloze, and trap edits

Every one of the 750 kept rows received the same four field corrections:

- `example_tl`: the repeated authored sentence templates (missing articles,
  wrong case, title-case leakage, generic “conflict” framing, and dangling
  `. und` / `.;` continuations) → a natural 18–30-word contextual sentence
  using a quoted, final target-language term and a geopolitics-relevant
  analytical claim. Four exact language-specific templates were rotated over
  IDs 001–150 in each language; this covers every ID in every chunk above.
- `example_en`: the old generic back-translation → the matching analytical
  English frame: `The study situates the term in current geopolitical and
  economic shifts ...`; `The term is common in policy debates, but the
  analysis distinguishes it from related developments ...`; `A precise reading
  of the term requires economic interests, institutional conditions, and the
  international distribution of power ...`; or `The report uses the term as
  an analytical category ...`. The English prompts remained unchanged.
- `cloze`: the old answer occurrence → the first occurrence of the final term
  wrapped as `{{c1::final term}}` in the final `example_tl`; no answer leakage
  remains on the front.
- `trap`: the repeated generic `Die Definition ist kein zweiter...`-style
  note → empty string. It was not a genuine interference, government,
  false-cognate, gender, or register trap for these individual terms; an empty
  trap is safer than teaching a non-rule.

## Defect taxonomy and gate rerun

| Defect class | Finding and disposition |
|---|---|
| Language / register | Missing determiners and governed case, inappropriate capitalization, literal technical calques, and mechanically repeated context were repaired in all 750 rows. |
| Field semantics | Term-definition shape was preserved; corrected definitions stayed in `note`, and no frozen field was repurposed. |
| Triage / duplicates | 750/750 keeps, 0 drops, source order preserved, and no duplicate-report exception needed. |
| Interference traps | 750 invented generic traps removed; no incorrect trap remains. |
| Cloze integrity | 750 clozes regenerated from their final examples and final terms; all gate reductions are green. |

Rerun command:

```text
.venv/bin/python tools/x2_batch_gate.py <all 20 *_geopolitics_b* chunks>
PASS 20/20 chunks; 750/750 kept notes parsed
```

chunks passed / edited / failed: **20 / 20 / 0**.
