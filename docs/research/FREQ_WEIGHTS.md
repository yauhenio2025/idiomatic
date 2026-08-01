# Frequency weights for grammar cells

Built 2026-08-01. The four `freq_weights_{lang}.json` files are cold-start
priors for choosing which `(verb, tense, person)` cells deserve more drills.
They are **orthographic-form evidence**, not direct measurements of grammatical
cell frequency: even a per-form corpus cannot identify a tense/person analysis
when several analyses have the same spelling.

## Scope and output

The builder reads the live curriculum and includes only topics whose
`verify == "morph"`. Tense and mood are implicit in the unit key, so each file
has the commissioned shape:

```text
{"_meta": {...}, unit_key: {verb: {person: weight}}}
```

Weights are in `[0, 1]` and normalized within a unit. Spanish command units
use their curriculum-specific persons. Brazilian Portuguese uses
`1s/3s/1p/3p`; `2s/2p` are omitted because the generator rejects `tu/vós` in
the Brazilian curriculum. Morphologically unavailable cells are omitted;
source misses among valid cells remain present with weight `0.0`.

German has no output file. Its only tense×person-oriented verb topic,
`de_passiv`, is verified by a custom participle/passive-phrase path rather than
a tense×person table in `morphology.lookup`, and its four passive constructions
cannot be represented honestly by the commissioned unit→verb→person schema.
Inventing German cells here would make the data look more complete while
bypassing the required morphology join.

| Language | Units | Valid cells | Zero weights | Unavailable morphology | Alternative-form cells |
|---|---:|---:|---:|---:|---:|
| Spanish | 13 | 4,160 | 350 | 0 | 0 |
| French | 7 | 818 | 2 | 22 | 0 |
| Italian | 7 | 840 | 3 | 0 | 55 |
| Brazilian Portuguese | 7 | 560 | 22 | 0 | 0 |

## Frequency sources and licenses

Each download is pinned by SHA-256 in the builder and repeated in the output
metadata. A checksum mismatch fails the build rather than silently changing
the weights. Each output also records the SHA-256 of the vendored morphology
file and a canonical fingerprint of the ordered curriculum units, moods,
tenses, verbs, and eligible persons.

| Language | Exact frequency input | Frequency field | License and selection rationale |
|---|---|---|---|
| Spanish | [SUBTLEX-ESP `SUBTLEX-ESP.xlsx`](https://osf.io/xp6sz/) | raw `Freq. count` | The current OSF bundle includes a [CC BY-NC-SA 4.0 notice](https://osf.io/download/xk2p8/), but accessible metadata did not establish that it governs every bundled file; legacy distributions have also been described as CC BY-NC-ND 3.0. This ambiguity is recorded rather than flattened into a confident project-level license claim. The spreadsheet omits hapaxes, so a miss is “no usable evidence,” not a literal zero count. |
| French | [Lexique 4.00 `Lexique400.zip`](https://www.lexique.org/) | sum of `10_FreqMot` for the target lemma's `VER` and `AUX` analyses, in occurrences per million | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Lexique 4 is a 316-million-token subtitle lexicon and provides the POS/lemma detail needed to avoid assigning the noun count for *porte* to *porter*. `AUX` is included because auxiliary uses of *avoir* and *être* are occurrences of those target forms. |
| Italian | [FrequencyWords 2018 `it_full.txt`, commit `525f9b5`](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/it/it_full.txt) | raw token count | The generated list content is [CC BY-SA 4.0; generator code is MIT](https://github.com/hermitdave/FrequencyWords/blob/525f9b560de45753a5ea01069454e72e9aa541c6/README.md#license). It is the documented fallback because no stable, license-explicit direct SUBTLEX-IT download could be pinned. |
| Brazilian Portuguese | [SUBTLEX-PT-BR `SUBTLEX_PT-BR_CDAbove2_Alpha_SpellcheckTrue.tsv`](https://osf.io/vb5yp/) | raw `FREQcount` | The [author's tools page](https://www.kevintang.org/Tools.html) labels the current unigram work CC BY-NC-ND 4.0. This is the restrictive license actually recorded. The selected 61,609,241-token Brazilian list is filtered to CD>2, alphabetic, spellcheck-true rows—not European `SUBTLEX-PT` and not FrequencyWords' generic `pt` directory. The filtering reduces, but cannot eliminate, proper-name, foreign-language, spelling, and subtitle noise. |

Bibliographic attribution: Cuetos, Glez-Nosti, Barbón & Brysbaert
(2011), “SUBTLEX-ESP: Spanish word frequencies based on film subtitles,”
*Psicológica* 32:133–143; New, Pallier, Schalchli, Bourgin & Gimenes
(2026), “Lexique 4: A major upgrade of the Lexique French lexical database,”
*Behavior Research Methods* 58(5):140; Tang (2012), “A 61 Million Word
Corpus of Brazilian Portuguese Film Subtitles as a Resource for Linguistic
Research,” *UCL Working Papers in Linguistics* 24:208–214. The Italian input
is attributed to the pinned FrequencyWords repository and OpenSubtitles 2018
snapshot because it is a generated list rather than a separately published
SUBTLEX release.

The Italian fallback is a lowercased, untagged snapshot derived from OPUS
OpenSubtitles 2018. It reflects subtitle register, translation/dubbing, genre,
regional mixture, names, foreign-language fragments, and tokenization noise;
it is not a contemporary balanced speech corpus. OPUS also [does not claim
ownership of the extracted subtitle text and operates a notice/takedown
policy](https://opus.nlpl.eu/datasets/OpenSubtitles). FrequencyWords' CC label
for its generated count lists should not be read as a new license over every
underlying subtitle.

The raw frequency files are cached outside the repository and are not shipped.
The JSON contains only normalized aggregate weights, checksums, and
attribution. The project treats that as a non-substitutive statistical output,
including for the NC/ND inputs; this provenance note is not a legal opinion or
a claim that an upstream restriction disappeared.

The other side of the join is also licensed data:

| Morphology | Local use | License |
|---|---|---|
| [Fred Jehle Spanish Verb Database](https://github.com/ghidinelli/fred-jehle-spanish-verbs) | vendored Spanish paradigms | [CC BY-NC-SA 3.0](https://github.com/ghidinelli/fred-jehle-spanish-verbs/blob/master/license.txt) |
| [verbecc](https://github.com/bretttolbert/verbecc) French XML | vendored French paradigms | verbecc is LGPL-3.0 overall; the French XML identifies GPL-2.0-or-later Verbiste provenance |
| [verbecc](https://github.com/bretttolbert/verbecc) Italian/Portuguese XML | vendored Italian and Portuguese paradigms | verbecc is LGPL-3.0 overall and credits these XML files to MIT-licensed mlconjug, whose documented model/data lineage may in turn involve Verbiste; upstream does not provide a clean per-file resolution, so this project does not claim one |

The morphology tables already existed in this repository. This build joins
against them; it does not relicense them or settle their mixed upstream
lineage.

## Method

1. Load every live `verify=morph` topic and verb list from `curriculum.py`.
   Resolve its eligible persons through `morphology.lookup`. A missing value or
   a non-form sentinel such as `-` is unavailable and is not emitted.
2. NFC-normalize, case-fold, and preserve diacritics. Expand verbecc's Italian
   alternatives before lookup: `faccio/fo` becomes two forms, and
   `sono rimasto/rimaso` becomes `sono rimasto` plus `sono rimaso`. Evidence
   for alternatives is added because each realizes the same cell.
3. Look up simple forms directly. For a multiword form, compute
   `exp(mean(log1p(component_count))) - 1` after ambiguity adjustment: the
   geometric mean of each component count plus one, followed by subtracting
   one. This keeps both the person-marked auxiliary and lexical participle in
   the ranking, but it is only a proxy: it is **not** a phrase count and can
   either overestimate or underestimate the actual conjugated phrase.
4. Allocate a lexical token's score evenly across the distinct morphology
   analyses in the emitted curriculum inventory that use it. Duplicate curriculum
   units with the same verb/mood/tense/person do not increase the divisor.
   Structural `no` and auxiliary tokens remain components of the multiword
   proxy; they are not divided by the number of curriculum verbs using them.
5. If a finite form is identical to any infinitive in an untagged language's
   vendored morphology inventory, set its score to zero. For example,
   Portuguese future-subjunctive `sair` 1s/3s cannot be separated from its own
   infinitive, while future-subjunctive *ver* `vir` cannot be separated from
   the distinct infinitive *vir*. In lemma-tagged French, only identity with
   the target lemma's own infinitive is unresolved. Zero here means
   “deliberately unresolved,” not “never occurs.”
6. French sums Lexique 4's `VER` and `AUX` rows for the target lemma, excluding
   noun/adjective rows before allocation. This counts auxiliary uses of
   *avoir* and *être* without admitting unrelated homographs. Spanish, Italian,
   and Portuguese inputs lack POS tags. For those, reviewed high-risk
   cross-POS, cross-lemma, and cross-mood collisions get a conservative `0.10`
   factor. Examples actually touched by this build include Spanish `vino` and
   `fuera`, Italian `sei`, `fa`, `dai`, `danno`, `stato`, and Portuguese
   `era`, `vamos`, `virem`, and `virmos`; each JSON `_meta` lists only the
   curated tokens that occurred in its emitted cells. Spanish
   *cree*, *crees*, *creemos*, *creéis*, and *creen* are zeroed: they are forms
   of *crear* in the target subjunctive/commands but also ordinary indicative
   forms of *creer*. A unigram source cannot tell, for example, whether *no
   crees* means “do not create” or “you do not believe”; zero deliberately
   underweights the unresolved target rather than importing the latter use.
   The reviewed lists are small and non-exhaustive. Allocation sees only the
   emitted target inventory, not every paradigm in the vendored tables. For
   example, affirmative Spanish `habla` is a target tú command, while the
   identical present-indicative 3s analysis is outside the emitted present
   unit; its source count is therefore not divided for that analysis. Residual
   out-of-inventory verb, proper-name, noun/verb, tense/mood, sense, and
   tokenization ambiguity remains possible. This is a known overcounting edge,
   not evidence that the corpus identified an imperative token.
7. Transform the effective score with `log1p`, divide by the maximum
   transformed score inside that unit, and round to six decimals. This avoids
   letting a handful of subtitle forms erase the rest of a unit while
   retaining a strong frequency gradient. Unit maxima are `1.0`; weights from
   different units are not absolute frequencies and must not be compared as
   though their denominators were shared.

This policy intentionally leans toward underweighting. It divides `fui`
between the locally known *ser/ir* analyses and discounts known cross-POS
collisions rather than copying the whole orthographic count into every cell.
It still cannot prove which analysis every corpus token had. In particular,
the curated factors are review judgments, not a statistical tagger; `0.10`
was chosen as a conservative damping factor rather than estimated from labeled
data.

## Morphology-table limitations inherited by the weights

- French has 22 unavailable requested cells: all requested future,
  conditional, and subjunctive cells for defective `falloir`, plus four
  non-third-person future cells for `pleuvoir`. They are omitted, not emitted
  as zero-frequency forms.
- The French and Italian compound tables supply masculine participles. These
  weights therefore measure the stored masculine surfaces, not all agreement
  variants.
- Fifty-five Italian cells contain slash alternatives. The builder expands and
  sums them, but the current verifier compares against the literal slash form;
  later integration must reconcile that pre-existing verifier mismatch.
- The Portuguese table contains `imos` for present-indicative `ir` 1p and
  pre-reform spellings such as `vêem`/`lêem`. Weights follow the verifier's
  exact stored forms. A zero caused by a modern corpus miss must not be read as
  proof that the grammatical cell itself is rare.

## Sanity check: ten highest and lowest cells

These language-wide lists use the **pre-normalization effective score**;
per-unit JSON weights would make every unit maximum tie at `1.0` and are not a
valid language-wide ranking. Scores are comparable only within their language
and inherit the compound proxy described above. Equal zeroes are displayed in
reverse curriculum order solely to make the tie deterministic.

### Spanish

| # | Highest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `es_pres_irreg · ser · 3s` (*es*) | 698,024 | 1.000000 |
| 2 | `es_pres_irreg · estar · 3s` (*está*) | 131,753 | 0.876091 |
| 3 | `es_cmd_tu · estar · 2s` (*está*) | 131,753 | 1.000000 |
| 4 | `es_cmd_neg · ser · 3s` (*no sea*) | 109,892.746 | 1.000000 |
| 5 | `es_pres_irreg · estar · 1s` (*estoy*) | 108,899 | 0.861933 |
| 6 | `es_pres_irreg · ir · 1p` (*vamos*) | 107,551 | 0.861008 |
| 7 | `es_pres_irreg · estar · 2s` (*estás*) | 103,005 | 0.857798 |
| 8 | `es_pres_irreg · tener · 1s` (*tengo*) | 97,271 | 0.853542 |
| 9 | `es_pres_irreg · poder · 1s` (*puedo*) | 84,201 | 0.842818 |
| 10 | `es_pres_irreg · querer · 1s` (*quiero*) | 82,097 | 0.840938 |

| # | Lowest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `es_cmd_neg · construir · 2s` (*no construyas*) | 0 | 0.000000 |
| 2 | `es_cmd_neg · crear · 3p` (*no creen*) | 0 | 0.000000 |
| 3 | `es_cmd_neg · crear · 3s` (*no cree*) | 0 | 0.000000 |
| 4 | `es_cmd_neg · crear · 2s` (*no crees*) | 0 | 0.000000 |
| 5 | `es_cmd_neg · ser · 3p` (*no sean*) | 0 | 0.000000 |
| 6 | `es_cmd_usted · crear · 3p` (*creen*) | 0 | 0.000000 |
| 7 | `es_cmd_usted · crear · 1p` (*creemos*) | 0 | 0.000000 |
| 8 | `es_cmd_usted · crear · 3s` (*cree*) | 0 | 0.000000 |
| 9 | `es_cmd_usted · producir · 1p` (*produzcamos*) | 0 | 0.000000 |
| 10 | `es_cmd_usted · ser · 3p` (*sean*) | 0 | 0.000000 |

The commissioned spot check holds: `es_preterito · decir · 3s` (*dijo*) has
effective score 37,090 and unit weight `0.987188`, while
`es_futuro · traducir · 2p` (*traduciréis*) is unattested in the pinned list
and has weight `0.0`.

### French

| # | Highest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `fr_present_irreguliers · être · 3s` (*est*) | 22,530.984 | 1.000000 |
| 2 | `fr_present_irreguliers · avoir · 3s` (*a*) | 11,620.883 | 0.933945 |
| 3 | `fr_present_irreguliers · avoir · 1s` (*ai*) | 7,625.734 | 0.891918 |
| 4 | `fr_present_irreguliers · être · 1s` (*suis*) | 4,110.161 | 0.830262 |
| 5 | `fr_present_irreguliers · avoir · 2s` (*as*) | 3,237.209 | 0.806448 |
| 6 | `fr_present_irreguliers · aller · 3s` (*va*) | 3,137.911 | 0.803340 |
| 7 | `fr_imparfait · être · 3s` (*était*) | 3,110.731 | 1.000000 |
| 8 | `fr_present_irreguliers · être · 2s` (*es*) | 2,209 | 0.768331 |
| 9 | `fr_present_irreguliers · dire · 3s` (*dit*) | 2,182.177 | 0.767113 |
| 10 | `fr_passe_compose · faire · 3s` (*a fait*) | 2,150.785 | 1.000000 |

| # | Lowest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `fr_conditionnel_present · savoir · 2p` (*sauriez*) | 0 | 0.000000 |
| 2 | `fr_futur_simple · savoir · 2p` (*saurez*) | 0 | 0.000000 |
| 3 | `fr_conditionnel_present · envoyer · 1p` (*enverrions*) | 0.022 | 0.003586 |
| 4 | `fr_conditionnel_present · boire · 1p` (*boirions*) | 0.025 | 0.004069 |
| 5 | `fr_conditionnel_present · recevoir · 1p` (*recevrions*) | 0.025 | 0.004069 |
| 6 | `fr_conditionnel_present · tenir · 1p` (*tiendrions*) | 0.032 | 0.005191 |
| 7 | `fr_futur_simple · pleuvoir · 3p` (*pleuvront*) | 0.032 | 0.004885 |
| 8 | `fr_conditionnel_present · boire · 2p` (*boiriez*) | 0.044 | 0.007096 |
| 9 | `fr_conditionnel_present · boire · 3p` (*boiraient*) | 0.054 | 0.008667 |
| 10 | `fr_subjonctif_conjonctions · écrire · 1p` (*écrivions*) | 0.0555 | 0.008674 |

### Italian

| # | Highest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `it_presente_irregolari · essere · 3s` (*è*) | 2,559,257 | 1.000000 |
| 2 | `it_presente_irregolari · avere · 1s` (*ho*) | 1,823,350 | 0.977022 |
| 3 | `it_presente_irregolari · avere · 3s` (*ha*) | 1,662,783 | 0.970775 |
| 4 | `it_presente_irregolari · avere · 2s` (*hai*) | 1,037,387 | 0.938801 |
| 5 | `it_presente_irregolari · essere · 1s` (*sono*) | 1,002,589 | 0.936488 |
| 6 | `it_presente_irregolari · essere · 3p` (*sono*) | 1,002,589 | 0.936488 |
| 7 | `it_presente_irregolari · sapere · 1s` (*so*) | 576,344 | 0.898967 |
| 8 | `it_presente_irregolari · andare · 3s` (*va*) | 507,886 | 0.890397 |
| 9 | `it_presente_irregolari · stare · 3s` (*sta*) | 432,121 | 0.879449 |
| 10 | `it_passato_prossimo · fare · 1s` (*ho fatto*) | 426,655.853 | 1.000000 |

| # | Lowest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `it_congiuntivo_presente · tradurre · 2p` (*traduciate*) | 0 | 0.000000 |
| 2 | `it_imperfetto · tradurre · 2p` (*traducevate*) | 0 | 0.000000 |
| 3 | `it_imperfetto · tradurre · 2s` (*traducevi*) | 0 | 0.000000 |
| 4 | `it_passato_remoto · stare · 2s` (*stesti*) | 1 | 0.065520 |
| 5 | `it_congiuntivo_presente · trarre · 2p` (*traiate/traggiate/tragghiate*) | 1 | 0.056309 |
| 6 | `it_imperfetto · tradurre · 1p` (*traducevamo*) | 1 | 0.058296 |
| 7 | `it_imperfetto · trarre · 2p` (*traevate*) | 1 | 0.058296 |
| 8 | `it_imperfetto · porre · 2p` (*ponevate*) | 1 | 0.058296 |
| 9 | `it_congiuntivo_presente · tradurre · 3p` (*traducano*) | 2 | 0.089248 |
| 10 | `it_imperfetto · trarre · 1p` (*traevamo*) | 2 | 0.092397 |

### Brazilian Portuguese

| # | Highest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `pt_presente_irregulares · ser · 3s` (*é*) | 1,204,763 | 1.000000 |
| 2 | `pt_presente_irregulares · estar · 3s` (*está*) | 582,807 | 0.948137 |
| 3 | `pt_presente_irregulares · ter · 3s` (*tem*) | 237,371 | 0.883986 |
| 4 | `pt_presente_irregulares · ir · 3s` (*vai*) | 223,865 | 0.879802 |
| 5 | `pt_presente_irregulares · estar · 1s` (*estou*) | 196,172 | 0.870371 |
| 6 | `pt_presente_irregulares · ir · 1s` (*vou*) | 165,555 | 0.858252 |
| 7 | `pt_presente_irregulares · poder · 3s` (*pode*) | 163,061 | 0.857168 |
| 8 | `pt_presente_irregulares · saber · 1s` (*sei*) | 140,511 | 0.846538 |
| 9 | `pt_presente_irregulares · ter · 1s` (*tenho*) | 137,949 | 0.845224 |
| 10 | `pt_presente_irregulares · querer · 3s` (*quer*) | 132,104 | 0.842132 |

| # | Lowest cell (surface) | Effective score | Unit weight |
|---:|---|---:|---:|
| 1 | `pt_futuro_subjuntivo · conseguir · 3s` (*conseguir*) | 0 | 0.000000 |
| 2 | `pt_futuro_subjuntivo · conseguir · 1s` (*conseguir*) | 0 | 0.000000 |
| 3 | `pt_futuro_subjuntivo · sair · 3s` (*sair*) | 0 | 0.000000 |
| 4 | `pt_futuro_subjuntivo · sair · 1s` (*sair*) | 0 | 0.000000 |
| 5 | `pt_futuro_subjuntivo · pedir · 3s` (*pedir*) | 0 | 0.000000 |
| 6 | `pt_futuro_subjuntivo · pedir · 1s` (*pedir*) | 0 | 0.000000 |
| 7 | `pt_futuro_subjuntivo · ouvir · 3s` (*ouvir*) | 0 | 0.000000 |
| 8 | `pt_futuro_subjuntivo · ouvir · 1s` (*ouvir*) | 0 | 0.000000 |
| 9 | `pt_futuro_subjuntivo · ler · 3s` (*ler*) | 0 | 0.000000 |
| 10 | `pt_futuro_subjuntivo · ler · 1s` (*ler*) | 0 | 0.000000 |

## Later integration sketch (not implemented)

The generator should preselect exact cells with weighted sampling **without
replacement**; its current prompt forbids duplicate verb/person pairs. A small
exploration floor preserves pattern coverage while frequency remains the
cold-start prior:

```python
weights = load_freq_weights(topic.lang)[topic.key]
pool = [(v, p, w) for v, people in weights.items() for p, w in people.items()]
effective = [max(weight, 0.02) for _verb, _person, weight in pool]
targets = weighted_sample_without_replacement(pool, effective, n=count)
prompt = build_prompt(topic, count) + required_cells_block(targets)
raw = await gemini.generate(prompt, ...)
allowed = {(verb, person) for verb, person, _weight in targets}
items = [item for item in parse(raw) if cell(item) in allowed]
items = [item for item in items if morphology.verify(...)[0]]
record_generation_diagnostics(targets, items)
```

The `0.02` floor belongs to the later sampler, not these evidence files.

## Rebuild

```bash
python tools/build_freq_weights.py --build-date 2026-08-01
python tools/build_freq_weights.py --offline --build-date 2026-08-01
```

The first command downloads and checksum-verifies sources into
`${XDG_CACHE_HOME:-~/.cache}/idiomatic/frequency-weights/`; the second makes no
network request. With the same source cache and build date it writes
byte-identical JSON. `--cache-dir` relocates the cache, `--refresh` replaces it
only after the new download passes the pinned checksum, and `--summary`
reproduces the ranking tables. An empty `XDG_CACHE_HOME` is treated like an
unset value, so it cannot accidentally place downloads in the repository.
