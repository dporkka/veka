# Veka v0.12 — cross-language borrowing research (noncanonical)

**Status:** Seven English-language *meaning-contrast hypotheses* and an
observational conversation scorer. Neither establishes a new Veka vocabulary,
pronunciation, syntactic register, valid translation, or human comprehension.
Canonical 0.4 vocabulary and 0.3 grammar remain frozen.

## Commands

```sh
python3 -m veka borrowing-audit
python3 -m veka borrowing-audit --catalog data/language_transfer_v01.json --output /tmp/veka-borrowing-audit.json
python3 -m veka conversation-score
python3 -m veka conversation-score --trials /secure/actual-conversation-results.csv --output /secure/descriptive-results.json
```

`data/language_transfer_v01.json` holds research hypotheses drawn from
Globasa, Indonesian, Quechua, Tagalog/Tamil, Turkish, Japanese, creoles, and
Hawaiian. The source-language names express design inspiration, **not**
linguistic evidence that Veka implements the features or that the proposed
study items have equivalent translations. Each proposal has two or more
English meaning contrasts, relevant IDs in the existing 100-scenario everyday
corpus, explicit risks, and a human-testing gate. The tool validates the
catalog against the frozen dialogue scenario identifiers and rejects unknown
fields, duplicate proposals, missing contrasts and attempted approvals.

The existing `international-plan` and `lexical-readiness` commands remain the
source of truth for *word-specific* research. This catalog does not provide
any donor-word attestation or change the 100-concept queue. To study a word,
first verify multilingual donor forms and independent families; then test
recognition and production against canonical roots. Do not treat repeated
borrowings from the same origin as independently evolved cognates.

## Human dialogue benchmark

The optional `data/conversation_trials_v01.csv` is **header only**. Rows must
come from actual, consented and independently recorded or administered
language tasks. The exact schema is:

```csv
participant_id,background_family,scenario_id,language,correct,elapsed_ms,repair_ms,critical_error
```

- `scenario_id`: a frozen `ED-001`..`ED-100` requirement identifier. Each
  participant may see that semantic scenario **only once**, to reduce
  cross-condition memorization and leakage.
- `language`: `veka`, `globasa`, `esperanto`, `interlingua`, or `indonesian`.
  These conditions can only be evaluated after independent native/competent
  translation review, stimulus matching, and comparable teaching/exposure.
- `participant_id`: pseudonym of 2–64 ASCII letters, digits, underscores or
  dashes; never store names, emails, IP addresses or other identifying data.
  `background_family` is a reviewer-provided label, not a validated ancestry
  or aptitude measurement. A participant has one consistent label.
- `correct`, `critical_error`: independently adjudicated `0` or `1`, never
  both `1`. Define correctness, critical-error severity and adjudication
  disputes *before* collecting outcomes.
- `elapsed_ms`: positive integer; `repair_ms`: nonnegative integer. Record
  actual response time and additional clarification/repair time separately;
  never guess or use a synthetically calculated duration.

The scorer reports successful meanings per **total observed minute**,
including repair time, along with critical errors, sample counts, and family
strata. A `balanced_scenario_family_cells` count indicates cells with Veka and
at least one comparator; it does **not** imply equivalent participants,
matched item counts, randomized conditions, adequate power, or statistical
balance. No outcome can automatically authorize a change or declare a winner.

### Preregister before data collection

1. Recruit real learners from multiple language families with a documented
   exposure and proficiency profile; do not substitute simulated participants.
2. Independently prepare and blind-review pragmatically equivalent dialogue
   prompts and translations for each study condition, and verify that the
   intended meaning and speech acts match. Record speaker and recording
   provenance outside the public CSV.
3. Block and counterbalance scenario assignment across language-background
   groups and conditions; use independent utterance recordings and separate
   previously unseen validation sentences. Handle missing data explicitly.
4. Prespecify correct-message and critical-error definitions, adjudication,
   timing boundaries, repair behavior, exclusion criteria and an error-rate
   noninferiority margin. Compare first-sight recognition, trained retention,
   spoken-in-noise comprehension and spontaneous dialogue separately.
5. Analyze uncertainty with appropriate paired/blocked inference external to
   this descriptive CLI. Inspect per-family effect heterogeneity, repeated
   participant structure, potential training bias and translation quality.
6. Only propose a *versioned opt-in* grammar or lexicon change after real
   human evidence demonstrates reduced total time per correctly communicated
   meaning **without** a meaningful critical-error increase; an inconclusive
   result means retaining the canonical implementation.

**Known limitations:** No recordings, verified translations, recruitment,
participant outcomes, or adoption decision are included. The benchmark
cannot prove language-level effectiveness, and its labels are not empirical
validation. Results are for research triage, not safety-critical messages.
