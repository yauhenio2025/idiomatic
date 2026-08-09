# Exercises 2.0 hostile audit: BIG_TECH_PHRASES

Audited 2026-08-09 against `docs/commissions/CODEX_X2_WAVE_AUDIT.md`, the
Wave 6 shadowing addendum, and `batches/manifests/wave6.json`. The 15 landed
chunks contain the 90 canonical production frames in each of German,
Spanish, French, Italian, and Portuguese. These are shadowing frames, not
translation-note rows; the audit therefore treats `tl` as a complete spoken
frame and `focus_tl`/`focus_en` as the reusable production cue.

## Source and triage checks

- Every input `id` and `en` remained unchanged and source-ordered.
- All 450 rows were triaged `keep`; there were no drops and no manifest
  `expected_duplicate_drop_ids` for BIG_TECH_PHRASES.
- The committed exact-English duplicate report contains no
  BIG_TECH_PHRASES occurrence. No cross-topic exception was required.
- Every kept note retains the shadowing schema: `category`, complete `tl`,
  `focus_tl`, `focus_en`, `register`, `trap`, and `note`.
- Every final `focus_tl` occurs verbatim inside `tl`; no ellipsis was added and
  no cloze field was introduced.

## Per-chunk verdicts

| Chunk | Rows | Triage | Verdict | Edited rows | Changed fields |
|---|---:|---|---|---:|---:|
| `de_big_tech_phrases_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 36 | 50 |
| `de_big_tech_phrases_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 34 | 51 |
| `de_big_tech_phrases_b03` | 10 | 10 keep / 0 drop | PASS-WITH-EDITS | 5 | 8 |
| `es_big_tech_phrases_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 4 | 8 |
| `es_big_tech_phrases_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 8 | 13 |
| `es_big_tech_phrases_b03` | 10 | 10 keep / 0 drop | PASS-WITH-EDITS | 2 | 3 |
| `fr_big_tech_phrases_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 4 | 7 |
| `fr_big_tech_phrases_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 9 | 14 |
| `fr_big_tech_phrases_b03` | 10 | 10 keep / 0 drop | PASS-WITH-EDITS | 1 | 2 |
| `it_big_tech_phrases_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 1 | 2 |
| `it_big_tech_phrases_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 5 | 9 |
| `it_big_tech_phrases_b03` | 10 | 10 keep / 0 drop | PASS-WITH-EDITS | 1 | 1 |
| `pt_big_tech_phrases_b01` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 1 | 2 |
| `pt_big_tech_phrases_b02` | 40 | 40 keep / 0 drop | PASS-WITH-EDITS | 17 | 25 |
| `pt_big_tech_phrases_b03` | 10 | 10 keep / 0 drop | PASS-WITH-EDITS | 5 | 10 |

## Every applied edit

### Exact target-frame edits

The following are exact `tl` old → new edits. The edited IDs are the numeric
suffix shown in each language block; the same canonical ID is present in that
language's chunk.

**DE**

- `001` `Angesichts der jüngsten Cybersecurity-Verstöße überdenken viele Startups im Silicon Valley ihre Datenschutzstrategien.` → `Angesichts der jüngsten Cyberangriffe überdenken viele Start-ups im Silicon Valley ihre Datenschutzstrategien.`
- `002` `Im Kontext der globalen digitalen Transformation beeilen sich traditionelle Unternehmen, Cloud-basierte Lösungen zu übernehmen.` → `Im Kontext der globalen digitalen Transformation beeilen sich traditionelle Unternehmen, cloudbasierte Lösungen einzuführen.`
- `008` `Bei der KI-Entwicklung hinkt Europa dem Silicon Valley hinterher, was zu Diskussionen über eine höhere Finanzierung führt.` → `Bei der KI-Entwicklung hinkt Europa dem Silicon Valley hinterher, was die Debatte über zusätzliche Finanzmittel anheizt.`
- `010` `In Anbetracht des Aufstiegs des Quantencomputers lenken mehrere Unternehmen ihre Investitionen um.` → `In Anbetracht des Aufkommens von Quantencomputing lenken mehrere Unternehmen ihre Investitionen um.`
- `011` `Aufgrund der jüngsten Fortschritte in der AR-Technologie sind viele VCs optimistisch, dass sich diese Technologie im Mainstream durchsetzen wird.` → `Aufgrund der jüngsten Fortschritte in der AR-Technologie sind viele Wagniskapitalgeber optimistisch, dass sich diese Technologie breit durchsetzen wird.`
- `012` `In Anbetracht der Tatsache, dass digitale Währungen das traditionelle Bankwesen stören, haben es die Regulierungsbehörden eilig, entsprechende Gesetze zu entwerfen.` → `Da digitale Währungen das traditionelle Bankwesen umwälzen, haben es die Regulierungsbehörden eilig, entsprechende Gesetze zu entwerfen.`
- `013` `In Anbetracht des enormen Potenzials des Internet der Dinge (IoT) erkunden Stadtplaner intelligentere Infrastrukturprojekte.` → `In Anbetracht des enormen Potenzials des Internets der Dinge (IoT) erkunden Stadtplaner intelligentere Infrastrukturprojekte.`
- `018` `Aufgrund ihrer großen Nutzerbasis üben einige Plattformen großen Einfluss auf den digitalen Anzeigenmarkt aus.` → `Aufgrund ihrer großen Nutzerbasis üben einige Plattformen großen Einfluss auf den digitalen Werbemarkt aus.`
- `019` `Aufgrund der rasanten Fortschritte in der Biotechnologie erlebt das Silicon Valley einen Anstieg der Startups im Bereich Gesundheitstechnologie.` → `Aufgrund der rasanten Fortschritte in der Biotechnologie erlebt das Silicon Valley eine Zunahme von Start-ups im Bereich der Gesundheitstechnologie.`
- `021` `Im Einklang mit den globalen Nachhaltigkeitszielen verstärken die Technologieunternehmen ihre grünen Initiativen.` → `Im Einklang mit den globalen Nachhaltigkeitszielen verstärken die Technologieunternehmen ihre Initiativen für ökologische Nachhaltigkeit.`
- `028` `Auf der Grundlage von prädiktiven Analysen personalisieren viele E-Retailer das Nutzererlebnis wie nie zuvor.` → `Auf Grundlage prädiktiver Analysen personalisieren viele Onlinehändler das Nutzererlebnis wie nie zuvor.`
- `029` `Im Zusammenhang mit dem Vorwurf der Steuerhinterziehung werden bestimmte Big Tech-Unternehmen verstärkt unter die Lupe genommen.` → `Im Zusammenhang mit Vorwürfen der Steuerhinterziehung werden bestimmte Big-Tech-Unternehmen verstärkt unter die Lupe genommen.`
- `030` `Im Interesse der Innovationsförderung werden die Regierungen aufgefordert, ihre Haltung zu digitalen Fusionen zu überdenken.` → `Im Interesse der Innovationsförderung werden die Regierungen aufgefordert, ihre Haltung zu Fusionen im Digitalbereich zu überdenken.`
- `032` `In Anbetracht der wachsenden technischen Kluft wurden die Mittel für Initiativen zur Überbrückung der Kluft erhöht.` → `Angesichts der wachsenden digitalen Kluft wurden die Mittel für Initiativen erhöht, die diese Kluft überbrücken sollen.`
- `033` `Inmitten von Bedenken hinsichtlich der Ethik des Deep Learning gewinnen Debatten über das maschinelle Bewusstsein an Zugkraft.` → `Inmitten von Bedenken hinsichtlich der Ethik des Deep Learning gewinnen Debatten über das maschinelle Bewusstsein an Fahrt.`
- `035` `Nach den Akquisitionen von Big Tech drängen die Kartellbehörden auf mehr Transparenz bei der Abwicklung von Geschäften.` → `In Anbetracht der Übernahmen durch Big-Tech-Unternehmen drängen die Kartellbehörden auf mehr Transparenz bei der Abwicklung von Geschäften.`
- `037` `Jenseits des traditionellen Computings werden Startups aus dem Bereich der Quantentechnologie zu den neuen Investitionslieblingen.` → `Jenseits der traditionellen Computertechnik werden Start-ups aus dem Bereich der Quantentechnologie zu den neuen Favoriten der Anleger.`
- `042` `Neben der Besorgnis über die KI-bedingte Arbeitslosigkeit gibt es eine wachsende Bewegung für Weiterbildungsinitiativen.` → `Angesichts der Sorge über die durch KI bedingte Arbeitslosigkeit wächst die Bewegung für Weiterbildungsinitiativen.`
- `043` `Auf der Suche nach der nächsten digitalen Grenze richtet das Silicon Valley seine Augen auf die Weltraumtechnologie.` → `Auf der Suche nach der nächsten digitalen Grenze nimmt das Silicon Valley die Weltraumtechnologie ins Visier.`
- `047` `Nach dem jüngsten Tech-Backlash verdoppeln die Unternehmen ihre Bemühungen in der Öffentlichkeitsarbeit.` → `Nach dem jüngsten Gegenwind für die Tech-Branche verdoppeln die Unternehmen ihre Anstrengungen in der Öffentlichkeitsarbeit.`
- `048` `Unter dem Gesichtspunkt der digitalen Nachhaltigkeit werden die Umweltkosten von Blockchain immer genauer unter die Lupe genommen.` → `Unter dem Gesichtspunkt der digitalen Nachhaltigkeit werden die Umweltkosten der Blockchain-Technologie immer genauer unter die Lupe genommen.`
- `051` `Jüngsten Trends zufolge steigt das Interesse an Edge Computing, um den IoT-Anforderungen gerecht zu werden.` → `Den jüngsten Trends zufolge steigt das Interesse an Edge Computing, um den Anforderungen des IoT gerecht zu werden.`
- `052` `Wenn es um digitale Gesundheitspässe geht, werden die Debatten über Datenschutz und Notwendigkeit immer hitziger.` → `Bei digitalen Gesundheitspässen werden die Debatten über Datenschutz und die Notwendigkeit solcher Pässe immer hitziger.`
- `054` `Aus den Erfahrungen vergangener Tech-Crashs ziehen Risikokapitalgeber ihre Lehren und verfolgen einen gemäßigteren Ansatz.` → `Auf Grundlage der Lehren aus vergangenen Tech-Crashs verfolgen Risikokapitalgeber einen gemäßigteren Ansatz.`
- `056` `Parallel zum Aufschwung des E-Commerce erlebt der stationäre Handel mit digitalen Integrationen eine Renaissance.` → `Parallel zum Aufschwung des E-Commerce erlebt der stationäre Handel mit digitaler Integration eine Renaissance.`
- `058` `Im Spektrum der digitalen Bildungslösungen machen VR-Klassenzimmer bemerkenswerte Fortschritte.` → `Im Bereich digitaler Bildungslösungen machen virtuelle Klassenzimmer bemerkenswerte Fortschritte.`
- `060` `Apps, die den Zeitgeist des digitalen Wohlbefindens aufgreifen und sich auf die psychische Gesundheit konzentrieren, verzeichnen ein exponentielles Nutzerwachstum.` → `Den Zeitgeist des digitalen Wohlbefindens aufgreifend, verzeichnen auf psychische Gesundheit ausgerichtete Apps ein exponentielles Nutzerwachstum.`
- `064` `In dem Bestreben, die digitale Vorherrschaft zu sichern, wetteifern die Länder um die Vorherrschaft im KI-Wettrüsten.` → `In dem Bestreben, die digitale Vorherrschaft zu sichern, wetteifern die Länder im Wettrüsten um KI.`
- `065` `Im Zentrum der geopolitischen Spannungen rückt die Kontrolle über die Dateninfrastruktur und Unterseekabel in den Mittelpunkt.` → `Im Zentrum der geopolitischen Spannungen wird die Kontrolle über Dateninfrastrukturen und Unterseekabel zu einem Brennpunkt.`
- `067` `An den vordersten Fronten des Kampfes für digitale Freiheit fordern Aktivisten Regierungen wegen Internetabschaltungen heraus.` → `An vorderster Front des Kampfes für digitale Freiheit fordern Aktivisten Regierungen wegen Internetabschaltungen heraus.`
- `068` `In den trüben Gewässern der Cyberdiplomatie kämpfen die Nationen mit der Festlegung von Normen in einer grenzenlosen digitalen Welt.` → `In den trüben Gewässern der Cyberdiplomatie ringen die Nationen darum, in einer grenzenlosen digitalen Welt Normen zu etablieren.`
- `069` `Mit dem Aufkommen und Abklingen des digitalen Kolonialismus wehren sich Entwicklungsländer gegen die Datenextraktion durch Tech-Giganten.` → `Mit dem Auf und Ab des digitalen Kolonialismus wehren sich Entwicklungsländer gegen die Datenextraktion durch Tech-Giganten.`
- `079` `An der Schnittstelle zwischen Geopolitik und Technologie sind Seltene Erden zum neuen Öl geworden und diktieren die diplomatischen Beziehungen.` → `An der Schnittstelle zwischen Geopolitik und Technologie sind seltene Erden zum neuen Öl geworden und bestimmen die diplomatischen Beziehungen.`
- `080` `Im Kampf gegen die globale Cyberkriminalität finden die Nationen bei der Zusammenarbeit der Strafverfolgungsbehörden eine gemeinsame Basis.` → `Im Kampf gegen die globale Cyberkriminalität finden die Nationen in der Zusammenarbeit der Strafverfolgungsbehörden eine gemeinsame Basis.`
- `081` `Mit der Verschiebung des Sandes in der Technologielandschaft entwickeln sich Nationen, die zuvor an der Peripherie lagen, zu digitalen Zentren.` → `Angesichts der Umbrüche in der Technologielandschaft entwickeln sich Nationen, die zuvor an der Peripherie lagen, zu digitalen Zentren.`
- `087` `Im Schmelztiegel der globalen digitalen Zusammenarbeit entsteht eine neue Art von multilateralen Technologieabkommen.` → `Im Schmelztiegel der globalen digitalen Zusammenarbeit entsteht eine neue Art multilateraler Technologieabkommen.`
- `088` `Länder in geopolitischen Brennpunkten surfen auf den Wellen der digitalen Revolution und nutzen die Technologie für Soft Power.` → `Auf den Wellen der digitalen Revolution nutzen Länder in geopolitischen Brennpunkten die Technologie als Instrument der Soft Power.`

**ES**

- `009` `Con respecto a la economía colaborativa, los reguladores están presionando para mejorar la protección de los trabajadores.` → `Con respecto a la economía de plataformas, los reguladores presionan para mejorar la protección de los trabajadores.`
- `014` `Teniendo en cuenta los retos que plantean las falsificaciones, las plataformas de redes sociales están introduciendo controles de contenido más estrictos.` → `Teniendo en cuenta los retos que plantean los deepfakes, las plataformas de redes sociales están introduciendo controles de contenido más estrictos.`
- `031` `Junto con la nueva legislación, las empresas tecnológicas buscan orientación sobre las medidas de cumplimiento.` → `Con la entrada en vigor de la nueva legislación, las empresas tecnológicas buscan orientación sobre las medidas de cumplimiento.`
- `032` `Tras reflexionar sobre la creciente brecha tecnológica, las iniciativas para salvarla han recibido más financiación.` → `Ante el aumento de la brecha tecnológica, las iniciativas para cerrarla han recibido más financiación.`
- `046` `En yuxtaposición con el crecimiento del metaverso, aumentan las preguntas sobre la identidad digital y la privacidad.` → `A medida que crece el metaverso, aumentan las preguntas sobre la identidad digital y la privacidad.`
- `051` `Según las últimas tendencias, hay un creciente interés en la computación de borde para satisfacer las demandas de IoT.` → `Según las últimas tendencias, crece el interés por la computación en el borde para satisfacer las demandas del IoT.`
- `052` `En lo que respecta a los pasaportes sanitarios digitales, los debates sobre la privacidad y la necesidad son cada vez más acalorados.` → `En lo que respecta a los pasaportes sanitarios digitales, los debates sobre la privacidad y la necesidad de estos pasaportes son cada vez más acalorados.`
- `059` `La agricultura sostenible está experimentando una revolución digital gracias a la afluencia de capital riesgo a la tecnología agrícola.` → `Gracias a la afluencia de capital riesgo a la tecnología agrícola, la agricultura sostenible está experimentando una revolución digital.`
- `060` `Aprovechando el espíritu del bienestar digital, las aplicaciones centradas en la salud mental están experimentando un crecimiento exponencial de usuarios.` → `Aprovechando el auge del bienestar digital, las aplicaciones centradas en la salud mental están experimentando un crecimiento exponencial de usuarios.`
- `063` `En la cúspide de una Guerra Fría digital, el mundo observa cómo las superpotencias establecen alianzas tecnológicas estratégicas.` → `Al borde de una nueva guerra fría digital, el mundo observa cómo las superpotencias establecen alianzas tecnológicas estratégicas.`
- `067` `En primera línea de la lucha por la libertad digital, los activistas desafían a los gobiernos por el cierre de Internet.` → `En primera línea de la lucha por la libertad digital, los activistas desafían a los gobiernos por los cortes de internet.`
- `080` `Para hacer frente a la gigantesca ciberdelincuencia mundial, los países están encontrando puntos en común en la colaboración policial.` → `Para combatir la lacra de la ciberdelincuencia mundial, los países están encontrando puntos en común en la cooperación policial.`
- `086` `Las instituciones democráticas se enfrentan a la propaganda de la inteligencia artificial y buscan estrategias de resistencia.` → `Ante la propaganda impulsada por la inteligencia artificial, las instituciones democráticas buscan estrategias de resistencia.`
- `088` `Aprovechando las olas de la revolución digital, los países situados en zonas geopolíticas conflictivas utilizan la tecnología como instrumento de poder.` → `Aprovechando las olas de la revolución digital, los países de zonas geopolíticas conflictivas utilizan la tecnología para proyectar poder blando.`

**FR**

- `009` `En ce qui concerne l'économie parallèle, les régulateurs font pression pour une meilleure protection des travailleurs.` → `En ce qui concerne l'économie à la tâche, les régulateurs font pression pour une meilleure protection des travailleurs.`
- `012` `Étant donné que les monnaies numériques perturbent le secteur bancaire traditionnel, les régulateurs sont pressés de rédiger une législation pertinente.` → `Étant donné que les monnaies numériques perturbent le secteur bancaire traditionnel, les régulateurs s'empressent de rédiger une législation pertinente.`
- `029` `Dans le cadre d'allégations d'évasion fiscale, certaines grandes entreprises technologiques font l'objet d'un examen plus approfondi.` → `Face aux accusations d'évasion fiscale, certaines grandes entreprises technologiques font l'objet d'un examen plus approfondi.`
- `039` `En adhérant aux dernières propositions en matière de fiscalité numérique, les multinationales de la technologie repensent leurs stratégies mondiales.` → `À la suite des dernières propositions en matière de fiscalité numérique, les multinationales de la technologie repensent leurs stratégies mondiales.`
- `045` `La révélation de nouvelles violations de données a ravivé les appels en faveur d'une déclaration des droits numériques.` → `À la suite de la révélation de nouvelles violations de données, les appels en faveur d'une déclaration des droits numériques se sont ravivés.`
- `050` `Au mépris des attentes du marché, certaines entreprises historiques font un retour impressionnant dans le domaine du numérique.` → `Contrairement aux attentes du marché, certaines entreprises historiques font un retour impressionnant dans le domaine du numérique.`
- `051` `D'après les tendances récentes, l'informatique de pointe suscite un intérêt croissant pour répondre aux exigences de l'IdO.` → `D'après les tendances récentes, l'informatique en périphérie suscite un intérêt croissant pour répondre aux exigences de l'IdO.`
- `052` `En ce qui concerne les passeports de santé numériques, les débats sur la confidentialité et la nécessité s'intensifient.` → `En ce qui concerne les passeports de santé numériques, les débats sur la confidentialité des données et la nécessité de ces passeports s'intensifient.`
- `056` `Parallèlement à l'essor du commerce électronique, on assiste à une renaissance des magasins de briques et de mortier dotés d'intégrations numériques.` → `Parallèlement à l'essor du commerce électronique, on assiste à une renaissance des commerces physiques dotés d'intégrations numériques.`
- `060` `S'inscrivant dans l'air du temps du bien-être numérique, les applications axées sur la santé mentale connaissent une croissance exponentielle du nombre d'utilisateurs.` → `Profitant de l'engouement pour le bien-être numérique, les applications axées sur la santé mentale connaissent une croissance exponentielle du nombre d'utilisateurs.`
- `066` `Sur le théâtre du cyber-espionnage mondial, les entreprises sont souvent prises entre les feux croisés des États.` → `Sur le théâtre du cyber-espionnage mondial, les entreprises sont souvent prises entre les feux croisés d'États.`
- `068` `Dans les eaux troubles de la cyber diplomatie, les nations s'efforcent d'établir des normes dans un monde numérique sans frontières.` → `Dans les eaux troubles de la cyberdiplomatie, les nations s'efforcent d'établir des normes dans un monde numérique sans frontières.`
- `077` `Au bord du précipice d'un nouvel ordre numérique, les pays font pression pour façonner l'architecture du futur internet.` → `À l'aube d'un nouvel ordre numérique, les pays font pression pour façonner l'architecture du futur internet.`
- `081` `Alors que les sables se déplacent dans le paysage technologique, des pays auparavant à la périphérie émergent en tant que centres numériques.` → `Dans un paysage technologique en pleine évolution, des pays auparavant à la périphérie émergent comme des centres numériques.`

**IT**

- `012` `Poiché le valute digitali stanno rivoluzionando il settore bancario tradizionale, le autorità di regolamentazione si stanno affrettando a elaborare norme specifiche in materia.` → `Poiché le valute digitali stanno trasformando il settore bancario tradizionale, le autorità di regolamentazione si affrettano a elaborare norme adeguate.`
- `046` `Parallelamente alla crescita del metaverso, aumentano gli interrogativi sull'identità digitale e sulla riservatezza.` → `Mentre cresce il metaverso, aumentano gli interrogativi sull'identità digitale e sulla riservatezza.`
- `051` `Sulla base delle tendenze recenti, cresce vertiginosamente l'interesse per l'edge computing, volto a soddisfare le esigenze dell'Internet delle cose.` → `Sulla base delle tendenze recenti, cresce l'interesse per l'edge computing, volto a soddisfare le esigenze dell'Internet delle cose.`
- `060` `Intercettando lo spirito del tempo legato al benessere digitale, le app incentrate sulla salute mentale stanno registrando una crescita esponenziale degli utenti.` → `Sfruttando l'entusiasmo per il benessere digitale, le app incentrate sulla salute mentale stanno registrando una crescita esponenziale degli utenti.`
- `063` `Alle soglie di una Guerra fredda digitale, il mondo osserva le superpotenze stringere alleanze tecnologiche strategiche.` → `Alle soglie di una nuova guerra fredda digitale, il mondo osserva le superpotenze stringere alleanze tecnologiche strategiche.`
- `080` `Nell'affrontare il colosso della criminalità informatica globale, le nazioni stanno trovando un terreno comune nella cooperazione tra le forze dell'ordine.` → `Di fronte al colosso della criminalità informatica globale, le nazioni stanno trovando un terreno comune nella cooperazione tra le forze dell'ordine.`
- `090` `Sull'incudine dei nuovi accordi informatici, gli Stati stanno forgiando percorsi per garantire la prosperità reciproca nell'era digitale.` → `Sull'incudine dei nuovi accordi informatici, gli Stati stanno tracciando percorsi per garantire la prosperità reciproca nell'era digitale.`

**PT**

- `004` `Em face da concorrência cada vez maior de empresas de mercados emergentes, as gigantes ocidentais da tecnologia estão acelerando suas iniciativas de pesquisa e desenvolvimento.` → `Diante da concorrência crescente dos mercados emergentes, as gigantes ocidentais da tecnologia estão acelerando suas iniciativas de pesquisa e desenvolvimento.`
- `042` `Além das preocupações com o desemprego causado pela IA, há um movimento crescente para iniciativas de aprimoramento de habilidades.` → `Além das preocupações com o desemprego causado pela IA, há um movimento crescente em favor de iniciativas de qualificação profissional.`
- `043` `Em busca da próxima fronteira digital, o Vale do Silício está voltando seus olhos para a tecnologia espacial.` → `Em busca da próxima fronteira digital, o Vale do Silício volta-se para a tecnologia espacial.`
- `045` `Com a revelação de novas violações de dados, os pedidos de uma declaração de direitos digitais foram reacendidos.` → `Após a revelação de novas violações de dados, voltaram a crescer os apelos por uma declaração de direitos digitais.`
- `046` `Em justaposição ao crescimento do metaverso, as questões sobre identidade digital e privacidade estão aumentando.` → `À medida que cresce o metaverso, aumentam as questões sobre identidade digital e privacidade.`
- `047` `Após a recente reação negativa da tecnologia, as empresas estão dobrando os esforços de relações públicas.` → `Após a recente reação negativa contra o setor de tecnologia, as empresas estão intensificando os esforços de relações públicas.`
- `049` `Em alinhamento com a demanda dos consumidores, os gigantes da tecnologia estão avançando no comércio de realidade aumentada.` → `Em sintonia com a demanda dos consumidores, os gigantes da tecnologia estão avançando no comércio baseado em realidade aumentada.`
- `050` `Desafiando as expectativas do mercado, algumas empresas legadas estão fazendo retornos digitais impressionantes.` → `Desafiando as expectativas do mercado, algumas empresas tradicionais estão obtendo resultados impressionantes no mercado digital.`
- `052` `Quando se trata de passaportes digitais de saúde, os debates sobre privacidade e necessidade estão esquentando.` → `Quando se trata de passaportes digitais de saúde, os debates sobre privacidade e a necessidade desses passaportes estão esquentando.`
- `055` `Dada a trajetória do consumo de mídia digital, o conteúdo orientado por AR está sendo apontado como a próxima grande novidade.` → `Dada a trajetória do consumo de mídia digital, o conteúdo baseado em realidade aumentada está sendo apontado como a próxima grande novidade.`
- `058` `No espectro das soluções de educação digital, as salas de aula de RV estão fazendo avanços notáveis.` → `No conjunto de soluções de educação digital, as salas de aula de RV estão fazendo avanços notáveis.`
- `060` `Aproveitando o zeitgeist do bem-estar digital, os aplicativos voltados para a saúde mental estão tendo um crescimento exponencial de usuários.` → `Aproveitando a tendência do bem-estar digital, os aplicativos voltados para a saúde mental estão tendo um crescimento exponencial de usuários.`
- `065` `No centro das tensões geopolíticas, o controle da infraestrutura de dados e dos cabos submarinos está se tornando um ponto focal.` → `No centro das tensões geopolíticas, o controle da infraestrutura de dados e dos cabos submarinos está se tornando um ponto central.`
- `067` `Na linha de frente da luta pela liberdade digital, os ativistas estão desafiando os governos em relação ao desligamento da Internet.` → `Na linha de frente da luta pela liberdade digital, os ativistas estão desafiando os governos em relação aos bloqueios da internet.`
- `068` `Percorrendo as águas turvas da diplomacia cibernética, as nações lutam para estabelecer normas em um reino digital sem fronteiras.` → `Percorrendo as águas turvas da diplomacia cibernética, as nações lutam para estabelecer normas em um mundo digital sem fronteiras.`
- `070` `Navegando na corda bamba da ética digital global, órgãos internacionais pretendem estabelecer padrões para o uso de IA em guerras.` → `Navegando na corda bamba da ética digital global, órgãos internacionais pretendem estabelecer padrões para o uso de IA em conflitos armados.`
- `077` `No precipício de uma nova ordem digital, os países estão fazendo lobby para moldar a arquitetura da futura Internet.` → `À beira de uma nova ordem digital, os países estão fazendo lobby para moldar a arquitetura da futura Internet.`
- `080` `Para enfrentar o gigante do crime cibernético global, as nações estão encontrando pontos em comum nas colaborações de aplicação da lei.` → `Para enfrentar a ameaça do crime cibernético global, as nações estão encontrando pontos em comum na cooperação entre forças de segurança.`
- `081` `Com as areias mudando no cenário tecnológico, nações que antes estavam na periferia estão emergindo como centros digitais.` → `Com as mudanças no cenário tecnológico, nações que antes estavam na periferia estão emergindo como centros digitais.`
- `082` `Lutando contra o espectro do armamento autônomo, as convenções internacionais estão sendo questionadas.` → `Diante do espectro do armamento autônomo, as convenções internacionais estão sendo questionadas.`
- `084` `Mergulhando no fundo do poço dos conflitos cibernéticos, as nações menores estão aproveitando estratégias assimétricas para nivelar o campo de jogo.` → `Mergulhando nas profundezas do conflito cibernético, as nações menores estão aproveitando estratégias assimétricas para nivelar o campo de jogo.`
- `086` `Encarando o barril da propaganda orientada por IA, as instituições democráticas estão buscando estratégias de resiliência.` → `Diante da propaganda impulsionada por IA, as instituições democráticas estão buscando estratégias de resiliência.`
- `089` `Presos na teia de aranha da vigilância cibernética, os agentes internacionais estão se adaptando a uma nova era de espionagem.` → `Presos na teia da vigilância cibernética, os agentes internacionais estão se adaptando a uma nova era de espionagem.`

### Focus-span edits

There were 110 `focus_tl` edits. The exact transformation was:

`author-selected prefix ending mid-clause (for example, “...überdenken viele Start-ups im”) → the complete reusable sentence-initial frame ending at the first clause boundary`.

This was applied only where the existing span was truncated or did not match
the final `tl`; spans already ending at a useful opening frame were retained.
The special complete-frame repairs were `de/012: Da digitale Währungen das
traditionelle Bankwesen umwälzen`, `de/017: Mit dem Ziel, den E-Commerce-Markt
zu dominieren`, and `de/064: In dem Bestreben, die digitale Vorherrschaft zu
sichern`. The five late native-editor rewrites above also updated their
verbatim focus spans. Every resulting span is parse-validated inside `tl`.

## Defect taxonomy and gate rerun

| Defect class | Finding and disposition |
|---|---|
| Language / register | 95 complete target frames contained a literal calque, a meaning shift, awkward collocation, or register mismatch; each was rewritten above. |
| Shadowing semantics | `tl` remains a complete, production-ready sentence; `focus_tl` is a reusable discourse span and `focus_en` remains a short function cue. |
| Triage / duplicates | 450/450 keeps, 0 drops, source order preserved, and no duplicate-report exception needed. |
| Interference traps | The language-specific opening-preposition/contraction warnings were retained because they are genuine frame risks; the intentionally empty PT row remains empty rather than inventing a trap. No wrong trap was found. |
| Cloze integrity | Not applicable by design: this is the separate shadowing model, not the vocab/cloze model. |

Rerun command:

```text
.venv/bin/python tools/x2_batch_gate.py <all 15 *_big_tech_phrases_b* chunks>
PASS 15/15 chunks; 450/450 kept notes parsed
```

chunks passed / edited / failed: **15 / 15 / 0**.
