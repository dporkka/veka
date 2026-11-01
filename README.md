# VEKA — experimental high-reliability constructed language

**Release candidate:** 1 November 2026  
**Status:** executable, machine-tested limited language prototype — **not empirically validated**.  
**Licensing:** No distribution license has been selected for this prototype. Third-party cited research retains its publishers' terms.

**Specification status:** Canonical 0.4 lexicon and 0.3 grammar are frozen by
`data/canonical_contract_v06.json`; 0.5 grammar, 0.6 discourse, and lexical research remain
opt-in. See [Veka 0.6 specification and transparent-compound policy](docs/specification_status_v06.md)
and the [proposed Veka-T technical register](docs/technical_profile_v06.md).

`make validate` runs the local contract suite and research audits. The existing
`.github/workflows/python-contract.yml` requests exact-head hosted
regression validation for PRs and `main`; check real run results.

## Core / Precise / Research usage gate (tooling v0.8)

New `register-check` classifies **machine-accepted syntax** without changing
canonical vocabulary or grammar. `Core` is strict canonical single clauses;
`Precise` additionally permits explicitly scoped canonical propositional logic;
`Research` explicitly permits opt-in v0.5/v0.6 syntax and the experimental
toneless profile. Broader input never silently becomes canonical.

```sh
python3 -m veka register-check 'Mi pa dak mel.'
python3 -m veka register-check 'Zi mi gos ve ti gos yu.' --max-register precise
python3 -m veka register-check 'Mi gos zi ti gos.' --max-register research
python3 -m veka register-check 'Mi fok mel.' --profile toneless --max-register research
```

**Parser acceptance is not human comprehension or safety validation.** See
[register semantics and limitations](docs/registers_v08.md).

## Lojban-inspired semantic scope (opt-in; no language changes)

The new `semantic` CLI projects **already-valid canonical** Veka into an
inspectable predicate/argument tree. It shows why `ne` inside a quantified
clause differs from a fully scoped `na ... yu`, labels a few reviewed
predicate places (other verbs retain subject/object labels), and expands
existing transparent noun compounds into their component tokens. There are
**no** new particles, dictionary entries, or mandatory spoken constructions.

```sh
python3 -m veka semantic 'Al ren ne gos.'
python3 -m veka semantic 'Na al ren gos yu.'
python3 -m veka semantic 'Mi dak mel to ti en pas sun.'
```

This is structural annotation, not real-world truth evaluation or evidence of
improved listener comprehension. Multiple quantified participants and
quantified possessors fail closed. Read the [semantic scope specification](docs/semantic_scope_v01.md).

## Interlingua-inspired learning aids (opt-in; no language changes)

The `family` command exposes *existing* canonical noun-modifier compounds
and separately labeled experimental v0.5 event derivations. The optional
`beginner --families` flag explains related forms without registering
any new word. `--readings` adds **exact-match**, unverified editorial
examples in English and Brazilian Portuguese (not machine translation);
unlisted sentences receive no translation.

```sh
python3 -m veka family dak
python3 -m veka family kun --limit 5 --format json
python3 -m veka beginner 'Mi pa dak mel.' --families --readings
```

Canonical forms and grammar remain frozen, and comprehension benefits have
**not** been measured. See [semantic family learning study and limits](docs/semantic_family_learning_v09.md).

## Everyday-language learning and requirements (v0.9, noncanonical)

A **four-level beginner lesson set** checks 16 starter examples against strict
canonical Veka. A separate **100-scenario, two-turn English dialogue inventory**
maps common communication requirements without inventing Veka translations or
claiming missing grammar. Neither tool provides human comprehension evidence.

```sh
python3 -m veka learn --level 1
python3 -m veka learn --level 4
python3 -m veka everyday-audit
python3 -m veka everyday-audit --domain clarification --include-items
```

See [the v0.9 everyday learnability protocol](docs/everyday_learning_v09.md).
Canonical vocabulary and grammar remain frozen; extensions are still opt-in.

**International names:** strict parsing now preserves capitalized Unicode single-token names such as `São`, `Łódź`, and `O’Connor` without changing Veka vocabulary or pronunciation. Multiword and uncased-script names require future explicitly scoped grammar. See [proper-name limitations](docs/proper_names_v09.md).

## Veka at first sight (beginner reading guide)

Use the **read-only interlinear guide** to understand canonical Veka before
memorizing its vocabulary. It shows English word glosses, strict grammatical
roles, and separate **unverified** international-looking associations where
available. It never substitutes experimental drafts into canonical text.

```sh
python3 -m veka beginner 'Mi pa dak mel.'
python3 -m veka beginner 'Mi sen kun.'
python3 -m veka beginner 'Mi sen kun.' --format json
python3 -m veka beginner 'Mi sen kun.' --no-cues
```

See [the beginner guide](docs/first_sight_guide.md) for a short lesson and
practice sentences. This is a presentation improvement, **not** evidence
that Veka is as immediately recognizable as Interlingua or that new word
forms are accepted into its grammar.

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

## Veka audio-quality preflight (research-only)

After collecting **real, independently produced** ABX WAV files, run an
additional read-only screening step before an authorized researcher listens to
the recordings. It uses only Python's standard library and does **not** alter
the canonical language, convert audio, mark clips as recorded, or fabricate
human observations.

```sh
python -m veka listening-preflight \
  --recording-csv /secure/recording_jobs.csv \
  --audio-root /secure/actual-wavs > /secure/preflight.json
```

The preflight requires a complete confirmed recording bank. It rejects
malformed ABX manifests, missing/truncated WAV files, byte-identical files,
and repeated decoded PCM even if WAV container bytes differ. It reports
per-clip RMS, clipping fraction, DC offset and advisory review warnings.
A clean report **never** certifies human speech, independent takes,
correct pronunciation, +5 dB SNR, or listener comprehension. See
[recording preflight protocol](docs/audio_preflight_v09.md).

## Veka 0.6 — blinded meaning-recovery study packet

The new `meaning-plan` command prepares a condition-blinded **participant
sheet**, separate researcher answer key, and recording job sheet for the
existing 32 constructed meaning pairs. It rejects structurally mismatched
pairings, ensures one presentation per meaning, and does **not** generate
audio or participant outcomes. The older `study-assign` output contains
the target meanings and should only be handled by researchers.

```sh
python -m veka meaning-plan --participant P001 --arm 0 \
  --participant-csv /tmp/participant.csv --key-csv /tmp/researcher.csv \
  --recording-csv /tmp/recordings.csv
```

See [meaning-recovery pilot protocol](docs/meaning_pilot_v06.md) for
blinding, recording, consent, adjudication and measurement limits.

## Veka 0.7 — structural communication regression corpus (noncanonical)

A new opt-in `communication-audit` command generates deterministic, curated **synthetic**
meaning contrasts, negative controls, and ambiguous-ellipsis examples. It checks strict
parser-field differences and conservative context recovery without changing canonical
forms. This is **not a human comprehension benchmark** and supplies no observed speech
or listener results. See [communication benchmark design](docs/communication_benchmark_v07.md).

```sh
python -m veka communication-audit
python -m veka communication-audit --profile toneless
```

## Veka 0.6 — empirical listening-study preparation

New blinded ABX pilot tools test phonetic contrasts without changing the Veka language. The system creates a participant-only trial schedule, a separate answer key and a human recording job manifest; it fails closed when asked to score missing WAV files or incomplete responses. Experimental audio is **not generated**, and **no human results are collected** in this release. Current tonal pilot: 13 contrasts, 104 trials for two talkers; toneless: 12 contrasts, 96 trials. Clip IDs are opaque and stable across participants assigned to the same arm and frozen stimulus bank.

```sh
python -m veka listening-plan --participant P001 --arm 0 --talker S01 --talker S02 \
  --participant-csv /tmp/participant.csv --key-csv /tmp/researcher-key.csv \
  --recording-csv /tmp/recording-jobs.csv
# After recording independent human WAVs and collecting real responses:
python -m veka listening-score --key-csv /tmp/researcher-key.csv \
  --responses-csv /path/to/completed.csv --recording-csv /tmp/recording-jobs.csv \
  --audio-root /path/to/actual-wavs
```

See [Veka 0.6 listening pilot protocol](docs/abx_protocol_v06.md) for blinding, recording and calibration requirements, statistical limitations and research ethics. Pilot infrastructure does **not** establish better human comprehension or speech speed.

## Cross-family lexical readiness (experimental, no canonical change)

`python3 -m veka lexical-readiness` produces an evidence-first research backlog
for Veka's 100 international-vocabulary concepts. It joins existing structural
word checks, independently labeled language-family attestations and descriptive
human-trial conditions. A two-family coverage prefilter is a research heuristic,
**not proof of comprehension or grounds for replacing vocabulary**. With the
bundled header-only evidence and trial files, eight experimental forms need
source review and 92 concepts still need proposals. There are no measured
learner outcomes, no automatically approved words and no canonical lexicon
changes. See [research readiness and language comparisons](docs/lexical_readiness_v09.md).

## Veka 0.7 global-comprehension research (opt-in; no canonical changes)

The experimental `global-audit` command compares reviewer-sourced candidate word
attestations across **unrelated language families** without treating multiple
Indo-European languages as independent genealogical evidence. `global-score`
reports only actually recorded comprehension and repair outcomes by learner
family, and cannot declare a winning word or automatically adopt vocabulary.

```sh
python -m veka global-audit
python -m veka global-score
python -m unittest discover -s tests -q
```

The bundled default CSV templates have **zero** verified attestations and **zero**
participant trials. A separate [source-linked music loanword case study](docs/music_loanword_case_study_v07.md)
contains five explicitly **unverified** leads. Audit with
`python -m veka global-audit --evidence data/global_music_leads_v07.csv`
without counting unreviewed items as verified cognates. All 1,025 canonical entries and existing
parsing semantics are unchanged. See [the Veka 0.7 research protocol](docs/global_comprehension_v07.md)
for evidence fields, blinded pilot methods, candidate provenance rules, privacy,
and empirical adoption gates.

## Veka 0.5 lexical-risk research (opt-in; no vocabulary changes)

The new `lexical-risk` command ranks **symbolic** near-pair risks with explicit **assumed**, not measured, exposure and consequence priorities, and generates alternative *unadopted* word forms. It also reports the 708 noun-adjective compounds whose silent hyphen produces the same spoken sequence as an ordinary noun-adjective phrase. It does **not** predict human errors or change the 1,025 canonical entries.

```sh
python -m veka lexical-risk --top 10 --target mi --target ne --target ran
python -m veka lexical-risk --profile toneless --top 10 --target mi
```

See [the v0.5 design and falsification protocol](docs/lexical_design_v05.md). No audio recordings or listener outcomes have been collected.

## Experimental 0.6 discourse and temporal grammar (opt-in)

A new `python -m veka discourse` command adds in-situ topic/focus marking, explicit location-restricted quantifiers, and bounded before/after temporal clauses, with no change to the canonical vocabulary or existing parsers. It enforces single-role reference, required arguments and overt scope boundaries. This is **machine-tested syntax**, not demonstrated listener comprehension or spoken efficiency.

```sh
python -m veka discourse 'Sas mi yu pa dak kol mel yu.'
python -m veka discourse 'Al ren gin pas yu pa gos.'
python -m veka discourse 'Sik ti ton mel yu mi dak mel.'
```

Read [Veka 0.6 grammar and limitations](docs/grammar_v06.md) before treating these constructions as established vocabulary.

## Experimental 0.5 grammar extensions (opt-in)

The reference extension now implements six regular event-derivational suffixes, a 4×6 correlative matrix, and bounded relative/propositional complements without altering the 1,025 canonical headwords. It adds `python -m veka extend`, `derive`, and `correlative` commands; the original `parse` behavior and tonal/toneless profiles remain the baseline. **No spoken-comprehension or speed advantage has been measured.**

```sh
python -m veka extend 'Ren ri wek dak mel yu pa gos.'
python -m veka extend 'Mi sen ka ti ton mel yu.'
python -m veka derive dak-nes
python -m veka correlative hon-ren
```

See [Veka 0.5 grammar specification](docs/grammar_v05.md) for restrictions, semantic interpretation, and compatibility guarantees.

## Spoken aesthetics: opt-in pilot (not a change to canonical Veka)

The `aesthetics` command uses transparent **text-only** heuristics to rank
hypothetical sound shapes; candidate hyphenated compounds require a separate
spoken segmentation review. The `prosody` command describes optional
tone-safe sentence delivery. Neither generates audio or measures beauty.

```sh
python -m veka aesthetics ma-li da dak --profile tonal
python -m veka prosody 'Mi pái mel.' --profile tonal
python -m veka prosody 'Mi fok mel.' --profile toneless
python -m veka spoken-study-assign --participant S0001 --profile tonal --arm 0 \
  --output participant.csv --researcher-key private-researcher.csv
```

The last command produces *blank* participant response fields and a
separate condition key, not a human study or sound recordings. See
[the spoken aesthetics proposal](docs/spoken_aesthetics_v05.md) for the
scoring weights, safety caveats and study protocol.

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
| `veka/lexical_risk.py` + `data/lexical_priors_v05.csv` | Explicit risk-prior hypothesis audit, unadopted single-root alternatives, spoken compound surface equivalence |
| `docs/lexical_design_v05.md` + `tests/test_lexical_risk_v05.py` | Method, known limits, experimental gates, regression tests |
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

## Opt-in international cognate pilot (0.7 research)

A separate, **noncanonical** pilot now tests 10 new internationalisms against
matched-syllable invented forms and eight replacement candidates against current
Veka roots. Participants see one rendition per meaning with balanced randomized
arms; the researcher key stays separate. It changes **no** dictionary entries,
accepted vocabulary, parser semantics, or versioned profiles. No human outcomes,
verified donor attestations, or speech recordings exist.

```sh
python -m veka cognate-audit
python -m veka cognate-manifest --participant P001 --arm 0 \
  --output p001.csv --answer-key p001_key.csv
# Score only collected and independently annotated human responses:
python -m veka cognate-score --answer-key p001_key.csv --annotated responses.csv
```

Review the candidate list, evidence requirements, exact experimental conditions,
and adoption gates in [the Veka 0.7 cognate pilot protocol](docs/cognate_pilot_v07.md).

Source-linked, **unverified** attestation leads for taxi, hotel, and robot
are available for independent multilingual review. To audit the 12 pending
review records without claiming human validation, run:

```sh
python -m veka cognate-leads
```

See [the Veka 0.7 source-review packet](docs/cognate_source_review_v07.md).

### Blinded, local first-sight trial collection (research only)

Prepare a participant-only JSON from the pre-generated blind manifest, then
open `site/cognate-study.html` locally and load that JSON. The page shows
18 unfamiliar words without translations, captures voluntary free-text guesses
and exploratory browser durations, and exports an unscored response CSV.
**No responses are automatically uploaded or collected by this repository.**

```sh
python -m veka cognate-session --manifest p001.csv --output p001-session.json
# After a volunteer returns an exported CSV, separately create a PRIVATE human review sheet:
python -m veka cognate-judge-sheet --answer-key p001_key.csv \
  --responses /path/to/participant-responses.csv --output p001-PRIVATE-review.csv
# After independent human adjudication, score with cognate-score as above.
```

Never provide the researcher key or judgment sheet to participants. No
cross-language recognition advantage is demonstrated by this tooling. See
[the first-sight pilot procedure](docs/cognate_first_sight_session_v07.md).

## Veka 0.6 experimental compound semantics and typed derivation metadata

The optional `compound-semantics` command inventories the **708 canonical
noun-adjective compounds** and their identical specified spoken word sequences.
All 708 are already **canonical compositional aliases** under the Veka 0.6
specification; their *possible specialized pragmatic uses* remain unreviewed.
An optional editorial CSV can flag a proposed *compositional alias* or
*potential lexicalization* without changing
canonical vocabulary, adding audible hyphen markers or claiming listening results.

```sh
python3 -m veka compound-semantics --top 5
python3 -m veka compound-semantics --review-file my_compound_review.csv --top 5
python3 -m veka derive dak-nes
python3 -m veka derive dak-mol
python3 -m veka derive gos-vuk
```

The existing experimental `derive` output now includes a backward-compatible
`semantic_contract` describing input and output argument roles, while retaining
its previous `semantics` dictionary and all existing 0.4/0.5/0.6 parser behavior.
See [Veka 0.6 compound and derivation semantics](docs/compound_semantics_v06.md)
and the [blank editorial CSV template](data/compound_review_template_v06.csv).
No human learning, meaning-discrimination or speech advantage is established.

## Concise statements and experimental reversible script metadata (0.5)

Use an **opt-in** two-clause conversational register when only one logical
connective is needed. Complex logic remains explicitly bracketed; the original
`parse` command is unchanged:

```sh
python -m veka extend 'Mi gos zi ti gos.'
python -m veka extend 'Mi gos oi ti gos.'
python -m veka logic 'Zi mi gos ve ti gos yu.'
```

The SVG syllable-block renderer now preserves word and syllable indexes in
machine-readable metadata. The `read-script` command reconstructs lowercase
romanized text, including tone marks and hyphenated compounds:

```sh
python -m veka render 'Mi pái mel.' --output my_script.svg
python -m veka read-script --input my_script.svg
```

**Limitations:** reconstruction reads embedded labels, **not the drawn shapes**.
It is not OCR, a Unicode writing standard, or proof that two shapes are visually
distinguishable. Case, original spaces, and sentence-final punctuation are not
preserved. SVG metadata is checked for ordering, legal syllables, and tone-label
consistency. See `docs/grammar_v05.md` for the concise syntax and limitations.
