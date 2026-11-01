# Veka 0.7 cognate/internationalism pilot — opt-in, not canonical

**Status:** research instruments only (2026-11-01). There are **zero** verified
multilingual attestations, human participants, audio recordings, and adoption
decisions. The canonical 1,025 entries, grammar, and both tonal/toneless
profiles are unchanged. These are proposed **internationalisms and loanword
adaptations**, not universally inherited historical cognates.

## Research questions

1. For **10 concepts not represented by a canonical primitive root**, do
   recognizable internationalisms produce higher first-sight semantic
   identification than matched-syllable nonce Veka forms?
2. For **eight existing meanings**, do longer recognizable words reduce the
   total learning/comprehension cost enough to compensate for extra syllables
   relative to established Veka words?

Neither a structural pass nor a shared written spelling establishes historical
cognacy, family-independent recognition, or spoken comprehension. Avoid using
national population estimates as if they were independent language-family
counts. Some internationalisms originated in only one language family and
spread by borrowing.

## Versioned datasets

- `data/cognate_candidates_v07.csv` — exactly 10 unadopted additions plus 8
  unadopted replacement comparisons. Candidate and nonce controls are
  explicitly stored (not dynamically invented during testing).
- `data/cognate_evidence_v07.csv` — empty provenance log. Fields:
  `concept_id,language,language_family,attested_form,citation,reviewer,verified`.
  Only attributable human-checked entries with `verified=yes` are counted.
  The validator **does not** check source truth or genealogy.
- `veka/cognates.py` — lexical sanity checks; randomized research manifests;
  descriptive scoring. No parser registration or dictionary writes.

## Run the tools

From the repository root, Python 3.10+:

```sh
python -m veka cognate-audit --output /tmp/veka-cognate-audit.json
python -m veka cognate-manifest --participant P001 --arm 0 \
  --output /tmp/p001-cognate.csv --answer-key /tmp/p001-cognate-key.csv
python -m veka cognate-manifest --participant P002 --arm 1 \
  --output /tmp/p002-cognate.csv --answer-key /tmp/p002-cognate-key.csv
# Only after real, manually adjudicated observations have been collected:
python -m veka cognate-score --answer-key /tmp/p001-cognate-key.csv \
  --annotated /tmp/p001-cognate-observed.csv
python -m unittest discover -s tests -v
```

**Do not** put researcher keys where participants can read them. The program
refuses to overwrite an existing participant sheet or key; each filename
should be unique. Assign arms randomly, rather than allocating arms from
demographic attributes or pseudonym spelling. Different arms reverse the
presentation conditions for each concept. Participant sheets have blank
responses, response times, and prior-exposure columns; no outcomes are
fabricated. A participant sees one version of each meaning, not both.

### Experimental conditions

| Category | Meanings | Arm-balanced condition A | Arm-balanced condition B |
|---|---:|---|---|
| Addition | 10 | international candidate | invented nonce control |
| Replacement | 8 | canonical primitive root | international candidate |

For every participant: **5 additions in each condition** and **4 replacements
in each condition**, randomly ordered. In opposite arms, the condition
assigned to each concept reverses. Nonce forms match candidate syllable
counts and the basic CV/CVC patterns at the time this fixed dataset was
generated. They have no canonical Veka meanings and are *not* proven to be
meaningless across natural languages.

Score `correct` only after independent human judgment against the answer key,
with accepted synonyms prespecified. Record `correct` as 0/1,
`repair_count` as a nonnegative integer, and
`response_ms` as elapsed milliseconds when available. A complete set of
observations is required to compute descriptive summaries. An output file
proves only that **supplied rows** were scored; it does not prove a real human
study occurred.

### Important risks and limitations

- `da-ta` is a prominent false friend: *data* in Portuguese ordinarily
  denotes a **calendar date**, not English *data*.
- `ro-bo` drops the final consonant of some donor words.
- `so-ko-la-te` requires four syllables, much longer than most primitive
  Veka roots.
- `kon-pu-ta` is a **hypothesis** about retention of a nasal consonant,
  not a measured improvement over the earlier `ko-pu-ta` draft.
- `vi-di-o` is used rather than `vi-de-o` because `de` is a protected
  grammatical syllable. It may be **less** recognizable.
- Adaptation sometimes collapses natural-language contrasts, and word forms
  could resemble unintended natural words. Nonce controls and loans require
  screening by diverse humans, with recorded pronunciation testing.
- The single written-form study cannot establish acoustic comprehension,
  learning retention, population-wide usefulness, actual speaking speed,
  language-family equity, or causal effectiveness of the vocabulary change.
  Additional preregistered listening and delayed-recall experiments are needed.
- The structural auditor does not model speech noise, meaning scope,
  connected-speech segmentation or phoneme confusion. Test these separately.

## Promotion gate

Do **not** promote any candidate from this pilot until it has:
(1) verified and independently reviewed donor attestations, including
genealogically diverse languages; (2) an explicit semantic sense and
false-friend assessment; (3) measured initial comprehension and time-to-learn
across diverse participants; (4) speech-in-noise, pronunciation and
retention evidence; (5) a demonstrated net improvement in **correctly
understood meaning per unit total time**, including repairs; and (6) a
versioned migration and compatibility plan.

An inconclusive experiment means **keep the existing vocabulary**.
