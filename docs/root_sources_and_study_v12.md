# Veka 1.2: multilingual root-source review and blinded root study

**Noncanonical research tools.** No lexical replacement, syntax modification,
new canonical alias, approved cross-language cognate, speech recording, or
human comprehension result is supplied by these commands.

## Source-linked research packet

Run the thirteen sourced *leads*, spanning the existing experimental roots
`do` (data), `woi` (music) and `vik` (school):

```sh
python3 -m veka root-sources
python3 -m veka root-sources --leads /path/to/reviewed-copy.csv
```

Data: `data/root_source_leads_v12.csv` (13 records in 3 concepts).
All are `review_status=pending`, `semantic_match=unknown`, and have empty
reviewer fields by design. External source references are supplied for
**research screening**, not proof of a complete independent review.
Existing `music_source_screening_v10.csv` and
`global_music_leads_v07.csv` are not overwritten or automatically
converted into independently reviewed evidence.

Each source has a target meaning, experimental Veka form, language/family/
branch, the original word, a URL, a scope note, and one of three relation types:

- `candidate_like` — research hypothesis of resemblance; NOT observed
  first-sight recognition.
- `different_common_form` — contrasting expression, important negative
  control; never counted as supporting resemblance.
- `false_friend` — misleading similarity/semantic mismatch. Portuguese
  **data** means a calendar date in ordinary use; the proposed Veka `da-ta`
  denotes information/data. This is a blocker *hypothesis* for comprehension
  study, not automatic invalidation for all Portuguese speakers.

Sources include directly linked [Portuguese data](https://en.wiktionary.org/wiki/data),
[Mandarin shuju](https://en.wiktionary.org/wiki/%E6%95%B0%E6%8D%AE),
[Swahili muziki](https://en.wiktionary.org/wiki/muziki),
[Indonesian sekolah](https://en.wiktionary.org/wiki/sekolah),
[Portuguese escola](https://en.wiktionary.org/wiki/escola),
[Mandarin xuexiao](https://en.wiktionary.org/wiki/%E5%AD%B8%E6%A0%A1),
[Japanese gakko](https://en.wiktionary.org/wiki/%E5%AD%A6%E6%A0%A1),
and [Swahili shule](https://en.wiktionary.org/wiki/shule).
These are short lexical leads; follow any respective content licenses for
reuse. The World Loanword Database (https://wold.clld.org/) provides
methodology for distinguishing attested loanwords from independently inherited
cognates.

### Independent-source review protocol

A fluent independent reviewer should inspect the **specific language section**
of the cited original source. Record sense equivalence, pronunciation,
regional usage, borrowed versus inherited history (if independently known),
register and false-friend risk. A book/dictionary's publication does not
automatically verify its attribution to a specific Veka sense. A reviewer may
set `review_status=approved` only with `semantic_match=yes`, plus their
reviewer identifier and nonempty explanation. A false friend cannot be approved
as matching evidence. Use `rejected` with an explanation for negative review.
Review status claims are not authenticated or independently checked by
the program, and approvals do not imply measured human recognition.

The source audit validates the schema, target concept mapping, public HTTPS
URL structure, uniqueness by concept/language, and required reviewer fields.
It counts reviewer-**claimed** lexical evidence without automatically
writing to `global_evidence_v07.csv`, deducing language-family independence,
promoting candidates, or estimating speech intelligibility. Contact-driven
borrowings may cross many recipient families without independent origin.

## First-sight controlled study preparation

Use the prior `data/cohort_roster_template_v10.csv` header with a real,
**private**, consented pseudonymous participant roster. The reviewer roster
must be balanced at an even number in each language-background stratum:

```csv
participant_id,background_stratum
P101,English-L1
P102,English-L1
P201,Portuguese-L1
P202,Portuguese-L1
```

This is a **format illustration**, not enrolled participants. Recruitment,
consent, proficiency and exposure screening, and statistical power analysis
remain outside this tool. For a real study include additional strata such as
Mandarin-L1, Swahili-L1 and Indonesian-L1.

```sh
python3 -m veka root-study-plan \
  --roster /private/cohort-roster.csv \
  --participants-dir /private/participant-packets \
  --researcher-dir /private/researcher-keys \
  --seed 20261101
```

Existing `cohort_plan.write_cohort_plan` writes separated private directories,
owner-only files on POSIX and rejects existing/overlapping destinations.
There is no email, network transmission or automatic outcome collection.

- All eight structurally valid international-root proposals are tested against
  their current canonical roots (including music, data and school).
- For each item, every participant sees **one** form only. Complementary arms
  ensure one core and one candidate exposure per **two-person background stratum**
  for each concept. For each participant, four forms are core and four
  candidate; presentation order is randomized reproducibly using a seed.
- Participant packets contain opaque trial IDs, presented spellings and blank
  response/time/exposure fields. They exclude the correct meaning, condition
  labels and answer keys.
- Only the researcher directory contains target glosses, condition labels and
  arm assignments. A clean file write is evidence of a generated study plan,
  not real enrollment, participant responses or validity of the randomization.

**Pre-register** primary first-sight semantic correctness, acceptable synonyms,
response time, false-friend errors, exclusions and critical safety errors.
Separately compare delayed vocabulary retention, time to learn, spontaneous
production and natural recordings in quiet/noise conditions. For a validated
claim, estimate participant/item uncertainty, report by actual language
background, and measure total communication time (including repairs), not just
weighted hypothesis scores or form length.

Even positive human reading observations would not automatically justify
replacing `do`, `woi`, `vik`, or any canonical Veka root. A later,
explicitly versioned compatibility proposal and evidence review would be
required. Until such evidence is collected, **no adoption is authorized**.

Run tests:

```sh
python3 -m unittest discover -s tests -p 'test_root_sources_v12.py' -v
python3 -m unittest discover -s tests -p 'test_root_study_v12.py' -v
make validate
```
