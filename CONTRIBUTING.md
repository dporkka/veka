# Contributing to Veka

Veka remains an **experimental** human-language research project, not a proven optimal language.

- Run `make test` (or `python -m unittest discover -s tests -v`) before proposing changes.
- Preserve the established Veka 0.3 grammar, existing roots, and lexicon unless an explicit versioned migration has been discussed.
- New international vocabulary is experimental. Candidate spellings require provenance, collision review, and human-study evidence before canonization.
- Do not insert invented response measurements, unverified cross-linguistic cognate claims, or purported listening-study outcomes.
- Include a minimal, reproducible test for any parser or validator change.
- Treat `data/lexical_priors_v05.csv` as declared assumptions, not observed frequency or error data. Do not adopt candidate root replacements without independently collected audio/comprehension evidence and a migration plan.
- Existing noun–adjective compounds have a silent hyphen. Do not claim these encode audible distinctions from corresponding noun–adjective phrases without a separately specified phonological mechanism.
- Keep ABX answer keys, raw recordings, private participant responses and personally identifying study files OUT of git. Only participant-agnostic templates, contrast lists, fake unit-test waveforms and protocol documentation belong here.
- All `noise_plus5db` labels are proposed playback conditions, not calibrated evidence. Humans must record independent A/B/X takes and externally verify sound and SNR before conducting any study.
- There is currently no explicit open-source license. Do not assume permission to redistribute third-party contributions under a particular license.
