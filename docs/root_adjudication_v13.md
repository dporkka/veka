# Veka v1.3: adjudicating the international-root first-sight pilot

This adds a **manual, condition-blind scoring bridge** to the already existing
v1.2 eight-root study. It makes no changes to accepted vocabulary, grammar,
lexical aliases, phonotactics or semantic identifiers. It is not an automatic
root-selection or word-recognition model.

## Process

1. Run `root-study-plan` as documented in
   [the v1.2 protocol](root_sources_and_study_v12.md), using an independently
   recruited, consented pseudonymous and language-stratified cohort.
2. Collect the returned `<participant_id>.csv` sheets securely. Each planned
   row must have a genuine `response_gloss`, a positive `response_ms` and
   `prior_exposure` set to `yes`, `no` or `unknown`. Do not fill these using
   the reference answer, automatic translation, or invented example data.
3. Generate a **private, initially unscored** review CSV:

   ```sh
   python3 -m veka root-study-review \
     --key /private/researcher-keys/researcher-key.csv \
     --responses-dir /private/returned-responses \
     --output /private/root-review.csv
   ```

4. Give reviewers only the review CSV, **not** the key or participant sheets.
   It contains `participant_id,trial_id,target_gloss,response_gloss,correct,
   critical_error,reviewer_id,review_note`; it deliberately hides the displayed
   form, experimental condition, language-background field and response time.
   Use opaque participant IDs that do not encode the language stratum. Decide
   acceptable senses and critical errors in a preregistered rubric. Reviewers
   manually enter `0`/`1` judgments and an identifier and rationale in each row.
   For contested meanings, resolve disagreements with a separate documented
   adjudication procedure outside this tool. Reviewer independence and true
   blindness cannot be verified by software.
5. Produce **descriptive** cross-language results:

   ```sh
   python3 -m veka root-study-score \
     --key /private/researcher-keys/researcher-key.csv \
     --responses-dir /private/returned-responses \
     --reviews /private/root-review.csv
   ```

   The output contains counts, correctness, critical meaning errors, declared
   prior exposure and mean written first-sight response milliseconds, aggregated
   by condition, language-background stratum, concept, and concept × background.
   There are no response glosses or participant pseudonyms in the summary.

## Fail-closed constraints and limitations

- Reject malformed CSV headers, missing/duplicate/unknown trial IDs, altered
  written forms, contradictory target meanings, mismatched original responses,
  inconsistent participant assignments and incomplete judgments.
- Require the full complementary language-background × concept allocation from
  the blinded root study; no silent cherry-picking of only scored responses.
- Reject response cells that begin with spreadsheet formula prefixes or contain
  control characters, to avoid formula execution when the CSV is opened in a
  spreadsheet.
- Create new review sheets only, with owner-only POSIX permissions; never
  overwrite a sheet. Keep raw responses, keys and reviews private.
- `prior_exposure=yes` may confound an apparent first-sight advantage. The
  tool reports such counts; it does not automatically exclude people or select
  a convenient subgroup. Exclusions must be registered **before** the study.
- The program does **not** authenticate human identity, source language,
  recruitment, consent, independent review, semantic correctness, timing,
  pronunciation, listening in noise, or delayed recall. Even manually scored
  observations cannot establish a causal gain without sufficient sample size,
  balanced, prespecified comparisons and uncertainty analysis.
- The CLI uses the existing 8-form `international_candidates_v04.csv` packet;
  the separate familiar-vocabulary profile is not silently substituted.
- `adoption_authorized` and `comparative_benefit_established` are always
  `false`. Further cross-family evidence, speaking/listening and retention
  outcomes, and explicit versioned migration review are required before any
  canonical word changes.

Test with:

```sh
python3 -m unittest discover -s tests -p test_root_adjudication_v13.py -v
make validate
```
