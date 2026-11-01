# Familiar vocabulary pilot, version 1

This is a working, **experimental lexical profile**, not a change to canonical
Veka. It replaces five nouns and their registered compositional compounds while
preserving Core grammar, meanings, valency, logical particles and numbers. It is
a starting point for the requested vocabulary reform, not a complete reform.

| Core | Pilot | Meaning | Caution |
|---|---|---|---|
| woi | mu-si-ka | music | Recognizable in some languages; not universal |
| vik | se-ko-la | school | Adapted spelling; recognizability untested |
| sau | bu-ku | book | Familiar in some languages; not universal |
| noi | os-pi-tal | hospital | Adapted pronunciation; meaning needs review |
| dik | ka-me-ra | camera | Meaning and recognition need review |

These editorial proposals reuse the existing international candidate list. They
are not validated multilingual attestations or evidence of better learning.
They add syllables and likely favor some language backgrounds. Grammar and
pronunciation regularity are retained at the cost of less familiar spellings.

```sh
python3 -m veka.familiar parse 'Mi sen mu-si-ka.'
python3 -m veka.familiar convert to-familiar 'Mi sen woi-val.'
python3 -m veka.familiar convert to-core 'Mi sen mu-si-ka-val.'
```

The dedicated parser accepts strict Core clauses in the pilot lexicon; it
rejects old replaced forms even when capitalized. Existing default commands,
other profiles, teaching materials and the canonical dictionary are unchanged.
Registered compounds follow their replaced head and retain their meanings. The
conversion utility works on whole lexicon tokens and preserves basic case and
punctuation; it is not a translator, grammar validator, or safe for a proper
name that happens to equal a replaced word. Treat source and destination as
explicitly versioned; do not mix them in one utterance. Hyphens separate
syllables as in existing Veka. Neither spelling checks nor exact surface
collision checks establish acoustic distinctness.

Before widening or standardizing the profile, review each intended sense and
false friends, compare first-sight understanding and retention for diverse
language backgrounds, test pronunciation and noisy listening, and audit all
lessons and downstream tools. No human outcomes are currently available.
