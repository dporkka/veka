# Proper-name compatibility — parser improvement (November 2026)

**Status:** a conservative input-handling improvement to the established
single-token proper-name position, not a new Veka word, phoneme, pronunciation
standard, or full multilingual naming grammar.

A capitalized proper name that is **not** already a canonical Veka word can
occupy an ordinary noun-phrase head position. This works in strict Core clauses,
fully scoped Precise logic, and the read-only beginner gloss:

```text
Mi lin São.              I see São.
Łódź pa gos.             Łódź went.
Mi lin O’Connor.         I see O’Connor.
Zi São gos ve ti gos yu. São goes AND you go.
```

These English readings are illustrative; proper names are returned unchanged
in the AST and are never translated or added to the canonical lexicon.

## Accepted single-token forms

* The first character must be a Unicode uppercase/titlecase letter.
* The name consists of Unicode letters and combining marks. Internal ASCII
  apostrophes, typographic apostrophes (`’`) and hyphens (`-`) may separate
  nonempty letter groups. Input is normalized to Unicode NFC.
* Ordinary Veka words take precedence over proper-name interpretation;
  `Mi` remains the pronoun `mi`.
* Empty segments, numbers, controls, bidi formatting characters, emoji and
  arbitrary punctuation are rejected. Names are bounded to 128 code points.

## Limitations and future work

Names containing spaces (`São Paulo`) and names written exclusively in
uncased scripts (`東京`) remain unsupported in the frozen Core grammar;
**do not split names into separate noun phrases or silently reinterpret
unrecognized tokens**. If broad multilingual coverage is required, first
design and version an explicitly delimited name syntax, independently validate
round-tripping and rendering, and test readability with native-language users.

This parser change does not make foreign names pronounceable under Veka's
phonotactics and does not add speech, transliteration, source-language
directionality, or support in the experimental featural SVG renderer. It
preserves the canonical root inventory and the locked grammar document.

Check with `python -m unittest discover -s tests -p test_unicode_proper_names_v09.py -v`.
