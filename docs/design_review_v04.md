# Veka 0.4 — evidence-based design review and experimental revision

**Release candidate:** 1 November 2026. **Status:** machine-tested only; no human speech or listening validation. This proposal preserves Veka 0.3 as the default canonical language and adds a separately selected **toneless experimental profile**.

## Design principles and ranking

1. **Comprehension and recoverability before compression.** Correct meaning per total elapsed interaction time, including mistakes and repair, is the objective; syllable compression is a surrogate. Maintain two registers: explicit (required for critical content), and compact (permitted only when shared referents are unique).
2. **Phonological learnability before more vocabulary.** With only four tonal roots, lexical tone carries little lexical capacity relative to its possible learning and detection cost. Compare tonal and toneless vocabularies experimentally before making any permanent breaking language change.
3. **Uniform morphology before elaboration.** Preserve the 317 roots + 708 compositional noun words and fixed SVO/particle grammar. A future general derivation system should specify productive semantics, lexical category selection and unambiguous segmentation before adding affixes or irregularity.
4. **Explicit scope where needed.** Retain Veka 0.3's scoped logical particles and exact decimals. Full quantifier binding, comparisons, relative clauses and counterfactuals remain unsolved; do not imply the existing parser can express them.
5. **Accessible writing as a separate evaluation.** Romanization remains the interoperability reference. The existing block SVG script is a graphical prototype, not a studied literacy system or accessible alternative to Unicode.

## Actual Veka 0.4 changes

- `veka/profiles.py`: **explicit, collision-checked profiles**. Default remains `tonal` (full Veka 0.3 compatibility). Optional `toneless` replaces precisely four rising-tone primitive roots, retaining English glosses, parts of speech, valency, and lexical headword count. The mapped forms are available as candidates, not accepted permanent spellings.
- An optional `--profile tonal|toneless` was added to `parse`, `logic`, `lookup`, and `audit`, plus `profile` and `convert` CLI commands. Under `toneless`, a tonal root is **rejected**, not silently stripped. Token-aware conversion preserves punctuation, case and hyphen boundaries but **does not validate grammar**.
- Parser rejects repeated punctuation endings rather than silently discarding them; noun-phrase possession recursion is bounded at 16 levels. These changes deliberately reject previously accepted edge cases.
- Listener scoring rejects assigning the same `participant_id` + `trial_id` to both test conditions, and rejects unknown conditions. It does not modify or manufacture any trials.
- New regression suite checks lexical bijection, collision rejection, semantically equivalent profile parses, CLI behavior, malformed punctuation, recursion depth, and scoring protocol integrity.

## Candidate substitutions (NOT standard vocabulary)

| Canonical 0.3 | Toneless candidate | Meaning | Linguistic role |
|---|---|---|---|
| `pái` | `fok` | remember | transitive verb |
| `pál` | `lek` | hill | noun |
| `lé` | `hok` | idea | noun |
| `vén` | `gon` | trust | transitive verb |

These forms are sourced from the earlier `data/tone_free_ablation.csv`. No acoustic benefit is established. The tonal baseline has **2,262** structurally one-feature minimal pairs among non-numeric, non-unit roots; the **toneless candidates increase that count to 2,320**. This is a warning against proclaiming the replacements better, but not proof of greater auditory confusion: the audit counts abstract one-feature differences rather than measured recognition errors. In particular, a toneless variant trades a pitch distinction for segmental contrast and may lose or gain clarity with different speakers and listeners.

The four substitutions do not collide with existing headwords, and in this release no existing compound contains any of these four roots, so there is no hidden compound remapping. That assumption is checked against the current lexicon in the release review but should become a dedicated contract test before introducing derivations that embed tonal roots.

## Commands

```sh
python -m unittest discover -s tests -v
python -m veka profile tonal
python -m veka profile toneless
python -m veka parse 'Mi pái mel.' --profile tonal
python -m veka parse 'Mi fok mel.' --profile toneless
python -m veka lookup remember --profile toneless
python -m veka convert 'Mi pái mel.' --target toneless
python -m veka convert 'Mi fok mel.' --target tonal
python -m veka audit --profile tonal --top 5
python -m veka audit --profile toneless --top 5
```

Do **not** mix profiles in one teaching cohort without an explicit study assignment. Token conversion is for constructing matched experimental text; it does not prove semantic equivalence when discourse is ambiguous.

## Prioritized research plan

**P0 — No unearned claims of spoken efficiency.** Collect multi-speaker human recordings, including independent productions of A/B/X contrasts, and recruit listeners from multiple phonological backgrounds. Specify criterion-to-fluency training time, comprehension success, critical semantic error, speaking and listening time, confidence, and repairs. Compare quiet and noisy conditions, then inspect error matrices. Counterbalance training and testing across profile assignments.

**P1 — Optimize root forms from empirical confusion.** If a speaker/listener error pattern is reproducible, select replacement candidates using structural screening (phoneme inventory, syllable length, coda reliance, and minimal pairs) followed by listening tests. Current toneless substitutes increase abstract minimal pairs; do not promote them by default.

**P2 — Expand the *measured* communication domain.** Add realistic dialogues with unknown antecedents, competing referents, conflicting negation, repairs, and noncompressible controls. Measure correct propositions per minute and training time; stratify by language background.

**P3 — Formal grammar expansion.** Prototype explicit variable scope and quantifier domain restriction with executable semantic tests before introducing more logical operators. Pilot modality and relative clauses under a stable and teachable grammar. Add productive affixes only if composed meanings are predictable and not semantically overloaded.

**P4 — Writing-system ergonomics.** Test speed, readability, dyslexia/accessibility concerns, typing and screen readers separately; keep Romanized text fully supported.

## Decision threshold

**Do not replace canonical tonal Veka solely because it has four tonal roots.** Advance the toneless variant only if controlled human data show improved total correct-message throughput without an unacceptable rise in critical semantic errors, and the difference is robust to speaker/listener language background and noise. Predefine an explicit margin, sample size and analysis plan before data collection. No such results currently exist.

## Reproducible matched-pair corpus

`data/profile_pairs_v04.json` contains eight paired examples: six target contrasts covering all four replaced words and two unchanged controls. Unit tests parse both sides under `strict=True` and assert exact abstract-role equivalence after applying only the four lexical mappings. This is a **machine-only semantic contract**; it does not establish whether two utterances are equally memorable, equally fast to say, or similarly intelligible.

## Experimental comparison safeguards

- Treat the canonical and candidate profiles as separately taught lexicons, each identified with its profile label in recorded metadata.
- Use independent human productions and trained listeners. Test a range of talkers and language backgrounds; do not use the text renderer as a surrogate for audio.
- Predefine whether the hypothesis concerns *complete profile usability* or *isolated lexical-tone perception*. The proposed four substitutions change both segmental identity and pitch dependence, so a profile-level comparison **cannot isolate a pure effect of tone**.
- Collect training time, lexical recall, comprehension, confidence, repeats, and repairs. Do not merge outcomes across different participant training arms without stating the design.
- Keep the original 0.3 canonical lexicon stable while collecting evidence; no community-facing vocabulary change is justified by these structural tests.
