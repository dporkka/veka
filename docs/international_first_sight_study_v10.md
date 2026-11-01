# Veka 0.10 international-root sources and first-sight study (NONCANONICAL)

**Research-only protocol and executable local tooling.** No candidate has been
adopted. The original 317 roots and 708 compounds remain unchanged, and no
human participants or comprehension measurements are included.

## Source-linked investigation (not verification)

Run:

```sh
python3 -m veka international-plan --output /var/tmp/veka-v10-review.json
python3 -m veka lexical-readiness --candidates data/international_candidates_v10.csv \
    --evidence data/international_source_leads_v10.csv
```

`data/international_source_leads_v10.csv` contains **14 unreviewed lexical
leads** for the 4 draft meanings music, doctor, hospital, and camera in
Indo-European, Niger-Congo, Austronesian, and Japonic language families.
These entries were sourced from public Wiktionary lexical pages:

- Music: [Portuguese música](https://en.wiktionary.org/wiki/m%C3%BAsica),
  [Tagalog musika](https://en.wiktionary.org/wiki/musika),
  [Swahili muziki](https://en.wiktionary.org/wiki/muziki),
  [Malay muzik](https://en.wiktionary.org/wiki/muzik).
- Camera: [Indonesian/Swahili kamera](https://en.wiktionary.org/wiki/kamera),
  [Japanese カメラ](https://en.wiktionary.org/wiki/%E3%82%AB%E3%83%A1%E3%83%A9),
  [Portuguese câmera](https://en.wiktionary.org/wiki/c%C3%A2mera).
- Doctor: [Indonesian dokter](https://en.wiktionary.org/wiki/dokter),
  [Swahili daktari](https://en.wiktionary.org/wiki/daktari),
  [Portuguese doutor](https://pt.wiktionary.org/wiki/doutor).
- Hospital: [Tagalog ospital](https://en.wiktionary.org/wiki/ospital),
  [Swahili hospitali](https://en.wiktionary.org/wiki/hospitali),
  [English hospital](https://en.wiktionary.org/wiki/hospital).

**None** of these records claims independent semantic verification, independent
historical origins, first-sight recognition or acoustic intelligibility.
Source-derived words are recorded as short factual forms, with links for
attribution/review; Wiktionary content is available under its applicable
[license terms](https://en.wiktionary.org/wiki/Wiktionary:Copyrights).
Each item is marked `attestation_verified=no`,
`semantic_equivalent=unknown`, and a blank `semantic_reviewer`.
The CLI will not count any such source as a verified family. Source-link
syntax is checked locally; this is **not** external authenticity verification.

Researcher next action: Independently check exact meaning, local written
forms and phonetics against primary dictionaries and qualified speakers, then
record named/pseudonymous reviewers and actual outcomes in a **separately
reviewed** evidence file. The study may compare differently accented forms,
but that alone does not make them genealogically independent. For example,
Tagalog `ospital`, Swahili `hospitali`, and English `hospital` have
borrowing relationships despite belonging to different recipient families.
Portuguese `doutor` need not mean a practising physician; investigate this
false friend before claiming equivalence.

## Prepare a blinded 24-word written-first-sight study

Run this locally from the repository root. Keep researcher keys and participant
responses under a private directory **outside the repo**. The paths are
examples; do not check them into git.

```sh
mkdir -p /secure/veka-study /secure/veka-study/participants
python3 -m veka international-manifest \
  --participant VKA101 \
  --candidates data/international_candidates_v10.csv \
  --output /secure/veka-study/participants/VKA101.csv \
  --answer-key /secure/veka-study/VKA101-key.csv

python3 -m veka international-session \
  --manifest /secure/veka-study/participants/VKA101.csv \
  --output /secure/veka-study/participants/VKA101.json
```

Use real **researcher-chosen** secure paths rather than literally `/secure` if
that location is unavailable. The participant JSON contains only pseudonym,
randomized trial ID and word form. Neither meanings nor core/candidate
allocations appear there. **Never give participants the answer key.**

Open `site/cognate-study.html` locally in a browser and load the
participant JSON. The same interface accepts v0.7 18-item cognate sessions
and v0.10 24-item international sessions. It does not send responses to any
server. Its export is a participant-only response CSV. Browser elapsed times
are approximate and interruptions must be scrutinized by a researcher.

Run a complementary pseudonym (for example `VKA102`) with the same seed to
place **every one of the 24 meanings** in the opposite condition. Pseudonyms
must be randomly assigned to eligible participants independently of language,
education, or expected performance. A pair of IDs is a **format demonstration**
only, not a powered experiment.

Suggested pre-registered multilingual groups: English, Brazilian Portuguese,
Mandarin, Swahili and Tagalog. This covers Germanic, Romance, Sinitic, Bantu,
and Philippine language branches; English and Portuguese are both
Indo-European and should not be miscounted as two top-level families.
First-language/family fields are self-reported, not independently confirmed.
Do not recruit, record or analyze participants without appropriate consent
and data-management practices.

## Researcher-only manual scoring

After *real* responses exist:

```sh
python3 -m veka international-judge-sheet \
  --answer-key /secure/veka-study/VKA101-key.csv \
  --responses /secure/veka-study/VKA101-responses.csv \
  --output /secure/veka-study/VKA101-judge.csv
```

The output is a **PRIVATE** sheet containing glosses/answers but not
experimental condition labels. It deliberately leaves `correct` and
`repair_count` blank. Qualified human adjudicators must review responses
and complete those columns independently. Reject or flag interrupted trials,
pre-exposure, ambiguous synonyms and implausible timings according to a
pre-registered rule; do not silently treat missing observations as zero.
The existing descriptive scorer accepts a completed judgment sheet:

```sh
python3 -m veka international-score \
  --answer-key /secure/veka-study/VKA101-key.csv \
  --annotated /secure/veka-study/VKA101-judge.csv
```

A real study needs separate human-recorded, speaker-balanced audio tasks,
delayed retention and a pre-registered analysis plan. The generated forms
currently have **no human validation**, and the scorer makes **no causal
claim or adoption decision**. Uncertain results mean retaining the
canonical roots and grammar, not promoting a recognizable-looking term.
