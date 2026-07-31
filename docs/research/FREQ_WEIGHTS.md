# Frequency weights for grammar cells

Built 2026-08-01. The five `freq_weights_{lang}.json` files turn observed
subtitle counts for conjugated surface forms into relative weights for each
live verb unit's `(verb, person)` cells. They are ordering evidence, not a
claim that an untagged corpus can recover a true tense distribution.

## Source choice and license

Direct SUBTLEX releases differ in format, download stability, variety, and
reuse terms. In particular, the Portuguese release is described as freely
available for research rather than under a standard redistribution license.
For this public, reproducible data layer we therefore use the fallback allowed
by commission R: the 2018 full per-form lists in
[hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords),
pinned to commit `525f9b560de45753a5ea01069454e72e9aa541c6`.
The repository identifies [OPUS OpenSubtitles
2018](https://opus.nlpl.eu/OpenSubtitles2018.php) as the corpus, specifies the
`word count` format, and licenses generated content under **CC BY-SA 4.0**
(builder code is MIT). These aggregate output files retain that attribution
and CC BY-SA label in `_meta`.

| Language | Pinned input | Curriculum scope |
|---|---|---|
| Spanish | [`es_full.txt`](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/es/es_full.txt) | 13 finite-morphology units; imperative-person restrictions applied |
| French | [`fr_full.txt`](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/fr/fr_full.txt) | 7 finite-morphology units |
| Italian | [`it_full.txt`](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/it/it_full.txt) | 7 finite-morphology units |
| Brazilian Portuguese | [`pt_full.txt`](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/pt/pt_full.txt) | 7 finite-morphology units; `tu/vós` cells excluded by project policy |
| German | [`de_full.txt`](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/de/de_full.txt) | current verb-list scope is `de_passiv` only |

The source SHA-256 for each downloaded file is embedded in its generated
JSON. The builder caches the pinned files outside the repository and supports
`--offline`; a fixed `--build-date` or `SOURCE_DATE_EPOCH` makes output
byte-for-byte reproducible.

## Method

1. Read live topics and their verb inventories from `curriculum.py`. Closed-
   class, noun, article, F3, and F4 units have no tense-person cell and are
   intentionally absent.
2. Resolve every eligible cell through the vendored Jehle table (Spanish) or
   verbecc tables (French, Italian, Portuguese). A source-table gap gets weight
   zero rather than an inferred form. Spanish command units use their actual
   allowed persons; Brazilian Portuguese omits `2s/2p`.
3. Look up the NFC-normalized, case-folded surface in the language's raw
   per-form count list. For compound forms, use the geometric mean of component
   token counts. This lets both the participle and person-marked auxiliary
   contribute without falsely treating unigram data as phrase counts.
4. German currently has no general finite-verb unit. For `de_passiv`, combine
   its curated participle with the closed auxiliary tables already enforced by
   `generate.py`; average Präsens, Präteritum, Perfekt, and modal categories.
   `archivieren`, whose participle is deliberately outside the deterministic
   table, remains zero.
5. Treat homographs conservatively. Exact surfaces are divided across all
   analyses in the complete local morphology table. Cross-lemma collisions and
   finite/nonfinite collisions receive an additional `0.10` uncertainty
   factor; one- to three-letter forms are discounted; and a small reviewed list
   catches obvious noun/function-word collisions the verb tables cannot see
   (`porte`, `livre`, `vino`, `para`, `stato`, and peers).
6. Divide every ambiguity-adjusted effective count by the maximum inside its
   unit and round to six decimals. Thus `1.0` means “highest observed cell in
   this unit,” not “same absolute frequency as a 1.0 in another unit.” Zero
   means missing/unattested/unsafe, never ungrammatical.

This is deliberately an underweighting policy. Untagged subtitles cannot tell
French *porte* the noun from *porte* the verb, distinguish Portuguese future
subjunctive *sair* from the infinitive, or allocate Spanish *fui* perfectly
between *ser* and *ir*. Inflating an ambiguous cell would work directly against
the project's frequency-first goal. Subtitle dialogue also skews toward spoken
register; the weights should order practice, not define a complete syllabus.

## Sanity check: highest and lowest cells

The lists below are generated from the shipped files. “Lowest” means the ten
lowest **positive** cells; zero cells are separately counted in each file's
metadata. Because normalization is per unit, the high list naturally includes
several unit maxima.

### Spanish

| # | Highest | Weight | Lowest positive | Weight |
|---:|---|---:|---|---:|
| 1 | `es_pres_irreg · estar · 3s` | 1.000000 | `es_imperfecto · crear · 2p` | 0.000003 |
| 2 | `es_preterito · decir · 3s` | 1.000000 | `es_imperfecto · sacar · 2p` | 0.000003 |
| 3 | `es_imperfecto · estar · 1s` | 1.000000 | `es_imperfecto · permitir · 2p` | 0.000003 |
| 4 | `es_imperfecto · estar · 3s` | 1.000000 | `es_imperfecto · recordar · 2p` | 0.000003 |
| 5 | `es_futuro · ser · 3s` | 1.000000 | `es_futuro · producir · 2p` | 0.000004 |
| 6 | `es_condicional · poder · 1s` | 1.000000 | `es_condicional · traducir · 2p` | 0.000006 |
| 7 | `es_condicional · poder · 3s` | 1.000000 | `es_condicional · traducir · 1p` | 0.000006 |
| 8 | `es_subj_pres · hacer · 2s` | 1.000000 | `es_condicional · repetir · 2p` | 0.000006 |
| 9 | `es_subj_imp · querer · 1s` | 1.000000 | `es_condicional · construir · 2p` | 0.000006 |
| 10 | `es_subj_imp · querer · 3s` | 1.000000 | `es_condicional · mantener · 2p` | 0.000006 |

The requested spot check holds: `decir · 3s` is the highest preterite cell,
while low-frequency first/second-person-plural future/conditional cells such
as `traducir · 2p` sit near the floor.

### French

| # | Highest | Weight | Lowest positive | Weight |
|---:|---|---:|---|---:|
| 1 | `fr_present_irreguliers · être · 3s` | 1.000000 | `fr_imparfait · écrire · 1p` | 0.000019 |
| 2 | `fr_passe_compose · arriver · 3s` | 1.000000 | `fr_imparfait · lire · 1p` | 0.000021 |
| 3 | `fr_imparfait · être · 3s` | 1.000000 | `fr_imparfait · boire · 1p` | 0.000039 |
| 4 | `fr_futur_simple · être · 3s` | 1.000000 | `fr_conditionnel_present · boire · 1p` | 0.000046 |
| 5 | `fr_conditionnel_present · pouvoir · 3s` | 1.000000 | `fr_conditionnel_present · recevoir · 1p` | 0.000046 |
| 6 | `fr_subjonctif_present · être · 3s` | 1.000000 | `fr_futur_simple · pleuvoir · 3p` | 0.000049 |
| 7 | `fr_subjonctif_conjonctions · être · 3s` | 1.000000 | `fr_conditionnel_present · envoyer · 1p` | 0.000053 |
| 8 | `fr_conditionnel_present · être · 3s` | 0.946904 | `fr_present_irreguliers · écrire · 1p` | 0.000061 |
| 9 | `fr_passe_compose · venir · 3s` | 0.928183 | `fr_present_irreguliers · vivre · 2s` | 0.000064 |
| 10 | `fr_conditionnel_present · avoir · 3s` | 0.918155 | `fr_present_irreguliers · vivre · 1s` | 0.000064 |

### Italian

| # | Highest | Weight | Lowest positive | Weight |
|---:|---|---:|---|---:|
| 1 | `it_presente_irregolari · essere · 1s` | 1.000000 | `it_imperfetto · tradurre · 1p` | 0.000004 |
| 2 | `it_presente_irregolari · essere · 3p` | 1.000000 | `it_imperfetto · trarre · 2p` | 0.000004 |
| 3 | `it_passato_prossimo · morire · 1s` | 1.000000 | `it_imperfetto · porre · 2p` | 0.000004 |
| 4 | `it_imperfetto · essere · 3s` | 1.000000 | `it_imperfetto · trarre · 1p` | 0.000008 |
| 5 | `it_futuro_semplice · essere · 3s` | 1.000000 | `it_congiuntivo_presente · tradurre · 3p` | 0.000009 |
| 6 | `it_condizionale_presente · essere · 3s` | 1.000000 | `it_imperfetto · tradurre · 3p` | 0.000011 |
| 7 | `it_congiuntivo_presente · avere · 1p` | 1.000000 | `it_imperfetto · porre · 2s` | 0.000011 |
| 8 | `it_passato_remoto · dire · 3s` | 1.000000 | `it_imperfetto · porre · 1p` | 0.000015 |
| 9 | `it_passato_prossimo · andare · 1s` | 0.903476 | `it_condizionale_presente · piacere · 1p` | 0.000025 |
| 10 | `it_congiuntivo_presente · essere · 1p` | 0.841928 | `it_imperfetto · trarre · 2s` | 0.000027 |

### Brazilian Portuguese

| # | Highest | Weight | Lowest positive | Weight |
|---:|---|---:|---|---:|
| 1 | `pt_presente_irregulares · estar · 3s` | 1.000000 | `pt_subjuntivo_presente · haver · 1p` | 0.000003 |
| 2 | `pt_preterito_perfeito · dizer · 1s` | 1.000000 | `pt_presente_irregulares · ir · 1p` | 0.000006 |
| 3 | `pt_preterito_perfeito · dizer · 3s` | 1.000000 | `pt_presente_irregulares · haver · 1p` | 0.000007 |
| 4 | `pt_preterito_imperfeito · estar · 1s` | 1.000000 | `pt_subjuntivo_presente · ler · 1p` | 0.000012 |
| 5 | `pt_preterito_imperfeito · estar · 3s` | 1.000000 | `pt_subjuntivo_presente · trazer · 1p` | 0.000034 |
| 6 | `pt_futuro_simples · ser · 3s` | 1.000000 | `pt_presente_irregulares · haver · 3p` | 0.000065 |
| 7 | `pt_condicional_presente · ser · 1s` | 1.000000 | `pt_subjuntivo_presente · pedir · 1p` | 0.000074 |
| 8 | `pt_condicional_presente · ser · 3s` | 1.000000 | `pt_futuro_simples · haver · 1s` | 0.000095 |
| 9 | `pt_subjuntivo_presente · ir · 1p` | 1.000000 | `pt_futuro_simples · querer · 1p` | 0.000124 |
| 10 | `pt_futuro_subjuntivo · querer · 1s` | 1.000000 | `pt_condicional_presente · ler · 1p` | 0.000129 |

### German

| # | Highest | Weight | Lowest positive | Weight |
|---:|---|---:|---|---:|
| 1 | `de_passiv · schreiben · 3s` | 1.000000 | `de_passiv · finanzieren · 2p` | 0.126096 |
| 2 | `de_passiv · schreiben · 1s` | 0.758286 | `de_passiv · genehmigen · 2p` | 0.135808 |
| 3 | `de_passiv · verbieten · 3s` | 0.705143 | `de_passiv · produzieren · 2p` | 0.138031 |
| 4 | `de_passiv · schreiben · 2s` | 0.694685 | `de_passiv · prüfen · 2p` | 0.148922 |
| 5 | `de_passiv · entwickeln · 3s` | 0.639491 | `de_passiv · schützen · 2p` | 0.152764 |
| 6 | `de_passiv · wählen · 3s` | 0.633691 | `de_passiv · veröffentlichen · 2p` | 0.154378 |
| 7 | `de_passiv · beschließen · 3s` | 0.600831 | `de_passiv · ersetzen · 2p` | 0.162005 |
| 8 | `de_passiv · untersuchen · 3s` | 0.557694 | `de_passiv · korrigieren · 2p` | 0.163055 |
| 9 | `de_passiv · ablehnen · 3s` | 0.555212 | `de_passiv · eröffnen · 2p` | 0.165450 |
| 10 | `de_passiv · verbieten · 1s` | 0.534583 | `de_passiv · finanzieren · 3p` | 0.177833 |

## Later integration sketch (not implemented here)

The generator should request a concrete weighted cell plan, rather than merely
listing verbs and hoping the model samples realistically:

```python
weights = load_freq_weights(topic.lang)[topic.key]
cells = [(verb, person, weight) for verb, people in weights.items()
         for person, weight in people.items() if weight > 0]
rng = random.Random(batch_id)                         # reproducible order
sampling = [max(0.01, weight ** 0.5) for *_, weight in cells]
chosen = weighted_without_replacement(cells, sampling, count=n)
cell_plan = [{"infinitive": verb, "person": person}
             for verb, person, _weight in chosen]
prompt = render_prompt(topic, required_cells=cell_plan)
items = generate_and_verify(prompt, topic)             # verifier unchanged
assert observed_cells(items) == cell_plan              # reject plan drift
```

The square root and `0.01` floor are generation-temperature choices, not part
of the evidence files: they retain rare but pedagogically necessary cells
without flattening the source signal. Telemetry can later adjust that sampling
layer while these corpus weights remain the cold-start prior.

## Rebuild

```bash
uv run python tools/build_freq_weights.py --build-date 2026-08-01
uv run python tools/build_freq_weights.py --offline --build-date 2026-08-01
```

Use `--summary` to reproduce the tables above. Cached inputs live under
`${XDG_CACHE_HOME:-~/.cache}/idiomatic/frequency-words/<revision>/`; they are
not committed.
