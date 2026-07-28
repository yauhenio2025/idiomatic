# Data sources for auto-generated grammar exercises (ES/PT/FR/IT/DE)

> Commissioned research, 2026-07-28. Raw findings; synthesis lives in
> ../GRAMMAR_STRATEGY.md. License notes inline. Items marked "verify"
> were not fully confirmable from primary sources during this pass.

## 1. Conjugation / morphology databases

### Cross-language

- **Wiktionary via wiktextract / kaikki.org** — https://kaikki.org/dictionary/ (per-language JSONL downloads), extractor: https://github.com/tatuylonen/wiktextract. The single best cross-language source. Each entry includes a `forms` array (full inflection/conjugation tables with feature tags), `sounds` (IPA + audio URLs to Wikimedia Commons mp3/ogg), senses, translations, etymology. Updated roughly weekly from fresh dumps (English-edition data currently from the 2026-07-06 dump). Coverage (senses in the English edition): Spanish 871k, Italian 719k, German 629k, Portuguese 514k, French 458k — verb conjugation tables for all five languages are systematically present because en.wiktionary auto-generates them from templates. Wiktextract also parses non-English editions (`--edition`; kaikki hosts dewiktionary, frwiktionary, etc.). License: same as Wiktionary — **dual CC BY-SA + GFDL** (extractor code MIT). Redistribution in a product is fine with attribution + share-alike on the data. Citation requested: Ylonen, LREC 2022.
- **UniMorph 4.0** — https://unimorph.github.io/, per-language repos under github.com/unimorph. Plain TSV triples (lemma ⇥ inflected form ⇥ feature bundle, e.g. `V;IND;PST;3;SG`). Counts: Italian 509,574 forms / 10,009 lemmas; Spanish 382,955 / 5,460; French 367,732 / 7,535; Portuguese 303,996 / 4,001; German 179,339 / 15,060. **CC BY-SA 3.0** (Wiktionary-derived). Last major release 2022 (LREC paper: https://aclanthology.org/2022.lrec-1.89/); largely static since — fine for morphology, which doesn't go stale. Ideal for drill generation because the feature schema is uniform across all five languages.
- **verbecc** — https://github.com/bretttolbert/verbecc — Python conjugator for **French, Spanish, Italian, Portuguese, Catalan, Romanian**; French data derived from Verbiste XML (Pierre Sarrazin, GPL), other languages in Verbiste-format XML; ML template prediction for unseen verbs. Also available as a dockerized microservice. Open source (GPL-family because of Verbiste-derived data — verify exact license in repo before commercial embedding).
- **mlconjug3** — https://github.com/SekouDiaoNlp/mlconjug3 — fr/en/es/it/pt/ro, ML-based, built on Verbiste + scikit-learn; code MIT but training data lineage is Verbiste (GPL) — same caveat.
- **Universal Dependencies** treebanks: morphologically annotated real sentences for all 5 languages; licenses vary **per treebank** (many CC BY-SA, some CC BY-NC-SA) — useful for mining cloze sentences where the target form is already POS/feature-tagged. MultiBLiMP (see §6) shows this UD+UniMorph combination works at scale.
- **Verbix** (https://api.verbix.com/) — keyed API, proprietary terms of use; community-maintained data; not openly licensed. **Cooljugator** — no open license or bulk download; scraping-only, proprietary. Neither is recommended as a foundation.

### Spanish
- **Fred Jehle Spanish verb DB** — https://github.com/ghidinelli/fred-jehle-spanish-verbs — 600+ fully conjugated verbs, 11,000+ mood/tense combinations incl. English translations of each form; CSV + PostgreSQL dump. Freely available (Jehle granted free use; exact license wording in the repo README — verify, it predates SPDX hygiene). Hand-curated, so a good gold check-set against generated forms.
- kaikki.org Spanish + UniMorph spa give full paradigms incl. vosotros/vos forms.

### French
- **Lefff** (Sagot, Alexina project) — large-coverage morphological + syntactic lexicon (~half a million inflected forms, plus subcategorization frames — useful for preposition/valency exercises: which verbs take *à* vs *de*). **LGPL-LR** (free, commercial-compatible). Paper: https://aclanthology.org/L10-1487/; a practical wrapper: https://github.com/ClaudeCoulombe/FrenchLefffLemmatizer.
- **Verbiste** — GPL, ~7,000 French verbs as conjugation-template XML; upstream of verbecc/mlconjug.

### Italian
- **Morph-it!** (Zanchetta & Baroni, UniBo) — https://www.docs.sslmit.unibo.it/doku.php?id=resources:morph-it — lexicon of inflected forms with lemma + morphological features (~500k forms). License stated as **GPL** (historically dual-licensed with CC BY-SA — verify on the page). Standard Italian NLP resource.

### Portuguese
- **LABEL-LEX** (LabEL, IST Lisbon) — http://label.ist.utl.pt/pt/downloads_pt.php — formalized lexicon of simple and multiword units, ~1M+ inflected simple forms with morphological tags; versions ≥4.1 distributed under **GPL**. European Portuguese orientation.
- **Portal da Língua Portuguesa / MorDebe** — http://www.portaldalinguaportuguesa.org/ — official orthography-era morphological database with conjugator. No bulk download documented, and the portal has had availability problems in recent years (verify it's still up before depending on it).
- kaikki/UniMorph por cover the future subjunctive and personal infinitive paradigms — important since these are exactly the forms to drill.

### German
- **DWDSmor** — https://github.com/zentrum-lexikographie/dwdsmor + https://huggingface.co/zentrum-lexikographie/dwdsmor-open — SFST/SMOR-based morphology from the DWDS (Berlin-Brandenburg Academy). **Open Edition: GPLv2** (grammar, Python lib, automata, sample lexicon — free for use); the full DWDS-dictionary edition is all-rights-reserved with individual licensing. The current, actively maintained German option.
- **DEMorphy** — https://github.com/DuyguA/DEMorphy — **MIT**, DAFSA-based analyzer with dictionary files included (~2.7M forms); paper: https://arxiv.org/pdf/1803.00902. Not very actively maintained but license-clean.
- **Zmorge** — https://github.com/rsennrich/zmorge — German morphological lexicon **extracted from Wiktionary** for use with SMOR; pre-compiled analyzers at https://pub.cl.uzh.ch/users/sennrich/zmorge/. Lexicon inherits Wiktionary CC BY-SA.
- Also: Morphisto (older open SMOR-based analyzer). For declension/article exercises, DWDSmor or kaikki's German noun tables give case/gender/plural paradigms.

## 2. Sentence corpora usable as exercise material

- **Tatoeba** — https://tatoeba.org/en/downloads — weekly TSV exports: sentences, translation links, tags, per-user skill levels, audio index. Sentences: **CC BY 2.0 FR** (attribution to the contributor) with a separately downloadable **CC0 subset**. Redistribution in a derived product is explicitly fine with attribution. Counts (July 2026): **Italian 979k, German 776k, French 729k, Spanish 444k, Portuguese 443k** (English 2.04M for pairing). Audio is licensed **per file** by the contributor (empty license field = not reusable outside Tatoeba); audio counts: Spanish 119k, German 33k, Portuguese 21k, French 10k, Italian only 1.6k. Sentence–translation links let you build bilingual cloze cards directly. Caveat: uneven quality/register; the tags file + user-skill file help filter.
- **OpenSubtitles (OPUS)** — https://opus.nlpl.eu/legacy/OpenSubtitles-v2018.php (62 languages, hundreds of millions of sentences for each of the five); **OpenSubtitles2024**: https://huggingface.co/datasets/Helsinki-NLP/OpenSubtitles2024 under **ODC-BY**, with a stated intent of dev/eval use and a takedown policy. Legal caution: the underlying subtitle text is user-transcribed copyrighted dialogue — ODC-BY covers the database layer, not the underlying content. For a shipped product, treat it as a frequency/statistics source rather than verbatim exercise text. Useful derivative: https://github.com/orgtre/top-open-subtitles-sentences — cleaned most-common sentences + words per language from OpenSubtitles2018.
- **Leipzig Corpora Collection (Wortschatz)** — https://corpora.wortschatz-leipzig.de/ — news/web/Wikipedia corpora in standard sizes (10k–1M randomly shuffled sentences) for all five languages, many years available. Plain-text downloads. Licensing is **mixed**: some corpora are CC BY, but the general terms have historically been research/non-commercial oriented; **check per-corpus terms before redistribution**. Mirror: https://huggingface.co/datasets/imvladikon/leipzig_corpora_collection (268 languages, no explicit license stated).
- **UniversalCEFR** — https://universalcefr.github.io/ + https://huggingface.co/UniversalCEFR — 505,807 CEFR-labeled texts from 26 corpora across 13 languages, standardized JSON, sentence/paragraph/document granularity. **Non-commercial research** framing; each constituent corpus keeps its own license. The most direct route to CEFR-graded sentence material. Paper: https://arxiv.org/html/2506.01419.
- **Existing FOSS cloze tooling on Tatoeba**: https://github.com/jacopofar/grammar-quiz — open-source cloze-deletion generator over Tatoeba; prior art worth reading.
- Honorable mentions: Europarl/GlobalVoices/news-commentary via OPUS (formal register, permissive-ish), Wikipedia (CC BY-SA), and for German the ~211k-sentence readability corpus at https://arxiv.org/pdf/1909.09067.

## 3. Frequency data (verbs / forms / tenses)

- **SUBTLEX family** (subtitle-based, best proxy for spoken frequency) — index: https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexus and http://crr.ugent.be/programs-data/subtitle-frequencies. Per language: **SUBTLEX-ESP** (https://osf.io/xp6sz/), **SUBTLEX-PT** (http://p-pal.di.uminho.pt/about/databases, "freely available for research"), **SUBTLEX-DE**, **SUBTLEX-IT** (Crepaldi et al. — verify current URL), plus SUBTLEX-US/UK for English. Terms per Brysbaert: free with credit, "similar to CC BY-SA" but not formally CC — research-friendly, product use should be cleared. Because these are **per-form** (not per-lemma) counts, you can compute *tense/person frequency* directly (e.g., rank passato remoto forms vs. passato prossimo) — the frequency-ordered curriculum backbone.
- **wordfreq** (rspeer) — https://github.com/rspeer/wordfreq — combined multi-source frequencies for 40+ languages incl. all five; code MIT, data from CC sources. Frozen/archived by the author in 2024 (AI-polluted web rationale) — still perfectly serviceable for the high-frequency band a curriculum needs.
- **FrequencyWords** (hermitdave) — https://github.com/hermitdave/FrequencyWords — per-language frequency lists from OpenSubtitles 2016/2018; code MIT, lists CC-licensed (CC BY-SA — verify README). Quick and dirty, all five languages.
- **Routledge Frequency Dictionaries** — series page: https://www.routledge.com/Routledge-Frequency-Dictionaries/book-series/RFD. Spanish (Davies) and German (Tschirner) explicitly ship their **full text as tab-delimited support-material downloads** via the Routledge Resource Centre (https://resourcecentre.routledge.com/books/9781138686540, /9781138659780). French, Italian, Portuguese volumes also exist. Copyrighted — usable as an internal curriculum-ordering reference for book owners, not redistributable.
- **CEFRLex resources double as frequency data**: per-CEFR-level normalized frequencies of lemmas in L2 textbooks/readers (see §5).
- Mark Davies' Corpus del Español / Corpus do Português frequency lists: rich (incl. by-register), but paid licenses.

## 4. Grammar-exercise banks & CEFR grammar syllabi

### Openly published CEFR grammar syllabi (Reference Level Descriptions)
Council of Europe index of all RLDs: https://www.coe.int/en/web/common-european-framework-reference-languages/reference-level-descriptions

- **Spanish — Plan Curricular del Instituto Cervantes (PCIC)**: full grammar inventory per level pair is **free online as clean, parseable HTML**, e.g. https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/02_gramatica_inventario_a1-a2.htm (also `_b1-b2`, `_c1-c2`; parallel inventories for pronunciation, tactics, notions, functions). Hierarchically numbered topics with per-level splits and examples — the best de-facto machine-scrapeable grammar taxonomy of the five. Copyright: **© Instituto Cervantes, all rights reserved** — fine as a design reference/topic taxonomy (facts/structure), don't republish the text.
- **Portuguese — Referencial Camões PLE (2017)**: **free ebook PDF, A1–C2**, with grammar/notion/function inventories: https://www.instituto-camoes.pt/images/REFERENCIAL_ebook.pdf, plus **interactive inventories on the Camões portal** (https://www.instituto-camoes.pt/activity/centro-virtual/referencial-camoes-ple). The most openly accessible full syllabus of the five. Also QuaREPE and the new **U.Porto Referencial Lexical PLE** (2025).
- **German — Profile Deutsch**: A1–C2 (grammar/vocab specified only to B2), commercial book+CD-ROM (Klett/Langenscheidt) — **not open, not online**. Modern machine-readable substitute: **"German Grammar Profile for Learners: Pedagogical Feature Definition and Automated Extraction"** (Löfflad, Beuttler, Meurers, KONVENS 2025): https://aclanthology.org/2025.konvens-2.17/ — defines pedagogical grammar features per CEFR level with automated extraction; check the paper for the artifact repo.
- **Italian — Profilo della lingua italiana** (CVCL, Univ. for Foreigners of Perugia): A1–B2, book + CD-ROM — not openly machine-readable.
- **French — Beacco et al., "Niveau A1/A2/B1/B2 pour le français"** (Didier): the reference grammar inventories for French, print-only, not open. (No French equivalent of the PCIC's free HTML exists.)
- **Model to copy**: English Grammar Profile (https://englishprofile.org/) and **Open Language Profiles / CEFR-J** — https://github.com/openlanguageprofiles/olp-en-cefrj — CEFR-J English profile datasets released **CC BY** in machine-readable form; the format is a good template for a 5-language grammar tree.

### Exercise banks / courseware
- **COERLL (UT Austin) — the CC goldmine**: https://coerll.utexas.edu/coerll/materials/ — *Français interactif* (CC BY; 320+ videos, grammar + self-correcting exercises, conjugation tools), *Deutsch im Blick* + **Grimm Grammar** (CC BY; online German grammar with exercises), *Spanish Grammar in Context* (grammar explanations + quizzes tied to authentic video). Portuguese: COERLL's Brazilpod materials (*Tá Falado*, *ClicaBrasil*). CC licenses (mostly BY or BY-NC-SA — check per resource) allow adaptation with attribution. Also: https://open.umn.edu/opentextbooks/textbooks/deutsch-im-blick.
- **Kwiziq** — topic trees are **publicly browsable** per language and CEFR level: https://french.kwiziq.com/revision/grammar/by-cefr-level (A0–C1, ~500 French grammar topics), https://spanish.kwiziq.com/revision/grammar/by-cefr-level/cefr-a1, plus tense-by-level pages (https://french.kwiziq.com/french-tenses-by-cefr-level). French + Spanish only. Proprietary content, but the taxonomy (topic names × CEFR level) is visible and scrapeable as a curriculum reference.
- **Lingolia** (de/en/fr/es/it — including German articles/prepositions drills): topic pages public, exercises behind Lingolia Plus; fully copyrighted, reference-only.
- **DW Nicos Weg / dw.com/learngerman** — free A1–B1 German course, but DW content is copyrighted broadcast material, not CC; syllabus inspiration only.
- **Language Transfer** — free audio courses; donation-funded, no open license; audio-methodology inspiration, not a data source.
- **Wikibooks** language courses (CC BY-SA) and *Liberté* (open French textbook, CC BY-NC-SA) as further CC exercise text.

## 5. Machine-readable CEFR tagging

- **CEFRLex family** — https://cental.uclouvain.be/cefrlex/ — downloadable **tab-separated CSVs** of lemmas × normalized frequency per CEFR level, estimated from L2 textbooks/graded readers: **FLELex** (French), **ELELex** (Spanish), **DAFlex** (German), **EFLLex** (English), NT2Lex/SVALex/SweLLex. No Italian or Portuguese. License: individual resources are generally **research/non-commercial** — confirm per resource. The closest thing to "which words (incl. verbs) belong at which level" in machine-readable form.
- **UniversalCEFR** (see §2) — CEFR labels at text/sentence level, standardized JSON, 13 languages.
- **PCIC HTML inventories** (Spanish) and **Referencial Camões interactive inventories** (Portuguese) — scrapeable grammar-topic-per-level structures (©, taxonomy-reference use).
- **Kwiziq public topic trees** (French/Spanish) — scrapeable level-tagged grammar taxonomy.
- **German Grammar Profile (KONVENS 2025)** — CEFR-level grammar features with extraction code (see §4).
- **CEFR-J / Open Language Profiles** — CC BY datasets, English-only but the schema is reusable.
- Gap: **no open CEFR grammar dataset exists for Italian**; Profilo is print-only — triangulate from Lingolia/Kwiziq-style topic lists + CELI exam syllabi.

## 6. LLM-generation angle (evals & known weak spots)

- **MultiBLiMP 1.0** (TACL 2025, Jumelet et al.) — https://arxiv.org/abs/2504.02768 — 128k+ minimal pairs, 101 languages, subject–verb/participle agreement (number/person/gender), auto-generated from **UD + UniMorph** (a pipeline replicable to generate distractors). Finding: high-resource languages (all five) score near ceiling for large models; accuracy tracks Common Crawl frequency and **can deteriorate during post-training**.
- **MELA** (Zhang et al. 2024) — 10-language grammaticality-judgment benchmark (includes Italian, German, French, Spanish — verify exact list) covering morphology + syntax.
- **MORPHOGEN** — https://arxiv.org/html/2604.18914 — gender-aware morphological generation benchmark; LLMs still err on **gender agreement across gendered Romance languages**.
- **ALBA** (2026) — https://arxiv.org/pdf/2603.26516 — **European Portuguese** benchmark with an explicit morphology/inflection dimension. Directly relevant weak spot: LLMs **default to Brazilian Portuguese** even when told otherwise (see also https://learn-portuguese.org/language-learning-with-chatgpt), which matters for the **future subjunctive** (routine in EP) and 2nd-person forms.
- Metalinguistic-knowledge eval across languages: https://arxiv.org/pdf/2602.02182 — top models are form-generation-strong but explanation-weaker.
- No published eval specifically isolating **Italian passato remoto** surfaced; the known risk is the irregular "1-3-3" pattern verbs. Practical takeaway: for these five high-resource languages LLM conjugation is near-ceiling, but the failure modes are (a) gender agreement, (b) dialect/variety defaults (EP vs BP), (c) rare literary tenses, (d) regressions from post-training — so **generate with the LLM and validate every inflected form against kaikki/UniMorph/Lefff/Morph-it/LABEL-LEX/DWDSmor before it enters a card**.

## Cross-cutting recommendations

1. **License-clean core stack**: kaikki.org (CC BY-SA) + UniMorph (CC BY-SA) for paradigms; Tatoeba (CC BY / CC0 subset) for sentences; wordfreq/FrequencyWords + SUBTLEX for ordering; COERLL (CC BY) for pedagogical text; Referencial Camões PDF + PCIC HTML + Kwiziq trees as syllabus references.
2. **Watch share-alike**: CC BY-SA on kaikki/UniMorph/Tatoeba-BY means derived *data* redistributed in decks should carry attribution and share-alike on that data layer — plan the attribution screen now.
3. **Avoid as foundations**: Verbix/Cooljugator (proprietary), OpenSubtitles verbatim text (copyright-grey), Leipzig for redistribution (terms unverified), Lingolia/DW/Kwiziq content (copyrighted).
