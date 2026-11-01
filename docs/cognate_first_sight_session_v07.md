# Veka v0.7: blinded first-sight comprehension session

**Status:** local research instrument only; no participant data have been collected, no language-level gains demonstrated, no vocabulary adopted. This study tool extends the [18-item cognate pilot](cognate_pilot_v07.md) and [12 unverified dictionary leads](cognate_source_review_v07.md). It does not alter the canonical lexicon.

## Researcher setup

Use Python 3.10+ with no third-party dependencies, from the Veka repository root. Use separate participant pseudonyms, separate file paths, and secure storage.

```sh
mkdir -p /tmp/veka-pilot
python -m veka cognate-manifest --participant P001 --arm 0 \
  --output /tmp/veka-pilot/p001-manifest.csv \
  --answer-key /tmp/veka-pilot/p001-SECRET.csv
python -m veka cognate-session \
  --manifest /tmp/veka-pilot/p001-manifest.csv \
  --output /tmp/veka-pilot/p001-session.json
```

Only give the participant **`p001-session.json`**, not the original researcher key, and not an adjudication sheet. The JSON has only an anonymous participant ID and 18 sequential `trial_id` + `presented_form` pairs. `cognate-session` rejects extra answer columns, already-completed responses, duplicated/invalid trials, and overwrites.

The participant opens `site/cognate-study.html` in Firefox/Chrome (direct local `file://` is supported), selects their assigned JSON, enters a self-reported first language (and optional language family), accepts the volunteer study prompt, and completes all 18 forms. There are no definitions or translations on the study screen. They may type “don't know.” Afterward they download an **unscored participant response CSV** and provide it to the researcher separately, if they choose.

**Nothing is transmitted to a server or persisted by the page.** If the page is refreshed or closed before download, its results disappear. This prototype does not establish a study's legal/ethical consent process; researchers must review their jurisdiction, recruitment, data minimization, privacy requirements, and any required human-subject review.

## Researcher judgment and scoring

The raw CSV preserves the trial ID, stimulus, free-text response, elapsed milliseconds, self-reported prior exposure, first language, optional self-reported family, and whether timing was interrupted by browser focus loss. Do not assume a participant's self-reported family label is genealogically correct.

```sh
python -m veka cognate-judge-sheet \
  --answer-key /tmp/veka-pilot/p001-SECRET.csv \
  --responses /path/to/participant-downloaded-responses.csv \
  --output /tmp/veka-pilot/p001-private-judge.csv
```

This command validates all 18 IDs, participant identity, and exact stimuli against the separate researcher key. It creates a **private researcher-only** sheet showing target and supplied meanings without experimental condition labels, leaving `correct` and `repair_count` blank. There is no automated scoring or invented participant result.

An independent bilingual reviewer must assign `correct=1` or `0` based on a preregistered acceptable-synonym rubric; fill `repair_count=0` when no repairs were allowed and observed; document ambiguous judgments separately. Prefer two blinded judges and adjudicate disagreements. Then:

```sh
python -m veka cognate-score \
  --answer-key /tmp/veka-pilot/p001-SECRET.csv \
  --annotated /tmp/veka-pilot/p001-private-judge.csv
```

The current scorer returns **descriptive** counts, response times, and accuracy by candidate/control conditions. It does not verify genuine humans, infer causal effects, compute statistically justified superiority, or declare vocabulary accepted. Never share the private judge sheet or answer key with participants. Be careful when opening volunteer-supplied CSV in spreadsheet software: CSV cells can contain untrusted user text. The browser prefixes a literal apostrophe to exported cells starting with spreadsheet formula characters, which preserves their visible meaning but means a leading apostrophe is added to those responses; preserve the original raw study context when adjudicating.

## Preregister before collecting real participants

- **Endpoint:** correct first-sight identification, elapsed time, prior exposure, and unanswered/“don't know” rate per condition. Separately estimate retention and spoken recognition; reading-only success is not speech evidence.
- **Recruitment:** represent *unrelated* genealogical families and mixed multilingual backgrounds, not just English, French, Spanish, and Portuguese (all Indo-European). Record actual languages, education, and prior exposure without inferring identity-sensitive traits.
- **Assignment:** randomly assign complementary `--arm 0`/`--arm 1` *within each recruited group*; use new IDs for every participant. Each participant sees each concept once. Preserve the independent researcher key.
- **Bias checks:** borrowed terms across different families may share a single European borrowing path. Compare results within family and by actual exposure. Evaluate mismatches such as Veka `ro-bo` versus `robotto` / `roboti`; consider known false friends such as Portuguese `data` (“calendar date”).
- **Exclusion:** define noncompliance, missing records, focus interruptions, bilingual prior knowledge, use of lookup tools, and extreme response times in advance. Do not silently remove slow or unsuccessful trials.
- **Analysis:** estimate accuracy differences with uncertainty by participant and item, explicitly distinguish new-concept nonce controls from replacement core roots, and report family-specific variation. The bundled scorer is not an inferential model.
- **Decision:** no canonical vocabulary promotion without independent semantic source review, sufficient human study evidence, acceptable critical error rates, and a net improvement in total correct communication time.

## Timing limitations and browser smoke

The page records durations with `performance.now()` from displayed stimulus until form submission and marks a focus interruption; this is **not calibrated psychophysics timing**. Browser/device differences can bias direct between-person timing comparisons, so prioritize correct answers and design within-device controls. See [Bridges et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7512138/) and [Anwyl-Irvine et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8367876/).

The local Firefox smoke test verified: loading a participant-only JSON, all 18 word responses, final completion screen, CSV export with exactly 18 rows, no answer-key leakage, and no page JavaScript errors. **These were automated synthetic interactions, not real participants.**

## Re-run validation

```sh
python -m unittest discover -s tests -p 'test_cognate_session_v07.py' -v
python -m unittest discover -s tests -p 'test_cognate_judging_v07.py' -v
make validate
```
