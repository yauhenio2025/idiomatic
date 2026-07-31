# `it_genere_plurali`

- Cluster: `5 Genere e plurali`
- Bank: `it_genere_plurali.json` — 159 entries
- Format: F1 primary; F5 for three orientation cards covering article onsets, regular plural classes, and irregular/invariant plurals
- Verification: Tier A noun/gender/plural/article lookup
- Recommended live size: 42 F1 cards plus 3 F5 landmarks

## Generator guidance draft

Choose a noun and test exactly one retrieval target: singular article+noun, plural article+noun, or the plural alone. Use the bank's fields literally. Mix `il/i`, `lo/gli`, masculine `l'/gli`, `la/le`, and feminine `l'/le`; ensure `lo/gli` is drilled before s+consonant, z, ps, and gn. Weight normal `-o→-i`, `-a→-e`, and `-e→-i` heavily, then interleave masculine Greek nouns in `-a`, feminine abbreviations in `-o`, invariant stressed/loan nouns, and irregulars. Meaning-sensitive plurals must retain the banked reading: body/collective `braccia`, `dita`, `ginocchia`, `ossa`, plus `uova`, `paia`, `migliaia`, `centinaia`, and `lenzuola`.

## Self-check

- JSON parsed; 159 unique nouns, above the 150 minimum.
- A mechanical onset/article audit passed, with the intentional irregular `gli dei` and feminine plural articles after gender-changing plurals handled as exceptions.
- Common-gender `collega` was removed during the ambiguity pass.
- Regular, spelling-changing, invariant, and irregular plural classes were reread separately.
- Review question: body-part nouns also have masculine plurals in special senses (`bracci`, `diti`, `ossi`). Keep those out of single-answer F1 cards unless the sentence explicitly contrasts the mechanical/individual sense.

