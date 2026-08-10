# Exercises2 `cold_war_vocab` hostile audit

Date: 2026-08-10  
Auditor: Codex, independent post-authoring review  
Scope: all 30 `{de,es,fr,it,pt}_cold_war_vocab_b01..b06` chunks

## Outcome

All 30 chunks pass after audit. Twenty-one chunks required edits; nine passed without edits; none failed. The review covered every one of the 1,110 source/triage rows, all 526 drop rationales, and every field of all 584 retained V1 cards. Every retained item was examined for repetition; no sampling was used. The legacy `it_` prefix on item IDs was treated as the expected seed artifact because language routing comes from the chunk filename.

## Verdict table

| Chunk | Inputs | Keep | Drop | Verdict | Edited rows | Edited fields | Final gate |
|---|---:|---:|---:|---|---:|---:|---|
| `de_cold_war_vocab_b01` | 40 | 25 | 15 | PASS | 0 | 0 | PASS |
| `de_cold_war_vocab_b02` | 40 | 21 | 19 | PASS | 0 | 0 | PASS |
| `de_cold_war_vocab_b03` | 40 | 24 | 16 | PASS-WITH-EDITS | 1 | 4 | PASS |
| `de_cold_war_vocab_b04` | 40 | 27 | 13 | PASS-WITH-EDITS | 3 | 13 | PASS |
| `de_cold_war_vocab_b05` | 40 | 20 | 20 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `de_cold_war_vocab_b06` | 22 | 13 | 9 | PASS-WITH-EDITS | 1 | 4 | PASS |
| `es_cold_war_vocab_b01` | 40 | 18 | 22 | PASS | 0 | 0 | PASS |
| `es_cold_war_vocab_b02` | 40 | 16 | 24 | PASS-WITH-EDITS | 2 | 12 | PASS |
| `es_cold_war_vocab_b03` | 40 | 23 | 17 | PASS-WITH-EDITS | 1 | 4 | PASS |
| `es_cold_war_vocab_b04` | 40 | 27 | 13 | PASS-WITH-EDITS | 3 | 11 | PASS |
| `es_cold_war_vocab_b05` | 40 | 21 | 19 | PASS-WITH-EDITS | 1 | 2 | PASS |
| `es_cold_war_vocab_b06` | 22 | 10 | 12 | PASS-WITH-EDITS | 1 | 4 | PASS |
| `fr_cold_war_vocab_b01` | 40 | 18 | 22 | PASS-WITH-EDITS | 1 | 4 | PASS |
| `fr_cold_war_vocab_b02` | 40 | 18 | 22 | PASS-WITH-EDITS | 1 | 8 | PASS |
| `fr_cold_war_vocab_b03` | 40 | 23 | 17 | PASS-WITH-EDITS | 2 | 8 | PASS |
| `fr_cold_war_vocab_b04` | 40 | 30 | 10 | PASS-WITH-EDITS | 2 | 7 | PASS |
| `fr_cold_war_vocab_b05` | 40 | 19 | 21 | PASS | 0 | 0 | PASS |
| `fr_cold_war_vocab_b06` | 22 | 9 | 13 | PASS-WITH-EDITS | 1 | 3 | PASS |
| `it_cold_war_vocab_b01` | 40 | 18 | 22 | PASS | 0 | 0 | PASS |
| `it_cold_war_vocab_b02` | 40 | 15 | 25 | PASS-WITH-EDITS | 1 | 8 | PASS |
| `it_cold_war_vocab_b03` | 40 | 23 | 17 | PASS-WITH-EDITS | 3 | 9 | PASS |
| `it_cold_war_vocab_b04` | 40 | 30 | 10 | PASS-WITH-EDITS | 2 | 13 | PASS |
| `it_cold_war_vocab_b05` | 40 | 19 | 21 | PASS | 0 | 0 | PASS |
| `it_cold_war_vocab_b06` | 22 | 6 | 16 | PASS | 0 | 0 | PASS |
| `pt_cold_war_vocab_b01` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `pt_cold_war_vocab_b02` | 40 | 17 | 23 | PASS-WITH-EDITS | 2 | 12 | PASS |
| `pt_cold_war_vocab_b03` | 40 | 23 | 17 | PASS-WITH-EDITS | 1 | 4 | PASS |
| `pt_cold_war_vocab_b04` | 40 | 25 | 15 | PASS-WITH-EDITS | 3 | 12 | PASS |
| `pt_cold_war_vocab_b05` | 40 | 20 | 20 | PASS | 0 | 0 | PASS |
| `pt_cold_war_vocab_b06` | 22 | 6 | 16 | PASS-WITH-EDITS | 1 | 4 | PASS |
| **Total** | **1,110** | **584** | **526** | **30 pass** | **34** | **149** | **30/30** |

“Edited fields” counts changed JSON fields across notes and triage artifacts. Italian item 148 accounts for eight note fields plus one triage-reason field; the edited-row total counts that item once.

## Audit method and evidence

- Applied all six defect classes in `CODEX_X2_WAVE_AUDIT.md`, including an item-by-item repetition review rather than sampling.
- Checked every source row against its triage decision and every retained card against the V1 vocabulary schema in `EXERCISES2_VOCAB_ADDENDUM.md`: production headword, genuine alternatives, register, interference trap, target example, English translation, exact cloze reduction, and provenance note.
- Read all 526 drop reasons. Language-dependent keep/drop differences were reviewed against target-language teaching value and are justified. No keep/drop verdict changed; one keep rationale was corrected after its retained headword was repaired.
- Compared the estate with `exercises2_cross_topic_exact_duplicates.json`. All twelve rows assigned to `COLD_WAR_VOCAB` were retained in all five languages: 011 Capitalism, 016 Authoritarian, 026 Diplomacy, 030 Censorship, 032 Neoliberalism, 044 Ideology, 108 Surveillance, 114 Geopolitics, 115 Infrastructure, 123 Integration, 134 Espionage, and 149 Disinformation. `x2_wave_pipeline.py duplicate-report --check` verified the report.
- Reviewed all 584 interference traps. Six misleading or incomplete traps were repaired together with the affected headwords or term morphology.
- Verified all 584 clozes have valid syntax, blank the drilled material in the target example, and preserve the example otherwise. Thirty-four clozes were regenerated solely to stay aligned after substantive example or headword edits.
- Compared retained cards vertically across all five languages and checked every target example for repeated propositions, recycled frames, and within-sentence repetition. No duplicate target example exists. Recurrent register openers are categorical metadata, not recycled drilled content; identical English translations across language-specific cards do not create learner-visible repetition within any language.
- Reviewed politically loaded Cold-War framings for attribution and neutrality. Twenty-two examples were rewritten to distinguish advocacy, criticism, historiographic labels, or documentary attribution from narrator voice.
- Ran `.venv/bin/python tools/x2_batch_gate.py <chunk>` after every edited chunk and then across the full estate. Final result: `30/30 chunks pass the mechanical gate`.

## Historiographic terminology checks

- German `gegenseitig gesicherte Zerstörung` was checked against [Bundeszentrale für politische Bildung usage](https://www.bpb.de/shop/zeitschriften/apuz/archiv/534756/nationale-interessen-und-sicherheit-in-europa/); the authored inflected form `gegenseitige gesicherte` was corrected.
- Spanish `guerra por delegación` and `guerra subsidiaria` were both confirmed in [United Nations Spanish-language material](https://digitallibrary.un.org/record/409844/files/S_PV.4113-ES.pdf).
- Portuguese historical use of `détente` alongside explanatory `distensão` was confirmed in [Brazilian public-administration archival material](https://repositorio.enap.gov.br/bitstream/1/8127/4/1981%20RSP%20ano38%20v109%20n4%20out-dez%20ALL.pdf).
- Italian feminine treatment of `samba` was checked against the [Accademia della Crusca](https://accademiadellacrusca.it/it/consulenza/genere-dei-forestierismi/1229). Other named policies and periods, including `Glasnost`, `perestrojka/perestroïka/perestroika`, and `Entspannung`, were reviewed in context and retained in their established language-specific forms.

## Complete edit ledger

### `de_cold_war_vocab_b03`, item 084

Reason: Attribute a contested evaluation of developmentalism to supporters and critics rather than present it as settled narration.

- `example_tl`
  - Old: `Der Developmentalismus versprach, durch staatlich gelenkte Industrialisierung und Importsubstitution die Abhängigkeit Brasiliens zu verringern, verschärfte jedoch regionale und soziale Ungleichheiten.`
  - New: `Befürworter des Developmentalismus versprachen staatlich gelenkte Industrialisierung und geringere Abhängigkeit, während Kritiker auf wachsende regionale und soziale Ungleichheiten verwiesen.`
- `example_en`
  - Old: `Developmentalism promised to reduce Brazil's dependency through state-directed industrialization and import substitution, but it exacerbated regional and social inequalities.`
  - New: `Supporters of developmentalism promised state-directed industrialization and less dependency, while critics pointed to growing regional and social inequalities.`
- `cloze`
  - Old: `Der {{c1::Developmentalismus}} versprach, durch staatlich gelenkte Industrialisierung und Importsubstitution die Abhängigkeit Brasiliens zu verringern, verschärfte jedoch regionale und soziale Ungleichheiten.`
  - New: `Befürworter des {{c1::Developmentalismus}} versprachen staatlich gelenkte Industrialisierung und geringere Abhängigkeit, während Kritiker auf wachsende regionale und soziale Ungleichheiten verwiesen.`
- `note`
  - Old: `Materially corrects old_back, which mistranslates the concept as development aid. The alternative preserves the Spanish name used for the specifically Latin American programmatic tradition.`
  - New: `Materially corrects old_back, which mistranslates the concept as development aid. The alternative preserves the Spanish name used for the specifically Latin American programmatic tradition. Audit review attributed the contested assessment in the example.`

### `de_cold_war_vocab_b04`, item 140

Reason: Correct German adjective/adverb morphology in the established strategic term: gegenseitig modifies gesichert and remains uninflected.

- `tl`
  - Old: `die gegenseitige gesicherte Zerstörung (MAD)`
  - New: `die gegenseitig gesicherte Zerstörung (MAD)`
- `trap`
  - Old: `Assured here means made certain by survivable retaliation, so gesichert is correct; the legacy zugesichert wrongly suggests that destruction was verbally promised.`
  - New: `Gegenseitig modifies gesichert adverbially and therefore remains uninflected: die gegenseitig gesicherte Zerstörung, not *die gegenseitige gesicherte Zerstörung; MAD remains English.`
- `example_tl`
  - Old: `Die gegenseitige gesicherte Zerstörung beruhte auf der Fähigkeit beider Supermächte, selbst nach einem nuklearen Erstschlag noch vernichtend zurückzuschlagen.`
  - New: `Die gegenseitig gesicherte Zerstörung beruhte auf der Fähigkeit beider Supermächte, selbst nach einem nuklearen Erstschlag noch vernichtend zurückzuschlagen.`
- `cloze`
  - Old: `Die {{c1::gegenseitige gesicherte Zerstörung}} beruhte auf der Fähigkeit beider Supermächte, selbst nach einem nuklearen Erstschlag noch vernichtend zurückzuschlagen.`
  - New: `Die {{c1::gegenseitig gesicherte Zerstörung}} beruhte auf der Fähigkeit beider Supermächte, selbst nach einem nuklearen Erstschlag noch vernichtend zurückzuschlagen.`
- `note`
  - Old: `Materially corrects old_back to the established German strategic term; the headword retains MAD as the conventional identifying acronym.`
  - New: `Materially corrects old_back's zugesichert to the established German strategic term and, after audit, keeps adverbial gegenseitig uninflected; MAD remains the conventional identifying acronym.`

### `de_cold_war_vocab_b04`, item 144

Reason: Attribute the critical satellite-state label to Western analysis instead of presenting it as a neutral constitutional fact.

- `example_tl`
  - Old: `Als Satellitenstaat blieb die Republik formal souverän, doch ihre Außenpolitik, Sicherheitsorgane und wirtschaftlichen Prioritäten wurden maßgeblich von Moskau bestimmt.`
  - New: `In westlichen Analysen galt die Republik als Satellitenstaat, weil Moskau ihre Außenpolitik, Sicherheitsorgane und wirtschaftlichen Prioritäten trotz formaler Souveränität maßgeblich bestimmte.`
- `example_en`
  - Old: `As a satellite state, the republic remained formally sovereign, but its foreign policy, security organs and economic priorities were largely determined by Moscow.`
  - New: `In Western analyses, the republic was considered a satellite state because Moscow largely determined its foreign policy, security organs and economic priorities despite formal sovereignty.`
- `cloze`
  - Old: `Als {{c1::Satellitenstaat}} blieb die Republik formal souverän, doch ihre Außenpolitik, Sicherheitsorgane und wirtschaftlichen Prioritäten wurden maßgeblich von Moskau bestimmt.`
  - New: `In westlichen Analysen galt die Republik als {{c1::Satellitenstaat}}, weil Moskau ihre Außenpolitik, Sicherheitsorgane und wirtschaftlichen Prioritäten trotz formaler Souveränität maßgeblich bestimmte.`
- `note`
  - Old: `The legacy rendering is accurate; the register warning prevents the historical label from being presented as a value-neutral legal status.`
  - New: `The legacy rendering is accurate; the register warning prevents the historical label from being presented as a value-neutral legal status, and audit review attributed that label in the example.`

### `de_cold_war_vocab_b04`, item 158

Reason: Replace an unattributed causal judgment about perestroika with explicitly opposed supporter and critic positions.

- `example_tl`
  - Old: `Die Perestroika sollte die sowjetische Wirtschaft erneuern, legte jedoch institutionelle Widersprüche offen, die weder administrative Reformen noch begrenzte Marktmechanismen rasch lösen konnten.`
  - New: `Befürworter der Perestroika wollten die sowjetische Wirtschaft erneuern, während Kritiker vor institutionellen Widersprüchen und den politischen Folgen begrenzter Marktmechanismen warnten.`
- `example_en`
  - Old: `Perestroika was intended to renew the Soviet economy but exposed institutional contradictions that neither administrative reforms nor limited market mechanisms could quickly resolve.`
  - New: `Supporters of perestroika wanted to renew the Soviet economy, while critics warned of institutional contradictions and the political consequences of limited market mechanisms.`
- `cloze`
  - Old: `Die {{c1::Perestroika}} sollte die sowjetische Wirtschaft erneuern, legte jedoch institutionelle Widersprüche offen, die weder administrative Reformen noch begrenzte Marktmechanismen rasch lösen konnten.`
  - New: `Befürworter der {{c1::Perestroika}} wollten die sowjetische Wirtschaft erneuern, während Kritiker vor institutionellen Widersprüchen und den politischen Folgen begrenzter Marktmechanismen warnten.`
- `note`
  - Old: `The legacy headword is accurate; the explanatory parenthesis is omitted from the production form and supplied through the usage fields.`
  - New: `The legacy headword is accurate; the explanatory parenthesis is omitted from the production form and supplied through the usage fields. Audit review replaced an unattributed causal assessment in the example.`

### `de_cold_war_vocab_b05`, item 187

Reason: Remove the conspicuous same-stem agent/action repetition Unterhändler verhandelten.

- `example_tl`
  - Old: `Die Unterhändler verhandelten mit der Gegenseite über Gefangenenaustausche, während beide Regierungen öffentlich bestritten, überhaupt direkte Gespräche miteinander zu führen.`
  - New: `Die Delegationen verhandelten mit der Gegenseite über Gefangenenaustausche, während beide Regierungen öffentlich bestritten, überhaupt direkte Gespräche miteinander zu führen.`
- `example_en`
  - Old: `The negotiators negotiated with the other side over prisoner exchanges while both governments publicly denied that they were holding direct talks at all.`
  - New: `The delegations negotiated with the other side over prisoner exchanges while both governments publicly denied that they were holding direct talks at all.`
- `cloze`
  - Old: `Die Unterhändler {{c1::verhandelten mit}} der Gegenseite {{c1::über}} Gefangenenaustausche, während beide Regierungen öffentlich bestritten, überhaupt direkte Gespräche miteinander zu führen.`
  - New: `Die Delegationen {{c1::verhandelten mit}} der Gegenseite {{c1::über}} Gefangenenaustausche, während beide Regierungen öffentlich bestritten, überhaupt direkte Gespräche miteinander zu führen.`

### `de_cold_war_vocab_b06`, item 216

Reason: Attribute the specific espionage claim to declassified files.

- `example_tl`
  - Old: `Vom Ausland gesteuerte Agentennetzwerke drangen in zentrale Ministerien ein und verschafften sich über Jahre Zugang zu vertraulichen Verhandlungsunterlagen.`
  - New: `Laut freigegebenen Akten drangen vom Ausland gesteuerte Agentennetzwerke in zentrale Ministerien ein und erlangten Zugang zu vertraulichen Verhandlungsunterlagen.`
- `example_en`
  - Old: `Foreign-controlled agent networks penetrated key ministries and gained access to confidential negotiating documents over a period of years.`
  - New: `According to declassified files, foreign-controlled agent networks penetrated key ministries and gained access to confidential negotiating documents.`
- `cloze`
  - Old: `Vom Ausland gesteuerte Agentennetzwerke {{c1::drangen}} {{c1::in}} zentrale Ministerien {{c1::ein}} und verschafften sich über Jahre Zugang zu vertraulichen Verhandlungsunterlagen.`
  - New: `Laut freigegebenen Akten {{c1::drangen}} vom Ausland gesteuerte Agentennetzwerke {{c1::in}} zentrale Ministerien {{c1::ein}} und erlangten Zugang zu vertraulichen Verhandlungsunterlagen.`
- `note`
  - Old: `The isolated source is polysemous. This card selects covert institutional entry; self-review supplied the governed preposition omitted by the legacy infinitive.`
  - New: `The isolated source is polysemous. This card selects covert institutional entry; self-review supplied the governed preposition omitted by the legacy infinitive. Audit review attributed the historical claim to declassified files.`

### `es_cold_war_vocab_b02`, item 046

Reason: Attribute the politically loaded historical assessment of U.S. interventionism.

- `example_tl`
  - Old: `El intervencionismo de Washington debilitó a gobiernos electos y alimentó un antiamericanismo que sobrevivió mucho después del final de la Guerra Fría.`
  - New: `Diversos historiadores han vinculado el intervencionismo de Washington con el debilitamiento de gobiernos elegidos y con un antiamericanismo que perduró tras la Guerra Fría.`
- `example_en`
  - Old: `Washington's interventionism weakened elected governments and fueled anti-Americanism that survived long after the end of the Cold War.`
  - New: `Various historians have linked Washington's interventionism to the weakening of elected governments and to anti-Americanism that endured after the Cold War.`
- `cloze`
  - Old: `{{c1::El intervencionismo}} de Washington debilitó a gobiernos electos y alimentó un antiamericanismo que sobrevivió mucho después del final de la Guerra Fría.`
  - New: `Diversos historiadores han vinculado {{c1::el intervencionismo}} de Washington con el debilitamiento de gobiernos elegidos y con un antiamericanismo que perduró tras la Guerra Fría.`
- `note`
  - Old: `Old_back has the correct lexeme but incorrectly capitalizes the common noun; the example fixes the foreign-policy sense.`
  - New: `Old_back has the correct lexeme but incorrectly capitalizes the common noun; the example fixes the foreign-policy sense and, after audit, attributes its historical assessment.`

### `es_cold_war_vocab_b02`, item 061

Reason: Correct a false-friend semantic shift: militancia means organized activism or affiliation, while the English prompt asks for combative militancy.

- `tl`
  - Old: `la militancia política`
  - New: `la combatividad`
- `alts`
  - Old: `[]`
  - New: `["la actitud combativa"]`
- `register`
  - Old: `Término neutral-formal para la pertenencia activa y sostenida a un partido o movimiento; no implica por sí mismo violencia ni extremismo.`
  - New: `Término neutral-formal para una disposición firme y confrontativa en la acción política, sindical o social; puede ser retórico y no implica necesariamente violencia.`
- `trap`
  - Old: `El inglés militancy suele destacar una actitud combativa; la militancia española normalmente alude a afiliación o activismo organizado, y ese falso paralelo puede alterar el sentido.`
  - New: `La militancia española suele aludir a afiliación o activismo organizado y no equivale al inglés militancy cuando este destaca una postura combativa.`
- `example_tl`
  - Old: `La militancia política sostuvo redes clandestinas de prensa y solidaridad, aunque el exilio y la represión redujeron drásticamente la capacidad organizativa de los partidos.`
  - New: `La combatividad del sindicato aumentó tras fracasar las negociaciones, aunque sus dirigentes siguieron rechazando explícitamente la violencia política.`
- `example_en`
  - Old: `Party activism sustained clandestine press and solidarity networks, although exile and repression drastically reduced the parties' organizational capacity.`
  - New: `The union's militancy increased after negotiations failed, although its leaders continued explicitly to reject political violence.`
- `cloze`
  - Old: `{{c1::La militancia política}} sostuvo redes clandestinas de prensa y solidaridad, aunque el exilio y la represión redujeron drásticamente la capacidad organizativa de los partidos.`
  - New: `{{c1::La combatividad}} del sindicato aumentó tras fracasar las negociaciones, aunque sus dirigentes siguieron rechazando explícitamente la violencia política.`
- `note`
  - Old: `Materially sharpens old_back by making the political-participation sense explicit. If the English prompt intended aggressive conduct instead, combatividad would be preferable; the source cluster supports the Romance political sense.`
  - New: `Materially corrects the false-friend legacy rendering: Spanish militancia normally means membership or organized activism, whereas the English prompt foregrounds a combative posture.`

### `es_cold_war_vocab_b03`, item 084

Reason: Attribute the contested assessment of Brazilian developmentalism to supporters and critics.

- `example_tl`
  - Old: `El desarrollismo brasileño confió al Estado la industrialización acelerada, pero la expansión productiva no corrigió la desigualdad social ni la dependencia tecnológica.`
  - New: `Los defensores del desarrollismo brasileño destacaban la industrialización dirigida por el Estado, mientras sus críticos señalaban que persistían la desigualdad social y la dependencia tecnológica.`
- `example_en`
  - Old: `Brazilian developmentalism entrusted the state with accelerated industrialization, but productive expansion did not correct social inequality or technological dependence.`
  - New: `Supporters of Brazilian developmentalism emphasized state-directed industrialization, while its critics pointed out that social inequality and technological dependence persisted.`
- `cloze`
  - Old: `{{c1::El desarrollismo}} brasileño confió al Estado la industrialización acelerada, pero la expansión productiva no corrigió la desigualdad social ni la dependencia tecnológica.`
  - New: `Los defensores {{c1::del desarrollismo}} brasileño destacaban la industrialización dirigida por el Estado, mientras sus críticos señalaban que persistían la desigualdad social y la dependencia tecnológica.`
- `note`
  - Old: `Old_back gives the correct specialist term but unnecessarily capitalizes the common noun. The alternative makes the model reading explicit without reducing the concept to development in general.`
  - New: `Old_back gives the correct specialist term but unnecessarily capitalizes the common noun. The alternative makes the model reading explicit without reducing the concept to development in general. Audit review attributed the contested assessment in the example.`

### `es_cold_war_vocab_b04`, item 131

Reason: Remove the repeated escolar in one short sentence without changing the educational context.

- `example_tl`
  - Old: `El analfabetismo persistió en zonas rurales donde la expansión escolar no vino acompañada de plantillas docentes estables, transporte escolar ni materiales suficientes.`
  - New: `El analfabetismo persistió en zonas rurales donde la expansión escolar no vino acompañada de plantillas docentes estables, transporte para el alumnado ni materiales suficientes.`
- `example_en`
  - Old: `Illiteracy persisted in rural areas where school expansion was not accompanied by stable teaching staff, school transport, or sufficient materials.`
  - New: `Illiteracy persisted in rural areas where school expansion was not accompanied by stable teaching staff, transport for pupils, or sufficient materials.`
- `cloze`
  - Old: `{{c1::El analfabetismo}} persistió en zonas rurales donde la expansión escolar no vino acompañada de plantillas docentes estables, transporte escolar ni materiales suficientes.`
  - New: `{{c1::El analfabetismo}} persistió en zonas rurales donde la expansión escolar no vino acompañada de plantillas docentes estables, transporte para el alumnado ni materiales suficientes.`

### `es_cold_war_vocab_b04`, item 144

Reason: Attribute the critical satellite-state label to Western studies.

- `example_tl`
  - Old: `Como Estado satélite, el país conservaba instituciones propias, pero Moscú condicionaba su política exterior, su aparato de seguridad y sus prioridades económicas.`
  - New: `En numerosos estudios occidentales, el país fue descrito como Estado satélite porque Moscú condicionaba su política exterior, su aparato de seguridad y sus prioridades económicas.`
- `example_en`
  - Old: `As a satellite state, the country retained its own institutions, but Moscow shaped its foreign policy, security apparatus, and economic priorities.`
  - New: `In many Western studies, the country was described as a satellite state because Moscow shaped its foreign policy, security apparatus, and economic priorities.`
- `cloze`
  - Old: `Como {{c1::Estado satélite}}, el país conservaba instituciones propias, pero Moscú condicionaba su política exterior, su aparato de seguridad y sus prioridades económicas.`
  - New: `En numerosos estudios occidentales, el país fue descrito como {{c1::Estado satélite}} porque Moscú condicionaba su política exterior, su aparato de seguridad y sus prioridades económicas.`
- `note`
  - Old: `Old_back is accurate. The register warning prevents the historical label from being taught as a value-neutral constitutional status.`
  - New: `Old_back is accurate. The register warning prevents the historical label from being taught as a value-neutral constitutional status, and audit review attributed that label in the example.`

### `es_cold_war_vocab_b04`, item 158

Reason: Replace an unattributed causal judgment about perestroika with explicitly opposed supporter and critic positions.

- `example_tl`
  - Old: `La perestroika intentó reformar la economía soviética mediante mayor autonomía empresarial, pero agravó desequilibrios que el sistema administrativo había mantenido ocultos.`
  - New: `Los partidarios de la perestroika buscaban reformar la economía soviética mediante mayor autonomía empresarial, mientras sus críticos advertían que las reformas podían agravar los desequilibrios existentes.`
- `example_en`
  - Old: `Perestroika sought to reform the Soviet economy through greater enterprise autonomy, but it worsened imbalances that the administrative system had kept hidden.`
  - New: `Supporters of perestroika sought to reform the Soviet economy through greater enterprise autonomy, while critics warned that the reforms could worsen existing imbalances.`
- `cloze`
  - Old: `{{c1::La perestroika}} intentó reformar la economía soviética mediante mayor autonomía empresarial, pero agravó desequilibrios que el sistema administrativo había mantenido ocultos.`
  - New: `Los partidarios {{c1::de la perestroika}} buscaban reformar la economía soviética mediante mayor autonomía empresarial, mientras sus críticos advertían que las reformas podían agravar los desequilibrios existentes.`
- `note`
  - Old: `Materially normalizes old_back's capitalization and removes the explanatory parenthesis from the production headword.`
  - New: `Materially normalizes old_back's capitalization and removes the explanatory parenthesis from the production headword. Audit review replaced an unattributed causal assessment in the example.`

### `es_cold_war_vocab_b05`, item 164

Reason: Remove the distracting Durante ... durante repetition.

- `example_tl`
  - Old: `Durante los años cincuenta, los ensayos nucleares expusieron a comunidades lejanas a partículas radiactivas, mientras las potencias minimizaron durante décadas los daños sanitarios.`
  - New: `En los años cincuenta, los ensayos nucleares expusieron a comunidades lejanas a partículas radiactivas, mientras las potencias minimizaron durante décadas los daños sanitarios.`
- `cloze`
  - Old: `Durante los años cincuenta, {{c1::los ensayos nucleares}} expusieron a comunidades lejanas a partículas radiactivas, mientras las potencias minimizaron durante décadas los daños sanitarios.`
  - New: `En los años cincuenta, {{c1::los ensayos nucleares}} expusieron a comunidades lejanas a partículas radiactivas, mientras las potencias minimizaron durante décadas los daños sanitarios.`

### `es_cold_war_vocab_b06`, item 202

Reason: Attribute the specific covert-intervention claim to declassified documents.

- `example_tl`
  - Old: `Las redes financiadas desde el exterior intentaron subvertir el orden constitucional mediante campañas clandestinas, pero sus vínculos con los servicios secretos quedaron expuestos.`
  - New: `Según documentos desclasificados, unas redes financiadas desde el exterior intentaron subvertir el orden constitucional mediante campañas clandestinas vinculadas con servicios de inteligencia extranjeros.`
- `example_en`
  - Old: `Foreign-funded networks attempted to subvert the constitutional order through covert campaigns, but their links to the intelligence services were exposed.`
  - New: `According to declassified documents, foreign-funded networks attempted to subvert the constitutional order through covert campaigns linked to foreign intelligence services.`
- `cloze`
  - Old: `Las redes financiadas desde el exterior intentaron {{c1::subvertir}} el orden constitucional mediante campañas clandestinas, pero sus vínculos con los servicios secretos quedaron expuestos.`
  - New: `Según documentos desclasificados, unas redes financiadas desde el exterior intentaron {{c1::subvertir}} el orden constitucional mediante campañas clandestinas vinculadas con servicios de inteligencia extranjeros.`
- `note`
  - Old: `Old_back gives the correct infinitive. Self-review added the irregular conjugation and distinguished this direct alteration of an established order from the gradual erosion expressed by socavar in item 222.`
  - New: `Old_back gives the correct infinitive. Self-review added the irregular conjugation and distinguished this direct alteration of an established order from the gradual erosion expressed by socavar in item 222. Audit review attributed the historical claim to declassified documents.`

### `fr_cold_war_vocab_b01`, item 011

Reason: Attribute the contested inequality assessment to defenders and critics of capitalism.

- `example_tl`
  - Old: `Le capitalisme a survécu à la guerre froide en se transformant, sans pour autant réduire les inégalités que ses défenseurs promettaient d’atténuer.`
  - New: `Les défenseurs du capitalisme soulignaient sa capacité d’adaptation, tandis que ses critiques estimaient qu’il ne réduisait pas les inégalités sociales.`
- `example_en`
  - Old: `Capitalism survived the Cold War by transforming itself, without thereby reducing the inequalities its defenders promised to alleviate.`
  - New: `Defenders of capitalism emphasized its capacity to adapt, while its critics argued that it did not reduce social inequalities.`
- `cloze`
  - Old: `{{c1::Le capitalisme}} a survécu à la guerre froide en se transformant, sans pour autant réduire les inégalités que ses défenseurs promettaient d’atténuer.`
  - New: `Les défenseurs {{c1::du capitalisme}} soulignaient sa capacité d’adaptation, tandis que ses critiques estimaient qu’il ne réduisait pas les inégalités sociales.`
- `note`
  - Old: `Retained in COLD_WAR_VOCAB under the exact-duplicate report rather than in FANCY_VOCAB. Old_back is accurate.`
  - New: `Retained in COLD_WAR_VOCAB under the exact-duplicate report rather than in FANCY_VOCAB. Old_back is accurate; audit review attributed the contested assessment in the example.`

### `fr_cold_war_vocab_b02`, item 061

Reason: Correct a false-friend semantic shift: militantisme normally denotes activism, while the English prompt asks for combativeness.

- `tl`
  - Old: `le militantisme`
  - New: `la combativité`
- `alts`
  - Old: `[]`
  - New: `["l’attitude combative"]`
- `register`
  - Old: `Neutral term for sustained activist or party engagement; the surrounding noun or adjective normally identifies the cause or organization.`
  - New: `Neutral-formal term for a firm, confrontational disposition in political, trade-union, or social action; it can be rhetorical and does not necessarily imply violence.`
- `trap`
  - Old: `English militancy often suggests aggressiveness, whereas French militantisme can describe peaceful activism; combativité is preferable when confrontation itself is central.`
  - New: `French militantisme usually denotes organized activism and is weaker than English militancy when the latter foregrounds a combative posture.`
- `example_tl`
  - Old: `Le militantisme syndical s’est intensifié dans les mines, où les revendications salariales se mêlaient désormais à une contestation plus large du régime.`
  - New: `La combativité du syndicat s’est accrue après l’échec des négociations, bien que ses dirigeants aient continué de rejeter explicitement la violence politique.`
- `example_en`
  - Old: `Trade-union activism intensified in the mines, where wage demands were now merging with a broader challenge to the regime.`
  - New: `The union's militancy increased after negotiations failed, although its leaders continued explicitly to reject political violence.`
- `cloze`
  - Old: `{{c1::Le militantisme}} syndical s’est intensifié dans les mines, où les revendications salariales se mêlaient désormais à une contestation plus large du régime.`
  - New: `{{c1::La combativité}} du syndicat s’est accrue après l’échec des négociations, bien que ses dirigeants aient continué de rejeter explicitement la violence politique.`
- `note`
  - Old: `Old_back gives the intended French term, but the English prompt is potentially stronger; the example fixes the organized-activism sense inherited from the source sequence.`
  - New: `Materially corrects the false-friend legacy rendering: French militantisme normally means organized activism, whereas the English prompt foregrounds a combative posture.`

### `fr_cold_war_vocab_b03`, item 084

Reason: Attribute the contested assessment of Brazilian developmentalism to supporters and critics.

- `example_tl`
  - Old: `Le développementalisme brésilien associait planification étatique, protection du marché intérieur et industrialisation rapide, au nom d’une autonomie économique encore largement inachevée.`
  - New: `Les partisans du développementalisme brésilien mettaient en avant la planification étatique et l’industrialisation rapide, tandis que ses critiques jugeaient l’autonomie économique promise encore inachevée.`
- `example_en`
  - Old: `Brazilian developmentalism combined state planning, protection of the domestic market, and rapid industrialization in the name of an economic autonomy that remained largely unrealized.`
  - New: `Supporters of Brazilian developmentalism emphasized state planning and rapid industrialization, while its critics considered the promised economic autonomy still unrealized.`
- `cloze`
  - Old: `{{c1::Le développementalisme}} brésilien associait planification étatique, protection du marché intérieur et industrialisation rapide, au nom d’une autonomie économique encore largement inachevée.`
  - New: `Les partisans {{c1::du développementalisme}} brésilien mettaient en avant la planification étatique et l’industrialisation rapide, tandis que ses critiques jugeaient l’autonomie économique promise encore inachevée.`
- `note`
  - Old: `Old_back gives the accepted headword. Self-review retained développementisme only as an established variant and made the doctrine, rather than generic development, explicit.`
  - New: `Old_back gives the accepted headword. Self-review retained développementisme only as an established variant and made the doctrine, rather than generic development, explicit. Audit review attributed the contested assessment in the example.`

### `fr_cold_war_vocab_b03`, item 111

Reason: Attribute both the celebratory label and the later critical assessment, and remove the croissance ... croissant same-stem repetition.

- `example_tl`
  - Old: `Le prétendu miracle économique a affiché une croissance spectaculaire, mais cette performance a surtout enrichi les élites tout en reposant sur un endettement extérieur croissant.`
  - New: `Ce que le régime appelait le « miracle économique » a produit une expansion spectaculaire, mais des études ont montré que les gains profitaient surtout aux élites et dépendaient de l’endettement extérieur.`
- `example_en`
  - Old: `The so-called economic miracle posted spectacular growth, but that performance mainly enriched the elites while relying on rising external debt.`
  - New: `What the regime called the “economic miracle” produced spectacular expansion, but studies showed that the gains mainly benefited elites and depended on external debt.`
- `cloze`
  - Old: `Le prétendu {{c1::miracle économique}} a affiché une croissance spectaculaire, mais cette performance a surtout enrichi les élites tout en reposant sur un endettement extérieur croissant.`
  - New: `Ce que le régime appelait le « {{c1::miracle économique}} » a produit une expansion spectaculaire, mais des études ont montré que les gains profitaient surtout aux élites et dépendaient de l’endettement extérieur.`
- `note`
  - Old: `Old_back gives the established phrase. Self-review added prétendu for critical distance and replaced the awkward bénéfices concentrés with a clearer distributional claim.`
  - New: `Old_back gives the established phrase. Audit review attributed both the celebratory label and the later distributional assessment, while removing a repeated growth word family.`

### `fr_cold_war_vocab_b04`, item 142

Reason: Remove the repeated capacité while preserving the distinction between retaliatory capability and willingness to use it.

- `example_tl`
  - Old: `La dissuasion exigeait que l’adversaire croie à la capacité de riposte, mais aussi à la volonté politique d’employer effectivement cette capacité.`
  - New: `La dissuasion exigeait que l’adversaire croie à la capacité de riposte, mais aussi à la volonté politique d’y recourir effectivement.`
- `example_en`
  - Old: `Deterrence required the adversary to believe in both the capacity to retaliate and the political will actually to use that capacity.`
  - New: `Deterrence required the adversary to believe in both the capacity to retaliate and the political will actually to use it.`
- `cloze`
  - Old: `{{c1::La dissuasion}} exigeait que l’adversaire croie à la capacité de riposte, mais aussi à la volonté politique d’employer effectivement cette capacité.`
  - New: `{{c1::La dissuasion}} exigeait que l’adversaire croie à la capacité de riposte, mais aussi à la volonté politique d’y recourir effectivement.`

### `fr_cold_war_vocab_b04`, item 158

Reason: Replace unqualified narration about perestroika with explicitly opposed supporter and critic positions.

- `example_tl`
  - Old: `La perestroïka a tenté de réformer l’économie soviétique sans démanteler immédiatement les structures politiques qui entravaient l’initiative et protégeaient les bureaucraties établies.`
  - New: `Les partisans de la perestroïka voulaient réformer l’économie soviétique, tandis que ses critiques craignaient que les changements n’affaiblissent les institutions sans résoudre les blocages existants.`
- `example_en`
  - Old: `Perestroika attempted to reform the Soviet economy without immediately dismantling the political structures that hindered initiative and protected established bureaucracies.`
  - New: `Supporters of perestroika wanted to reform the Soviet economy, while its critics feared that the changes would weaken institutions without resolving existing bottlenecks.`
- `cloze`
  - Old: `{{c1::La perestroïka}} a tenté de réformer l’économie soviétique sans démanteler immédiatement les structures politiques qui entravaient l’initiative et protégeaient les bureaucraties établies.`
  - New: `Les partisans {{c1::de la perestroïka}} voulaient réformer l’économie soviétique, tandis que ses critiques craignaient que les changements n’affaiblissent les institutions sans résoudre les blocages existants.`
- `note`
  - Old: `Old_back has the correct French spelling but treats restructuration as if it were part of the headword. Self-review kept the gloss in the register explanation instead.`
  - New: `Old_back has the correct French spelling but treats restructuration as if it were part of the headword. Self-review kept the gloss in the register explanation instead. Audit review replaced an unattributed causal assessment in the example.`

### `fr_cold_war_vocab_b06`, item 210

Reason: Correct industriels, which denotes industrialists, where the English and context require industrial sectors or firms.

- `example_tl`
  - Old: `Après l’essai nucléaire, plusieurs gouvernements ont imposé de nouvelles restrictions commerciales au régime, malgré les réserves de leurs industriels les plus exposés.`
  - New: `Après l’essai nucléaire, plusieurs gouvernements ont imposé de nouvelles restrictions commerciales au régime, malgré les réserves de leurs secteurs industriels les plus exposés.`
- `example_en`
  - Old: `After the nuclear test, several governments imposed new trade restrictions on the regime, despite reservations from the industrial firms in their countries most exposed to the measures.`
  - New: `After the nuclear test, several governments imposed new trade restrictions on the regime, despite reservations from their most exposed industrial sectors.`
- `cloze`
  - Old: `Après l’essai nucléaire, plusieurs gouvernements ont {{c1::imposé}} de nouvelles restrictions commerciales {{c1::au}} régime, malgré les réserves de leurs industriels les plus exposés.`
  - New: `Après l’essai nucléaire, plusieurs gouvernements ont {{c1::imposé}} de nouvelles restrictions commerciales {{c1::au}} régime, malgré les réserves de leurs secteurs industriels les plus exposés.`

### `it_cold_war_vocab_b02`, item 061

Reason: Correct a false-friend semantic shift: militanza normally denotes organized activism or affiliation, while the English prompt asks for combativeness.

- `tl`
  - Old: `la militanza politica`
  - New: `la combattività`
- `alts`
  - Old: `["l'impegno militante"]`
  - New: `["l'atteggiamento combattivo"]`
- `register`
  - Old: `Termine neutro-formale per la partecipazione attiva e continuativa a un partito o movimento; non implica di per sé violenza o estremismo.`
  - New: `Termine neutro-formale per una disposizione ferma e conflittuale nell'azione politica, sindacale o sociale; può essere retorica e non implica necessariamente violenza.`
- `trap`
  - Old: `L'inglese militancy sottolinea spesso la combattività; l'italiano militanza indica normalmente appartenenza e attivismo organizzato, creando un falso parallelismo semantico.`
  - New: `L'italiano militanza indica normalmente appartenenza o attivismo organizzato e non equivale all'inglese militancy quando questo sottolinea una postura combattiva.`
- `example_tl`
  - Old: `La militanza politica mantenne attive reti clandestine di stampa e solidarietà, sebbene l'esilio avesse drasticamente ridotto la capacità organizzativa dei partiti.`
  - New: `La combattività del sindacato aumentò dopo il fallimento dei negoziati, sebbene i dirigenti continuassero a respingere esplicitamente la violenza politica.`
- `example_en`
  - Old: `Political activism kept clandestine press and solidarity networks active, although exile had drastically reduced the parties' organizational capacity.`
  - New: `The union's militancy increased after negotiations failed, although its leaders continued explicitly to reject political violence.`
- `cloze`
  - Old: `{{c1::La militanza politica}} mantenne attive reti clandestine di stampa e solidarietà, sebbene l'esilio avesse drasticamente ridotto la capacità organizzativa dei partiti.`
  - New: `{{c1::La combattività}} del sindacato aumentò dopo il fallimento dei negoziati, sebbene i dirigenti continuassero a respingere esplicitamente la violenza politica.`
- `note`
  - Old: `Materially sharpens old_back by fixing the political-participation sense. If the English prompt intended aggressive conduct instead, combattività would be preferable; the source cluster supports the Romance political sense.`
  - New: `Materially corrects the false-friend legacy rendering: Italian militanza normally means membership or organized activism, whereas the English prompt foregrounds a combative posture.`

### `it_cold_war_vocab_b03`, item 084

Reason: Attribute the contested assessment of military-government developmentalism to supporters and critics.

- `example_tl`
  - Old: `Lo sviluppismo dei governi militari privilegiò grandi opere e crescita industriale, relegando la tutela ambientale e la redistribuzione del reddito ai margini.`
  - New: `I sostenitori dello sviluppismo dei governi militari esaltavano le grandi opere e la crescita industriale, mentre i critici denunciavano la scarsa tutela ambientale e la debole redistribuzione del reddito.`
- `example_en`
  - Old: `The military governments' developmentalism prioritized major projects and industrial growth, relegating environmental protection and income redistribution to the margins.`
  - New: `Supporters of the military governments' developmentalism praised major projects and industrial growth, while critics denounced weak environmental protection and limited income redistribution.`
- `cloze`
  - Old: `{{c1::Lo sviluppismo}} dei governi militari privilegiò grandi opere e crescita industriale, relegando la tutela ambientale e la redistribuzione del reddito ai margini.`
  - New: `I sostenitori {{c1::dello sviluppismo}} dei governi militari esaltavano le grandi opere e la crescita industriale, mentre i critici denunciavano la scarsa tutela ambientale e la debole redistribuzione del reddito.`
- `note`
  - Old: `Old_back identifies the established Italian term. Self-review made its frequent critical connotation explicit so it is not learned as a neutral synonym of sviluppo.`
  - New: `Old_back identifies the established Italian term. Self-review made its frequent critical connotation explicit so it is not learned as a neutral synonym of sviluppo. Audit review attributed the contested assessment in the example.`

### `it_cold_war_vocab_b03`, item 092

Reason: Avoid treating the whole economic elite as a single political actor.

- `example_tl`
  - Old: `L'élite economica sostenne inizialmente il golpe, confidando che i militari avrebbero ristabilito l'ordine senza alterare gli assetti proprietari del paese.`
  - New: `Una parte dell'élite economica sostenne inizialmente il golpe, confidando che i militari avrebbero ristabilito l'ordine senza alterare gli assetti proprietari del paese.`
- `example_en`
  - Old: `The economic elite initially supported the coup, trusting that the military would restore order without altering the country's ownership structure.`
  - New: `Part of the economic elite initially supported the coup, trusting that the military would restore order without altering the country's ownership structure.`
- `cloze`
  - Old: `{{c1::L'élite}} economica sostenne inizialmente il golpe, confidando che i militari avrebbero ristabilito l'ordine senza alterare gli assetti proprietari del paese.`
  - New: `Una parte {{c1::dell'élite}} economica sostenne inizialmente il golpe, confidando che i militari avrebbero ristabilito l'ordine senza alterare gli assetti proprietari del paese.`

### `it_cold_war_vocab_b03`, item 105

Reason: Remove the conspicuous same-stem repetition organizzò ... organismi.

- `example_tl`
  - Old: `Il corporativismo organizzò lavoratori e imprenditori in organismi controllati dallo Stato, presentando la repressione del conflitto sociale come collaborazione nazionale.`
  - New: `Il corporativismo raggruppò lavoratori e imprenditori in organismi controllati dallo Stato, presentando la repressione del conflitto sociale come collaborazione nazionale.`
- `cloze`
  - Old: `{{c1::Il corporativismo}} organizzò lavoratori e imprenditori in organismi controllati dallo Stato, presentando la repressione del conflitto sociale come collaborazione nazionale.`
  - New: `{{c1::Il corporativismo}} raggruppò lavoratori e imprenditori in organismi controllati dallo Stato, presentando la repressione del conflitto sociale come collaborazione nazionale.`

### `it_cold_war_vocab_b04`, item 148

Reason: Correct the definite English noun from an abstract condition to the covert political movement or network it denotes; align the triage rationale as well.

- `tl`
  - Old: `la clandestinità`
  - New: `il movimento clandestino`
- `alts`
  - Old: `[]`
  - New: `["la resistenza clandestina"]`
- `register`
  - Old: `Termine neutro-formale per la condizione e l'insieme delle pratiche di chi svolge attività politica illegalmente e in segreto.`
  - New: `Termine neutro-formale per una rete o organizzazione politica che opera illegalmente e in segreto; resistenza clandestina è adatto quando l'opposizione a un regime è esplicita.`
- `trap`
  - Old: `Nel senso politico underground non è sotterraneo; se indica specificamente le persone o l'organizzazione, servono movimento clandestino o rete clandestina.`
  - New: `Nel senso politico underground non è sotterraneo; clandestinità indica la condizione o il metodo operativo, non il movimento designato dal sostantivo inglese con articolo determinativo.`
- `example_tl`
  - Old: `La clandestinità impose agli oppositori identità false, comunicazioni cifrate e riunioni frammentate, riducendo la capacità del regime di smantellare intere reti.`
  - New: `Il movimento clandestino coordinò l'uso di identità false, comunicazioni cifrate e cellule separate, riducendo la capacità del regime di smantellare l'intera rete.`
- `example_en`
  - Old: `Operating underground forced opponents to use false identities, coded communications, and fragmented meetings, reducing the regime's ability to dismantle entire networks.`
  - New: `The underground movement coordinated the use of false identities, coded communications, and separate cells, reducing the regime's ability to dismantle the entire network.`
- `cloze`
  - Old: `{{c1::La clandestinità}} impose agli oppositori identità false, comunicazioni cifrate e riunioni frammentate, riducendo la capacità del regime di smantellare intere reti.`
  - New: `{{c1::Il movimento clandestino}} coordinò l'uso di identità false, comunicazioni cifrate e cellule separate, riducendo la capacità del regime di smantellare l'intera rete.`
- `note`
  - Old: `The English prompt is polysemous; old_back selects the state of operating underground, and the trap records the different rendering required for an underground organization.`
  - New: `Materially corrects the semantic shift in old_back: the definite English noun denotes a covert political network or movement, whereas clandestinità names the condition or practice of operating underground.`
- Triage `reason`
  - Old: `Political underground requires nonliteral clandestinità and different Italian phrases when the source denotes a network or movement.`
  - New: `The definite English noun denotes a covert political network or movement; Italian requires movimento clandestino rather than physical sotterraneo or abstract clandestinità.`

### `it_cold_war_vocab_b04`, item 158

Reason: Replace an unattributed causal judgment about perestroika with explicitly opposed supporter and critic positions.

- `example_tl`
  - Old: `La perestrojka tentò di riformare economia e istituzioni sovietiche, ma innescò dinamiche politiche che la dirigenza non riuscì più a controllare.`
  - New: `I sostenitori della perestrojka volevano riformare l'economia e le istituzioni sovietiche, mentre i critici temevano dinamiche politiche che la dirigenza non avrebbe saputo controllare.`
- `example_en`
  - Old: `Perestroika attempted to reform the Soviet economy and institutions but triggered political dynamics that the leadership could no longer control.`
  - New: `Supporters of perestroika wanted to reform the Soviet economy and institutions, while critics feared political dynamics that the leadership would be unable to control.`
- `cloze`
  - Old: `{{c1::La perestrojka}} tentò di riformare economia e istituzioni sovietiche, ma innescò dinamiche politiche che la dirigenza non riuscì più a controllare.`
  - New: `I sostenitori {{c1::della perestrojka}} volevano riformare l'economia e le istituzioni sovietiche, mentre i critici temevano dinamiche politiche che la dirigenza non avrebbe saputo controllare.`
- `note`
  - Old: `Old_back already uses the standard Italian transliteration. Self-review omitted ristrutturazione from alts because it is explanatory and changed liberò to the more idiomatic innescò.`
  - New: `Old_back already uses the standard Italian transliteration. Self-review omitted ristrutturazione from alts because it is explanatory. Audit review replaced an unattributed causal assessment in the example.`

### `pt_cold_war_vocab_b02`, item 046

Reason: Attribute the politically loaded historical assessment of U.S. interventionism.

- `example_tl`
  - Old: `O intervencionismo de Washington enfraqueceu governos eleitos e alimentou um antiamericanismo que sobreviveu muito depois do fim da Guerra Fria.`
  - New: `Diversos historiadores associaram o intervencionismo de Washington ao enfraquecimento de governos eleitos e a um antiamericanismo que perdurou após a Guerra Fria.`
- `example_en`
  - Old: `Washington's interventionism weakened elected governments and fueled an anti-Americanism that survived long after the end of the Cold War.`
  - New: `Various historians linked Washington's interventionism to the weakening of elected governments and to anti-Americanism that endured after the Cold War.`
- `cloze`
  - Old: `{{c1::O intervencionismo}} de Washington enfraqueceu governos eleitos e alimentou um antiamericanismo que sobreviveu muito depois do fim da Guerra Fria.`
  - New: `Diversos historiadores associaram {{c1::o intervencionismo}} de Washington ao enfraquecimento de governos eleitos e a um antiamericanismo que perdurou após a Guerra Fria.`
- `note`
  - Old: `The example fixes the foreign-policy sense; old_back supplies the right lexeme but omits the pedagogically useful article.`
  - New: `The example fixes the foreign-policy sense; old_back supplies the right lexeme but omits the pedagogically useful article. Audit review attributed the historical assessment.`

### `pt_cold_war_vocab_b02`, item 061

Reason: Correct a false-friend semantic shift: militância normally denotes organized activism or affiliation, while the English prompt asks for combativeness.

- `tl`
  - Old: `a militância política`
  - New: `a combatividade`
- `alts`
  - Old: `[]`
  - New: `["a postura combativa"]`
- `register`
  - Old: `Termo neutro-formal para a participação ativa e continuada em partido ou movimento; por si só, não implica violência nem extremismo.`
  - New: `Termo neutro-formal para uma disposição firme e confrontadora na ação política, sindical ou social; pode ser retórica e não implica necessariamente violência.`
- `trap`
  - Old: `O inglês militancy costuma salientar combatividade; em português, militância geralmente indica participação ou filiação ativa, e o falso paralelo pode alterar o sentido.`
  - New: `Em português, militância geralmente indica participação ou filiação ativa e não equivale ao inglês militancy quando este salienta uma postura combativa.`
- `example_tl`
  - Old: `A militância política sustentou redes clandestinas de imprensa e solidariedade, embora o exílio e a repressão reduzissem a capacidade organizativa dos partidos.`
  - New: `A combatividade do sindicato aumentou após o fracasso das negociações, embora seus dirigentes continuassem a rejeitar explicitamente a violência política.`
- `example_en`
  - Old: `Political activism sustained clandestine press and solidarity networks, although exile and repression reduced the parties' organizational capacity.`
  - New: `The union's militancy increased after negotiations failed, although its leaders continued explicitly to reject political violence.`
- `cloze`
  - Old: `{{c1::A militância política}} sustentou redes clandestinas de imprensa e solidariedade, embora o exílio e a repressão reduzissem a capacidade organizativa dos partidos.`
  - New: `{{c1::A combatividade}} do sindicato aumentou após o fracasso das negociações, embora seus dirigentes continuassem a rejeitar explicitamente a violência política.`
- `note`
  - Old: `Materially sharpens old_back by fixing the political-participation sense. If English militancy instead means aggressive conduct, combatividade would be preferable; the source cluster supports the Romance political sense.`
  - New: `Materially corrects the false-friend legacy rendering: Portuguese militância normally means membership or organized activism, whereas the English prompt foregrounds a combative posture.`

### `pt_cold_war_vocab_b03`, item 084

Reason: Attribute the contested assessment of developmentalism to supporters and critics.

- `example_tl`
  - Old: `O desenvolvimentismo prometia acelerar a industrialização por meio do investimento estatal, mas frequentemente subordinava direitos sociais às metas de crescimento.`
  - New: `Os defensores do desenvolvimentismo prometiam acelerar a industrialização por meio do investimento estatal, enquanto os críticos denunciavam a subordinação de direitos sociais às metas de crescimento.`
- `example_en`
  - Old: `Developmentalism promised to accelerate industrialization through state investment, but it often subordinated social rights to growth targets.`
  - New: `Supporters of developmentalism promised to accelerate industrialization through state investment, while critics denounced the subordination of social rights to growth targets.`
- `cloze`
  - Old: `{{c1::O desenvolvimentismo}} prometia acelerar a industrialização por meio do investimento estatal, mas frequentemente subordinava direitos sociais às metas de crescimento.`
  - New: `Os defensores {{c1::do desenvolvimentismo}} prometiam acelerar a industrialização por meio do investimento estatal, enquanto os críticos denunciavam a subordinação de direitos sociais às metas de crescimento.`
- `note`
  - Old: `Old_back identifies the right specialist lexeme but adds unnecessary capitalization.`
  - New: `Old_back identifies the right specialist lexeme but adds unnecessary capitalization. Audit review attributed the contested assessment in the example.`

### `pt_cold_war_vocab_b04`, item 139

Reason: Attribute the critical assessment of domino-theory reasoning to historians critical of the doctrine.

- `example_tl`
  - Old: `A teoria do dominó levou governos norte-americanos a tratar conflitos locais como testes decisivos, ignorando frequentemente suas causas sociais e políticas específicas.`
  - New: `Segundo historiadores críticos da doutrina, a teoria do dominó levou governos norte-americanos a tratar conflitos locais como testes decisivos e a ignorar suas causas específicas.`
- `example_en`
  - Old: `Domino theory led U.S. governments to treat local conflicts as decisive tests, frequently ignoring their specific social and political causes.`
  - New: `According to historians critical of the doctrine, domino theory led U.S. governments to treat local conflicts as decisive tests and to ignore their specific causes.`
- `cloze`
  - Old: `{{c1::A teoria do dominó}} levou governos norte-americanos a tratar conflitos locais como testes decisivos, ignorando frequentemente suas causas sociais e políticas específicas.`
  - New: `Segundo historiadores críticos da doutrina, {{c1::a teoria do dominó}} levou governos norte-americanos a tratar conflitos locais como testes decisivos e a ignorar suas causas específicas.`
- `note`
  - Old: `Old_back gives the established term; capitalization is normalized for a common-noun doctrine name.`
  - New: `Old_back gives the established term; capitalization is normalized for a common-noun doctrine name. Audit review attributed the critical historical assessment.`

### `pt_cold_war_vocab_b04`, item 144

Reason: Remove the false implication that the Kremlin itself used the critical satellite-state label for East Germany; attribute it to Western historiography.

- `example_tl`
  - Old: `O Kremlin tratava a Alemanha Oriental como Estado-satélite, formalmente soberano, mas submetido a fortes constrangimentos militares, econômicos e diplomáticos.`
  - New: `Na historiografia ocidental, a Alemanha Oriental foi frequentemente descrita como Estado-satélite, formalmente soberana, mas sujeita a fortes constrangimentos militares, econômicos e diplomáticos impostos por Moscou.`
- `example_en`
  - Old: `The Kremlin treated East Germany as a satellite state, formally sovereign but subject to strong military, economic, and diplomatic constraints.`
  - New: `In Western historiography, East Germany was often described as a satellite state, formally sovereign but subject to strong military, economic, and diplomatic constraints imposed by Moscow.`
- `cloze`
  - Old: `O Kremlin tratava a Alemanha Oriental como {{c1::Estado-satélite}}, formalmente soberano, mas submetido a fortes constrangimentos militares, econômicos e diplomáticos.`
  - New: `Na historiografia ocidental, a Alemanha Oriental foi frequentemente descrita como {{c1::Estado-satélite}}, formalmente soberana, mas sujeita a fortes constrangimentos militares, econômicos e diplomáticos impostos por Moscou.`
- `note`
  - Old: `Adds the standard hyphen and the pedagogically useful article to old_back. Self-review capitalized Estado in the sovereign-polity sense used by the example.`
  - New: `Adds the standard hyphen and the pedagogically useful article to old_back. Self-review capitalized Estado in the sovereign-polity sense used by the example; audit review attributed the critical label.`

### `pt_cold_war_vocab_b04`, item 158

Reason: Replace an unattributed causal judgment about perestroika with explicitly opposed supporter and critic positions.

- `example_tl`
  - Old: `A perestroika pretendia reformar a economia soviética sem abandonar o socialismo, mas suas contradições aceleraram a perda de autoridade do governo central.`
  - New: `Os defensores da perestroika pretendiam reformar a economia soviética sem abandonar o socialismo, enquanto os críticos temiam que as contradições das reformas enfraquecessem o governo central.`
- `example_en`
  - Old: `Perestroika sought to reform the Soviet economy without abandoning socialism, but its contradictions accelerated the central government's loss of authority.`
  - New: `Supporters of perestroika intended to reform the Soviet economy without abandoning socialism, while critics feared that the reforms' contradictions would weaken the central government.`
- `cloze`
  - Old: `{{c1::A perestroika}} pretendia reformar a economia soviética sem abandonar o socialismo, mas suas contradições aceleraram a perda de autoridade do governo central.`
  - New: `Os defensores {{c1::da perestroika}} pretendiam reformar a economia soviética sem abandonar o socialismo, enquanto os críticos temiam que as contradições das reformas enfraquecessem o governo central.`
- `note`
  - Old: `The parenthetical restructuring is explanatory rather than part of the headword. Self-review normalized old_back's capitalization, preserved the standard Brazilian spelling, and clarified the institutional referent in the example.`
  - New: `The parenthetical restructuring is explanatory rather than part of the headword. Self-review normalized old_back's capitalization and preserved the standard Brazilian spelling. Audit review replaced an unattributed causal assessment in the example.`

### `pt_cold_war_vocab_b06`, item 202

Reason: Attribute the specific covert-intervention claim to declassified documents.

- `example_tl`
  - Old: `O serviço de inteligência tentou subverter a ordem constitucional, financiando grupos clandestinos e manipulando divisões internas para desestabilizar o governo eleito.`
  - New: `Documentos desclassificados indicaram que um serviço de inteligência tentou subverter a ordem constitucional, financiando grupos clandestinos e explorando divisões internas para desestabilizar o governo eleito.`
- `example_en`
  - Old: `The intelligence service tried to subvert the constitutional order by financing clandestine groups and manipulating internal divisions to destabilize the elected government.`
  - New: `Declassified documents indicated that an intelligence service tried to subvert the constitutional order by financing clandestine groups and exploiting internal divisions to destabilize the elected government.`
- `cloze`
  - Old: `O serviço de inteligência tentou {{c1::subverter}} a ordem constitucional, financiando grupos clandestinos e manipulando divisões internas para desestabilizar o governo eleito.`
  - New: `Documentos desclassificados indicaram que um serviço de inteligência tentou {{c1::subverter}} a ordem constitucional, financiando grupos clandestinos e explorando divisões internas para desestabilizar o governo eleito.`
- `note`
  - Old: `Old_back fornece o infinitivo correto. Autorrevisão: mantive o sentido de alteração direta da ordem estabelecida e excluí minar das alternativas, pois esse verbo expressa erosão gradual, já ensinada em outro tópico.`
  - New: `Old_back fornece o infinitivo correto. Autorrevisão: mantive o sentido de alteração direta da ordem estabelecida e excluí minar das alternativas, pois esse verbo expressa erosão gradual, já ensinada em outro tópico. A auditoria atribuiu a afirmação histórica a documentos desclassificados.`

## Defect taxonomy summary

Counts are findings by defect class and may overlap on the same row.

| Class | Result | Findings and disposition |
|---|---|---|
| 1. Language quality / naturalness | EDITED | Thirteen rows: four Romance false-friend repairs for Militancy; German 140 morphology; Italian 148 noun sense; French 210 referent precision; and six rows with intrusive lexical repetition. |
| 2. Schema and field semantics | EDITED | Five rows had a production-headword/English-prompt semantic mismatch: Militancy in Spanish, French, Italian, and Portuguese, plus Italian Underground. All other retained objects satisfy the V1 field contract. |
| 3. Triage judgment / duplicate policy | EDITED | Italian 148 retained the correct keep verdict but required a corrected rationale after its headword repair. The other 1,109 decisions and all twelve cross-topic ownership groups are correct. |
| 4. Interference traps | EDITED | Six traps were corrected: the four Romance Militancy false friends, German 140 morphology, and Italian 148 condition-versus-movement scope. The other 578 traps identify a real lexical, grammatical, collocational, or register risk. |
| 5. Cloze integrity | PASS | No cloze-specific defect. Thirty-four clozes were regenerated only to remain exact reductions after examples or headwords changed; all 584 pass. |
| 6a. Circular definitions | PASS | None. V1 has no separate definition field; register and trap prose do not define a term with itself. |
| 6b. Cross-item boilerplate | PASS | No repeated target example or multi-card proposition/frame requiring repair. Recurrent categorical register openers are metadata, not repeated drilled content. |
| 6c. English/target term-definition redundancy | N/A / PASS | The definition-pair test is not structurally applicable to V1. Required English examples are faithful translations, not duplicate definitions. |
| 6d. Within-sentence repetition | EDITED | Six rows: German 187; Spanish 131 and 164; French 111 and 142; Italian 105. |
| Topic-specific political neutrality | EDITED | Twenty-two examples were reframed with supporters/critics, historiographic attribution, narrower scope, or documentary attribution. No loaded claim remains in unmarked narrator voice. |

No uncorrected blocker remains. No source item is silently reinterpreted, no retained card leaks its cloze answer, and no chunk requires rejection or rewrite.

**Final counts — chunks passed / edited / failed: 30 / 21 / 0.**

