# VEKA 0.4 candidate — experimental high-reliability constructed language

**Release candidate:** 1 November 2026  
**Status:** executable, machine-tested limited language prototype — **not empirically validated**.  
**Licensing:** No distribution license has been selected for this prototype. Third-party cited research retains its publishers' terms.

## Design objective

Veka tries to minimize **total time to correctly understood meaning**, including teaching, speaking, misunderstanding and repair. It combines short syllables, highly regular grammar, fully scoped logic, exact decimal numerals, an experimental Hangul-like featural writing system, and conservative context-based omission. None of these choices have yet been shown to outperform natural languages in human trials.

The preserved 0.3 baseline focuses on: (1) transparent numbers and units, (2) logical scope without precedence ambiguity, (3) a sound-confusion audit and tone-free test condition, and (4) randomized, reproducible *human listening study materials*. It does not synthesize convincing Veka speech or fabricate test participants.

## 0.4 experimental profile (new)

This candidate adds an **opt-in toneless lexicon** preserving the original 1,025 meanings, parts of speech, and valency. Canonical 0.3 tonal forms remain the default. The toneless vocabulary is **not** empirically proven superior: its structural near-pair count rises from 2,262 to 2,320. See [`docs/design_review_v04.md`](docs/design_review_v04.md) for the review, compatibility rules, known tradeoffs, and human go/no-go criteria.

```sh
python -m veka profile tonal
python -m veka profile toneless
python -m veka parse 'Mi fok mel.' --profile toneless
python -m veka parse 'Mi pái mel.' --profile tonal
python -m veka convert 'Mi pái mel.' --target toneless
python -m veka audit --profile toneless --top 5
```

0.4 also tightens punctuation validation, bounds recursive possessions and verifies participant/item condition uniqueness in listening-study input. **No speaker/listener recordings or experiment outcomes have been created.**

## Experimental 0.5 grammar extensions (opt-in)

The reference extension now implements six regular event-derivational suffixes, a 4×6 correlative matrix, and bounded relative/propositional complements without altering the 1,025 canonical headwords. It adds `python -m veka extend`, `derive`, and `correlative` commands; the original `parse` behavior and tonal/toneless profiles remain the baseline. **No spoken-comprehension or speed advantage has been measured.**

```sh
python -m veka extend 'Ren ri wek dak mel yu pa gos.'
python -m veka extend 'Mi sen ka ti ton mel yu.'
python -m veka derive dak-nes
python -m veka correlative hon-ren
```

See [Veka 0.5 grammar specification](docs/grammar_v05.md) for restrictions, semantic interpretation, and compatibility guarantees.

## Quick start (Python 3.10+, zero third-party dependencies)

From the directory containing `README.md`:

```sh
python -m unittest discover -s tests -v
python -m veka number spell '120.05'
python -m veka number read 'wen ran kuk nul dis nul gel'
python -m veka parse 'Mi fu dak mel to ti sun.'
python -m veka parse 'Mi rin sil wen ran dis gel su wok.'
python -m veka parse 'Al ren pa gos.' --strict
python -m veka logic 'Fi mi dak mel ve ti ton mel yu.'
python -m veka logic 'Na zi mi gos ve ti gos yu yu.'
python -m veka lookup 'message'
python -m veka check 'pál'
python -m veka render 'mi dak mel' --output my_script.svg
python -m veka audit --top 8 --output my_audit.json
python -m veka benchmark
python -m veka study-assign --participant P001 --output my_manifest.csv
python -m veka score collected_trials.csv  # Only after real human data exist
```

**All tools operate locally.** The CSV trial template is deliberately blank. The `score` command does not invent results.

## Core spoken vocabulary

| Veka | English | Notes |
|---|---|---|
| `mi`, `ti`, `ni` | I, you, we | Separate pronouns; must be intelligible in noise |
| `dak`, `ton`, `gos` | send, receive, go | Regular predicates |
| `mel`, `ren`, `sil` | message, person, water | Noun roots |
| `pa`, `fu`, `ne` | past, future, negation | Fixed grammar particles |
| `al`, `kis` | every, some | At most one quantified noun phrase per atomic clause |
| `wen`, `dis`, `sin` | exact-number marker, decimal separator, minus | Decimal digits spoken individually |
| `zi`, `oi`, `fi`, `na` | AND, OR, IF, NOT | Fully bracketed logic only |
| `ve`, `yu` | operand separator, scope end | Mandatory for logic |
| `rel`, `sek`, `vos`, `wok` | meter, second, kilogram, liter | Standard quantity unit names |

Examples:

- `Mi pa dak mel.` = I sent a message.
- `Mi rin sil wen ran dis gel su wok.` = I need 1.5 liters of water.
- `Al ren pa gos.` = Every person went.
- `Na zi mi gos ve ti gos yu yu.` = NOT (I go AND you go).
- `Fi mi dak mel ve ti ton mel yu.` = If I send a message, then you receive it, as a *material implication*. It does not encode real-world causation.

For complete grammar and numeric digit table see **[`docs/grammar_v03.md`](docs/grammar_v03.md)**. The reference parser accepts a bounded single-clause subset; grammar specifications are not claims of complete syntax.

## Deliverables

| File | Purpose |
|---|---|
| `data/lexicon.csv` | 1,025 unique lexicon entries = 317 roots + 708 transparent noun compounds; includes all 1,000 unchanged v0.2 entries |
| `build_lexicon.py` | Deterministically rebuild the lexicon, appending rather than reassigning the original words |
| `veka/core.py` | Phonology validator, conservative clause parser, SVG writer, baseline scoring |
| `veka/numbers.py` | Lossless canonical spoken decimal encoding/decoding |
| `veka/logic.py` | Explicitly bracketed propositional expressions, AST + truth evaluation |
| `veka/phonology.py` | Structural minimal-pair and numeral-codeword audit; **not** an acoustic predictor |
| `veka/study.py` | Participant counterbalancing and ABX assignment generation |
| `docs/grammar_v03.md` | Formal written/speech rules and defined semantics |
| `docs/phonology_v03.md` | Phonological risks, evidence references, alternate toneless inventory |
| `docs/listening_protocol_v03.md` | Recording protocol, comprehension study, ABX tasks, preregistration checklist |
| `data/study_items_v03.json` | 32 communication items: 24 compressible examples + 8 honest uncompressible controls |
| `data/phonology_abx_pairs.json` | 7 ABX contrast pairs including tone, pronouns, negation and coda perception |
| `data/sample_manifest_p001.csv` | Counterbalanced randomized study manifest for fictional participant ID P001; no recordings |
| `data/sample_abx_manifest_p001.csv` | Recording manifest for 28 ABX trials; no recordings |
| `data/phonology_audit.json` | Full lexical pair audit, labeled as nonempirical |
| `data/tone_free_ablation.csv` | Four alternative candidate words to compare against tonal forms; not canonical |
| `data/profile_pairs_v04.json` | Eight constructed profile-matched semantic checks, **not audio or listener data** |
| `tests/test_v03.py` | 0.3 behavior and regression tests |
| `veka/profiles.py` | 0.4 opt-in lexical profile loader and token converter |
| `tests/test_v04.py` | 0.4 profile, CLI and fail-closed regression tests |
| `docs/design_review_v04.md` | 0.4 architecture review, tradeoffs, experimental release gates |
| `docs/veka_script_v0_1.svg` | Original hand-designed syllable-block writing prototype |

## Important numeric facts

- The validator permits **932 theoretical monosyllabic forms** under its restrictions: **556 level-tone forms and 376 rising-tone forms**. These are *distinct spellings/abstract phonological forms*, not 932 equally intelligible choices.
- Only **4 of 317 primitive roots use rising tone**. Therefore a toneless alternative is scientifically worth testing before committing to tone as a permanent feature.
- The audit finds **2,262 structural one-feature minimal pairs** among 303 nonnumeric, nonunit roots; these are *surface-form pair counts*, not measured human confusion rates.
- In the preserved 24 deliberately compressible structural examples, explicit and compact clauses still parse to the same role representation (108 vs 65 syllables). The **39.8% reduction is constructed**, not actual time savings or information rate.
- Exactly 10 numeral words are at least two simple string edits apart from each other and designated grammar operators. This is a coding heuristic, not a claim of robust acoustic separation.

## How to conduct the next actual experiment

1. Read `docs/listening_protocol_v03.md` and preregister criteria, participant recruitment and analysis.
2. Generate manifest CSVs for pseudonymous listeners. Record all stimuli with **human speakers** independently, including A/B/X separate productions, and normalize playback level.
3. Teach participants to a predefined criterion; perform the comprehension and ABX tasks. Collect data, elapsed times, repairs and answer correctness.
4. Score with `python -m veka score ...` and analyze participant-paired uncertainty. Report each critical meaning error and avoid interpreting edit distance as listening success.
5. Keep tone only if it demonstrates worthwhile performance under controlled learning and speech conditions.

## Boundaries

No text-to-speech, native input method, voice data, human comprehension measurements, full first-order quantifier binding, language-wide semantic inference, or real-world safety validation is included. The script is scalable SVG art, not a published font or Unicode writing system. Do not use the prototype to carry actual safety-critical instructions.


## Interlingua-inspired vocabulary research (parallel Veka 0.4 experiment)

The optional `veka/international.py` tooling explores recognizable technical vocabulary
without changing the canonical Veka 0.3 lexicon or the separate tonal/toneless profiles.
The 100-concept queue includes eight illustrative **unverified** candidate spellings;
none is accepted by the parser, and no human recognition benefit is claimed.

```sh
python make_international_v04.py
python -m veka international-audit --output pilot_audit.json
python -m veka international-family --noun ren --adjective sak
python -m veka international-manifest --participant P001 --output blind.csv --answer-key key.csv
```

See [the international vocabulary pilot protocol](docs/international_v04.md).
