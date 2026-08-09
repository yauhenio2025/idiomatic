# Mac codex prompt — Hammer's/Practising German Grammar structuring

Paste everything below the line into a codex session on the Mac.

---

You are structuring two German grammar books into verified, learnable
exercise data. Work ONLY inside a new workspace `~/llms/grammar-books/`
(create `de_hammer/` under it). Do not touch `~/llms/factory-node/`,
any render or bookscan process, or anything outside your workspace. The
job is CPU-light text work; nothing needs pausing.

INPUTS (in ~/Downloads/):
1. "Hammer's German Grammar and Usage" … 7th Edition … .epub — the
   reference grammar. EPUB: unzip, chapters are XHTML.
2. "Practising German Grammar … Kaiser; Kohl …" .pdf — the official
   workbook: exercises cross-referenced to Hammer's sections, with an
   answer key in the back. The PDF has a NATIVE TEXT LAYER (verified) —
   extract text faithfully (make a venv and pip install a PDF text
   library of your choice; keep page numbers as anchors). No OCR.

Copy both books into the workspace first; never modify the originals.

TASK — chapter by chapter over the WORKBOOK:
1. Parse every exercise: its number, instruction (English and/or
   German, verbatim), the Hammer's §-references it cites, and every
   item (numbered sentence/prompt) verbatim.
2. Parse the answer key and MATCH key entries to exercise items 1:1.
3. For each item build the CARD-READY solution: the FULL sentence with
   the answer integrated, with the answer span marked as
   `<mark>…</mark>`. Rules, strictly in this order:
   - Gap-fill items: splice the key's answer into the gap — mechanical,
     no rewording.
   - Transformation/rewrite items where the key prints the full
     transformed sentence: use the key's sentence verbatim, mark the
     changed span.
   - Anything where producing a full sentence would require inventing
     words the book didn't print: DO NOT invent — record the raw key
     answer and flag `needs-reconstruction`.
   - Key offers alternatives: keep them all in `alternatives`.
4. TRANSCRIBE, NEVER CORRECT: if the book/key looks wrong or
   inconsistent, flag `source-suspect` with a note — do not fix German.

OUTPUT (all under ~/llms/grammar-books/de_hammer/):
- `chapters/chNN.json` per workbook chapter:
  {chapter, title, hammer_sections: [...], exercises: [{ex_no,
   instruction, page, items: [{item_no, prompt, answer_key_raw,
   full_solution_html, alternatives: [...], flags: [...],
   key_page}]}]}
- `MANIFEST.json`: per-chapter counts (exercises, items, matched key
  entries, flagged items by flag type), source file SHA-256s, and the
  extraction method used.
- `QA_REPORT.md`: unmatched items, count mismatches between exercises
  and key, ambiguous cases, extraction anomalies — every one listed
  individually. Honest gaps beat silent padding.
- Also extract Hammer's chapter/section HEADING TREE only (numbers +
  titles, no body text) to `hammer_toc.json` — it becomes the lesson
  outline skeleton later.

METHOD: deterministic and re-runnable (a fresh run reproduces identical
JSON); work chapter by chapter and write each chapter's file as you
finish it, so partial progress survives; finish with a one-paragraph
summary of totals and the flag counts.
