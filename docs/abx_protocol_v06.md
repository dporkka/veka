# Veka 0.6 — preregistered ABX listening pilot

**Status (2026-11-01):** reproducible stimulus and scoring infrastructure, **no real recordings or human responses have been collected**. The implementation does not change canonical Veka. The phonological risk scores in [lexical_design_v05.md](lexical_design_v05.md) are symbolic hypotheses, **not** measured confusion rates. This protocol tests phonetic discriminability, **not** language-wide communication superiority.

## Experiment questions and limitations

The ABX question: after listening to two independent productions A and B of different words, can a listener decide whether an **independently recorded** X token matches the phonological category of A or B? A/B position and X identity are balanced in each contrast/talker/condition block.

- Primary descriptive endpoint: **correct ABX identification** by contrast, listening condition and talker. Measure actual response times and repeated listening/repairs separately in the human study.
- Critical contrasts: `mi/ni`, `mi/ti`, `ne/no`, `fu/du`, `ke/ne`, `en/es`, `to/ton`, `ran/ren`, `sok/sak`, `gel/gal`. These choices are hypotheses generated from symbolic distance and meaning consequence, not proven hazardous pairs.
- Exploratory contrasts: `pal/pál` (tonal-only), `ba/bal`, `bel/bes`. The toneless profile skips `pal/pál` because `pál` is not one of its words.
- All source forms are existing valid Veka roots. No draft replacement syllables are introduced or promoted into canonical Veka.
- ABX discrimination alone says nothing about lexical memorization, meaning interpretation, conversational repairs, speaking speed, practical grammar or superiority to existing languages. Follow it with **full-utterance comprehension and repair studies** (the v0.3 protocol contains experimental stimulus ideas).

## 1. Generate a sealed study packet

From the repository root, using Python 3.10+ and no dependencies beyond the standard library:

```bash
python -m unittest discover -s tests -v
mkdir -p /tmp/veka-study-p001
python -m veka listening-plan \
  --participant P001 --arm 0 --profile tonal \
  --talker S01 --talker S02 \
  --participant-csv /tmp/veka-study-p001/participant.csv \
  --key-csv /tmp/veka-study-p001/researcher_key.csv \
  --recording-csv /tmp/veka-study-p001/recording_jobs.csv
```

Allocate **arm 0 or 1 through external randomized enrollment**, counterbalanced within language backgrounds, never from the participant's name, demographics or self-selection. The explicit `--seed` controls trial order; the default is stable. Only use pseudonymous participant IDs. Restrict access to `researcher_key.csv` and `recording_jobs.csv`. Do not publish, email, or display them to participants. The participant file contains only opaque clip IDs, blank responses and blank elapsed times: it does not disclose words, answers, speaker IDs or quiet/noise condition labels.

For the 13-contrast **tonal** profile with **two** talkers there are 104 ABX decisions and 312 *independent A/B/X WAV recording jobs per arm*. The **toneless** profile has 12 contrasts, 96 decisions and 288 recording jobs per arm. With one talker, these counts halve.

The clip name includes a short SHA-256 **namespace fingerprint** derived from the exact frozen contrast definitions, talkers, chosen profile and arm. That keeps different stimulus banks from silently reusing filenames. Within a bank, clip IDs remain stable when a new listener ID or trial-order seed is supplied. **Record each bank once and reuse its fixed assets across participants assigned to that same arm**, rather than recording hundreds of new files for every participant. A changed contrast list/order, talker set, profile or arm requires a different bank. Do not edit the contrast file after recruiting participants.

## 2. Record original human speech

Use trained human speakers from more than one language background, with explicit informed consent and documented session IDs. For each row in `recording_jobs.csv`, record the specified word and **create a separate take for each A/B/X job**. Never copy a source waveform to stand in for another take. Save the actual WAV at the opaque path `audio_root/<audio_id>`, retaining the original generated filename.

- Record in consistent conditions with calibrated microphones and playback level. Use a common uncompressed PCM WAV format (e.g. mono, 16-bit, 48 kHz); the validator accepts 8–192 kHz, 1–2 channels and 0.10–30 seconds, and refuses duplicate identical file bytes.
- For `quiet`, use uncluttered listening audio. For `noise_plus5db`, **externally produce and calibrate a +5 dB signal-to-noise-ratio condition**, keeping tone information intact; record the mixing method, signal/noise definitions, hardware and calibration. The software **does not generate noise, measure SNR or verify voice quality**. Its condition labels are planned assignments, not acoustic evidence.
- Control timing, loudness and recording distance. Include separate independent productions of A, B and X even when X has the same underlying word as A or B. The scorer validates that no two WAV files have identical SHA-256 bytes; this does not guarantee independently produced human speech.
- Update `recorded` from `no` to `yes` in the restricted recording manifest **only when the actual WAV exists, was auditioned by an authorized researcher and the provenance log is complete**. File verification does not establish these human conditions.

Capture additional external metadata: consent, the trained speech category, recording date, talker's background, accent, volume normalization, noise calibration, and exclusions. Do not place identifiable speaker or listener data in version control.

### Optional PCM preflight before manual review

After all WAVs exist and recording-job flags have been marked `yes` by an
authorized researcher, run `python -m veka listening-preflight
--recording-csv /secure/recording_jobs.csv --audio-root /secure/actual-wavs`
to find candidate silence/clipping/DC-offset issues, truncated data, and
identical PCM hidden by different container bytes. This command does not
modify WAVs or classify a recording as genuine speech. Even a warning-free
report requires manual audition, independent-take provenance, pronunciation
checks and external SNR calibration; see
[audio preflight protocol](audio_preflight_v09.md).

## 3. Present the trials and capture real responses

Pre-register recruitment criteria, learning-to-criterion requirements, number of listeners, power/sample-size rationale, time cap per trial, critical-error policy, subgroup plan, randomized allocation, and the exact comparison tests **before seeing outcomes**. Enroll multiple independent speakers and listeners; keep the researcher key inaccessible to the person running the participant interface.

Play A, B and X WAVs in order using the participant sheet. Ask whether X matches A or B. Let the participant indicate `A` or `B`; record the complete time from first audio onset to committed answer as a positive `elapsed_ms` (maximum 600000). Record any repeats, equipment failures, language background and individual session exclusions in separately safeguarded records. The current CSV format does **not** encode repeats, equipment status, confidence or training time; capture them in the experiment's preregistered observation log.

The response CSV must be the same participant-sheet schema, with exactly one completed row per trial. **Never substitute invented participant responses to create an apparent success rate.** Unit tests use synthetic WAVs and synthetic response rows exclusively to verify software behavior; these are not research data.

## 4. Score only a complete, recorded packet

```bash
python -m veka listening-score \
  --key-csv /tmp/veka-study-p001/researcher_key.csv \
  --responses-csv /path/to/p001-completed-responses.csv \
  --recording-csv /tmp/veka-study-p001/recording_jobs.csv \
  --audio-root /path/to/actual-wav-clips
```

Scoring fails closed on missing responses, duplicate trial IDs, invalid answer values/times, altered key/participant metadata, inconsistent target balancing, absent/unconfirmed WAVs, WAVs outside the recording directory through symlinks, implausible WAV metadata, and byte-identical reused audio.

Reports show descriptive accuracy, correct ABX decisions/minute (including failed-trial elapsed time), quiet/noise breakdown, per-contrast A/B-position confusion, per-talker summaries and counts of critical errors. **Correct ABX decisions/minute is not real-world correctly communicated messages/minute.** The software does not calculate statistically defensible population effect sizes or participant-clustered confidence intervals. It deliberately reports `human_authenticity_verified=false`, `snr_verified=false`, and `population_effect_estimated=false` even when fed valid WAVs and completed rows.

## 5. Falsifiable decision rules

The existing [listening_protocol_v03.md](listening_protocol_v03.md) proposes **tentative**, not scientifically certified, 90% held-out training-to-criterion understanding and a 95% quiet-listening accuracy design target for essential contrasts. Decide exact thresholds, uncertainty criteria, sample size and consequences of critical failures **before** collecting outcome data. A few successful ABX trials, especially with repeated listener/item measurements, cannot establish a population error bound.

- Require enough independently sampled *listeners and talkers* to estimate uncertainty; report participant-level and item/talker-level variation rather than treating all repetitions as independent observations.
- Compare quiet against properly calibrated noise; examine whether high-priority negation, reference, number and scope markers behave differently across language groups.
- Reject or redesign any critical contrast that reproducibly fails the prespecified thresholds. Do not rename all roots on the basis of symbolic distance.
- Run a separate, adequately controlled **meaning-recovery experiment** with isolated candidate lexical profiles and complete utterances before adopting any new words. It must measure learning cost, correct meaning, response time and repairs against the original Veka baseline.
- If the study is inconclusive, **keep the existing Veka vocabulary and grammar unchanged**.

## Privacy and integrity

Recruit consenting adult volunteers; use pseudonymous IDs and separate sensitive consent and recorded speech from participant-facing CSVs. Do not put identifiable participants, researcher keys, phonetic recordings or response datasets in the Git repository. Establish retention/deletion and participant withdrawal procedures; encrypt or access-control storage. Do not use this prototype for actual safety-critical communication.

There are **no participant observations or audio files** in this release. The presence of a plan and a scorer is not evidence that Veka has improved human communication.
