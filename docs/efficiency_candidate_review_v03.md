# Veka efficiency research — candidate-bound independent ratings (v0.3)

**Research-only. No language design changes or human validation results.**

The 0.2 workflow asked two independent translators to invent *exactly the
same wording*. That is overly restrictive: two different natural translations
may be semantically equivalent and independent authorship does not imply
character-for-character agreement. The preferred v0.3 workflow splits
**authorship of a fixed candidate** from **two independent evaluations of that
same candidate**.

This workflow does **not** authenticate author or reviewer identities, language
competence, consent, or reviewer independence. Source hashes only protect
against accidental changes or undetected edits *relative to a supplied local
manifest*. Meaning equivalence is not machine-verifiable.

## 1. Candidate author drafts one language

A qualified human translator authors ten candidate readings, anchored to the
existing Veka, English, Mandarin and Portuguese editorial reference corpus:

```sh
python3 -m veka efficiency-review-plan \
  --language id --reviewer ind_author \
  --output /private/ind-candidate.csv
```

Fill **only** `target_text` and optional `review_notes` on every row. Leave
`meaning_equivalent`, `natural`, and `critical_ambiguity` empty: those are
the independent reviewers' decisions. The references are editorial and
**not a verified gold standard**: flag uncertain semantics and do not silently
translate unclear Veka propositions. The candidate author may not be either
reviewer. Keep the candidate source file and its digest private and unchanged
after reviewers begin. For every change to a candidate, generate new rating
packets and preserve previous records as a separate version.

Repeat with `tr` (Turkish), `eo` (Esperanto) and `ia` (Interlingua).
No candidate translations are filled or fabricated by the software.

## 2. Generate two independently rated copies

```sh
python3 -m veka efficiency-review-bind \
  --candidates /private/ind-candidate.csv \
  --reviewer ind_reviewer_A \
  --output /private/ind-A.csv

python3 -m veka efficiency-review-bind \
  --candidates /private/ind-candidate.csv \
  --reviewer ind_reviewer_B \
  --output /private/ind-B.csv
```

Each reviewer independently fills the three yes/no/uncertain flags and optional
notes. **Do not change** the `target_text` or source columns. The two reviewers
are separately instructed to evaluate candidate meaning equivalence,
naturalness and critical ambiguity, and should have suitable language expertise
and no access to each other's judgments. The software checks distinct
pseudonymous IDs and all ten item IDs, but cannot prove that separate people
performed the review.

The source-locked candidate sheet and two bound review packets are stored in a
protected directory and created with **0600 file permissions**. Do not publish
completed review files without an explicit privacy and consent assessment.
A normal CSV spreadsheet may interpret some text as formulas; this tool rejects
formula-leading translation strings and notes at validation time.

## 3. Fail-closed audit and optional research-only export

```sh
python3 -m veka efficiency-review-check \
  --candidates /private/ind-candidate.csv \
  --review-a /private/ind-A.csv \
  --review-b /private/ind-B.csv
```

Only if **both** reviewers explicitly mark `meaning_equivalent=yes`,
`natural=yes`, and `critical_ambiguity=no` for **every** candidate, export:

```sh
python3 -m veka efficiency-review-check \
  --candidates /private/ind-candidate.csv \
  --review-a /private/ind-A.csv \
  --review-b /private/ind-B.csv \
  --output /private/ind-reviewed.json
```

The result is a **noncanonical research manifest**, not a certification.
Missing/uncertain, conflicting, or negative judgments block export.
Reviewers cannot silently substitute another candidate, even if both changed
to the same text. Already-existing output files cannot be overwritten.

If a reviewer rejects an item, arrange a *new* candidate-revision round with
independent checks, preserving the old candidate and verdicts. Never rewrite
previous judgments to pretend they agreed. If the original editorial meaning
is disputed, stop and independently adjudicate the intended Veka meaning
*before* translating it: changing the frozen baseline is a distinct corpus
revision requiring a new version.

## 4. Measure real comprehension separately

Only after acceptable meaning-matched stimuli are independently reviewed
should a properly preregistered reading or listening experiment begin.
Use separate testing of speech production/pronunciation, balanced participants
by first language, comparable training and task conditions, blind judges and
consequential-error noninferiority checks. Count all repair time and incorrect
responses when calculating correctly recovered meanings per elapsed minute.

No candidate text, reviewer verdict, participant outcome or timing measurement
was generated as a real observation by this implementation. Examples in the
automated tests are synthetically labeled and are **not research evidence**.
