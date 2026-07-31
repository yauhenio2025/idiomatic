# `pt_gender_core`

- Cluster: `5 Gênero & Artigos`
- Bank: `pt_gender_core.json` — 120 entries
- Format: F1 primary; F3 for attested noun, numeral, possessive, and contraction errors
- Verification: Tier A curated gender/agreement lookup
- Recommended live size: 36 cards: 50% attested core, 25% `-ma/-agem` pattern extension, 25% numeral/contraction agreement

## Generator guidance draft

Use Brazilian Portuguese. For noun rows, create one blank for an article, demonstrative, possessive, or adjective whose form is determined by `gender_or_correct`. For frame rows, preserve the exact construction and ask for the full value in `gender_or_correct`. Prioritize `problema/programa/idioma/tema/sistema`, `mensagem/viagem`, `ordem/lei/voz/equipe/fonte`, `site/e-mail/link`, `dois/duas`, `uns/umas`, agreeing hundreds, and contractions such as `no site`, `na ordem`, `à lei`, `numa mensagem`. Do not include common-gender human nouns without an explicit referent.

## Self-check

- JSON parsed; exactly 120 entries with consistent fields.
- Attested nouns and numeral/contraction frames are frequency-first.
- The suffix families were checked for exceptions. An initial overgeneralization of `-ma` to `asma` was caught; the bank now correctly records `a asma`.
- Article, possessive, numeral, hundreds, adjective, and contraction agreement all appear.
- No unresolved item remains; generated cards should still state “Brazilian Portuguese” because article use with country names differs across varieties.

