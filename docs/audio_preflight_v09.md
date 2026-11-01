# Veka 0.9 — read-only ABX PCM preflight

**Status:** supplementary recording hygiene tooling; **not** a canonical
language change, an acoustic model, an empirically validated threshold, or
evidence of any recorded human Veka speech.

## Why

The Veka 0.6 ABX score command checks the manifest, WAV metadata, and
byte-for-byte file identity. Those checks cannot tell whether a recording is
silent, audibly distorted, incorrectly pronounced, a copied waveform with
different WAV metadata, or genuinely a separate human take.

The new command provides additional signal-level diagnostics **before** a
researcher manually audits recordings. It makes no participant-facing study
files and does not write to the recording directory.

## Workflow

1. Generate the researcher-only manifest with `listening-plan` per
   [ABX study protocol](abx_protocol_v06.md).
2. Have trained, consenting speakers record all A/B/X takes independently.
   Maintain provenance and audible validation notes outside version control.
3. Mark `recorded=yes` **only after** externally verifying each file and
   reviewing its documented provenance. The preflight does not change these flags.
4. From the repository root, run:

   ```sh
   python -m veka listening-preflight \
     --recording-csv /secure/recording_jobs.csv \
     --audio-root /secure/actual-wavs > /secure/preflight.json
   ```

5. Inspect `clips[].warnings`; personally listen to every clip, including
   those without warnings. Investigate every warning and document justified
   decisions. Verify transcript, pronunciation, talker, independent takes,
   microphone calibration, and external SNR preparation.
6. Only then proceed to independently collected listener responses and
   `listening-score`. This tool does **not** replace the existing scorer.

This command accepts **complete** confirmed ABX banks, not in-progress
recordings, and exits with an error if files/manifest are missing or structurally
invalid. The JSON report is diagnostic, not a study outcome.

## Transparent diagnostics

- PCM decoding supports 8-bit unsigned and 16/24/32-bit signed little-endian
  WAV, mono or stereo. Samples across channels contribute to scalar metrics.
- `rms_dbfs`: root mean square relative to digital full scale.
- `near_silence`: RMS below -45 dBFS.
- `possible_clipping`: at least 1% of samples reach absolute normalized
  amplitude 0.995.
- `large_dc_offset`: absolute sample mean at least 0.1 full scale.
- PCM content is hashed separately from the entire WAV file, to detect
  exact reused sample data despite different container metadata. It **cannot**
  detect copied audio that has been requantized, normalized, trimmed,
  resampled, denoised or remixed.

These numerical thresholds are **arbitrary screening heuristics**, not
prespecified eligibility criteria or guaranteed speech-quality standards.
For example, a quiet recording may have low RMS yet contain intelligible
speech; clipped samples might be legitimate transients; absence of detected
clipping does not mean absence of distortion. Stereo levels are pooled:
separate channel checks may be necessary. No per-phoneme analysis, voice
activity detection, intelligibility rating, pitch validation, independent
take authentication, background noise calibration, or SNR measurement is done.

The report explicitly includes `human_speech_verified=false`,
`snr_verified=false`, `pronunciation_verified=false`,
`independent_takes_verified=false`, and `manual_review_required=true`.
Even `review_count=0` does not mean the recordings are correct or usable.

## Safety, integrity and reproducibility

Use pseudonymous talker codes. Keep real voice audio and consent records
outside the repository, in access-controlled storage. Do not use a preflight
report as a proxy for actual listening-study observations. Capture the
recording hardware, environment, independent take IDs, processing chain,
quality-control adjudication, and noise calibration independently.

Unit tests generate synthetic sample arrays to test file parsing and
numerical calculations. They contain **no speech or human participant data**.
Run `python -m unittest discover -s tests -p 'test_audio_preflight_v09.py' -v`
for focused tests and `make validate` for the full project contract.
