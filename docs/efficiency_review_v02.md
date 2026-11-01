# Veka 0.2 — per-language independent-review packets

**Research-only.** Zero translations from Indonesian, Turkish, Esperanto or
Interlingua have been independently checked by this repository. The CLI cannot
recruit reviewers, verify identity/fluency, check language semantics or establish
human learning gains. A reviewer ID is **self-declared**, not an attestation
authenticated by software.

## Phase A: make blank, source-locked review packets

Give each of the four languages to **two different qualified bilingual
reviewers**. They must work independently and not share drafts. For Indonesian
(`id`), for example:

```sh
python3 -m veka efficiency-review-plan --language id \
  --reviewer ind_editor_A --output /private/ind-editor-A.csv
python3 -m veka efficiency-review-plan --language id \
  --reviewer ind_editor_B --output /private/ind-editor-B.csv
```

Repeat with `--language tr` (Turkish), `eo` (Esperanto), `ia`
(Interlingua). Omitting `--language` creates all **40** items for a
qualified four-language reviewer, but per-language review is strongly preferred.

Each 10-row CSV carries the immutable canonical Veka utterance, existing
English/Mandarin/Portuguese editorial **reference readings**, and a SHA-256
source digest. Reviewers fill `target_text` in their assigned language and
record three assessments: `meaning_equivalent`, `natural` (yes/no/uncertain),
and `critical_ambiguity` (yes/no/uncertain). They can add optional concise
`review_notes`, without identity or personal data. **The editorial references
are not a gold-standard semantic key**. Reviewers must independently adjudicate
the intended Veka meaning. The forms in the default reference corpus were not
previously professionally verified.

The packet rejects malformed/unprintable text, CSV formula prefixes in target
translations, duplicate/missing rows, altered reference material, changed
digests, unexpected fields, identity switches inside a sheet and oversized
notes. Do not alter protected reference columns. If a sentence permits two
reasonable interpretations, mark `uncertain` or `critical_ambiguity=yes`.
Never guess a target form to make a row complete.

## Phase B: compare two independent sheets without promotion

```sh
python3 -m veka efficiency-review-check \
  --review-a /private/ind-editor-A.csv \
  --review-b /private/ind-editor-B.csv
```

The check reports `pending`, `blocked`, and `accepted` rows.
A sentence is accepted only when both independent sheets contain the
**exact same Unicode-normalized text**, both mark meaning and naturalness
`yes`, and both mark critical ambiguity `no`. Different valid natural
translations are currently a **blocking disagreement**. Preserve the original
independent sheets, defer the item, and arrange a separate documented blinded
adjudication round rather than editing original reviews into artificial agreement.
The current tool does not model a third-reviewer adjudication; reviewers can
independently submit an additional consensus round with preserved source
records, but it does not automatically authenticate that process.
The tool verifies two distinct *IDs*, not two distinct people.

## Phase C: export, without overriding canonical vocabulary

Only when all ten target-language sentences have matching positive reviews:

```sh
python3 -m veka efficiency-review-check \
  --review-a /private/ind-editor-A.csv \
  --review-b /private/ind-editor-B.csv \
  --output /private/efficiency-reviewed-id.json

python3 -m veka efficiency-review-plan --language tr \
  --reviewer tr_editor_A \
  --manifest /private/efficiency-reviewed-id.json \
  --output /private/tr-editor-A.csv
# Independently prepare a second Turkish review sheet, then:
python3 -m veka efficiency-review-check \
  --manifest /private/efficiency-reviewed-id.json \
  --review-a /private/tr-editor-A.csv \
  --review-b /private/tr-editor-B.csv \
  --output /private/efficiency-reviewed-id-tr.json
```

Continue for `eo` and `ia`. Every output is an **immutable new file**:
existing files are never overwritten. A check with incomplete, negative or
mismatched reviews refuses `--output`. Earlier per-language consensus
annotations remain in the derived research manifest. The new language variants
have no human-derived syllable/ambiguity measurements yet; they are still
`null`, not invented zeroes. The review fingerprints are evidence links to
reviewer IDs and source text, **not cryptographic signatures**. Store source
CSV sheets in a protected location, outside the public repository.

## Phase D: human study — NOT yet conducted

After qualified reviewers verify meaning, define separate reading and spoken
listening conditions, equal exposure/training, and recruited participant groups.
For reading, expose one meaning **once per participant** (no duplicate
translations across conditions) and measure elapsed time to recover meaning.
For listening, obtain real human recordings and acoustic controls before any
claims about syllable/time efficiency. Preserve a condition-blind participant
packet and separate researcher key, randomize item order and language
assignment, preregister noninferiority error margins, and score responses with
independent blinded judges.

The existing `efficiency-score` CLI accepts a genuine pseudonymous
eight-column CSV and calculates **correct meaning responses per total elapsed
plus repair minute** (including time spent on incorrect trials). It does not
gather consent, record responses, certify scoring, or perform causal inference.
The checked-in `data/efficiency_trials_v01.csv` remains header-only. No
real participant observation, enrollment, recording or verified independent
translation has been fabricated for this change.
