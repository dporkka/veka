# Veka 1.1 tooling — international-root audit (noncanonical)

**Status:** opt-in research assistance only. Canonical Veka 0.4 vocabulary
(317 atomic roots, 708 noun–modifier compounds), reference grammar, parser,
and frozen compatibility manifest are unchanged.

## Purpose

Veka may gain first-sight recognizability from widely used international
roots, but longer borrowed words can cost speaking time or create semantic
confusion and language-family advantages. The objective remains **correctly
understood meaning per total interaction time**, including training,
pronunciation, listening, errors, clarification and repair. Dictionary entries
in multiple languages do not prove that speakers recognize the adapted form.

Run the exhaustive read-only audit:

```bash
python3 -m veka root-research --output /tmp/veka-root-research.json
python3 -m unittest discover -s tests -p 'test_root_research_v11.py' -v
```

`root_inventory.roots` includes every one of the 317 original atomic roots,
its gloss and part of speech, existing international research membership,
unverified draft where available, and the number of dictionary compounds in
which it occurs as a head or modifier. These dependencies indicate
**migration cost**, not measured lexical exposure. Never equate compound count
with spoken frequency. The report's statuses are:

- `protected_structural`: pronouns, particles, digits, time terms and units.
  Do not modify through general vocabulary selection.
- `draft_needs_evidence`: research form passes existing mechanical checks;
  **not accepted or verified**.
- `repair_draft`: candidate fails existing structural validation.
- `needs_proposal`: one of the old 100 research concepts, no draft yet.
- `not_queued`: no international candidate research has been specified.

This adds visibility into the **217 roots omitted from the prior 100-concept
queue**; it does not automatically invent proposals for those roots.

## Candidate comparison: explicit, hypothetical scenarios only

The optional CSV schema is
`data/root_scenarios_template_v11.csv`. Add **two records** for each
supported `concept_id`, one with `condition=core` and the existing root form,
the other with `condition=candidate` and the verified-structure experimental
form. The input template is intentionally empty. The `form` and ID must
exactly match the established research mapping. Duplicate, incomplete,
unknown, out-of-range, non-finite or otherwise mismatched rows are rejected.

```bash
python3 -m veka root-research \
  --scenarios /path/to/your_hypothetical_scenarios.csv \
  --output /tmp/veka-root-research-scored.json
```

Each row requires five **researcher-assumed** 0–100 numbers (higher is better),
`critical_error_count` (nonnegative integer), and a nonempty
`scenario_note` documenting how the assumptions were chosen:

| Factor | Weight |
| --- | ---: |
| `recognition_acquisition` | 35% |
| `pronunciation_listening` | 25% |
| `compactness` | 15% |
| `semantic_clarity` | 15% |
| `cross_family_access` | 10% |

The example weights are **design assumptions, not fitted coefficients**.
The output sorts hypothetical candidate-minus-core score differences,
but reports `evidence_observed=false`,
`human_benefit_established=false` and `adoption_authorized=false`
even with a positive difference. A candidate with an assumed critical error
receives `research_gate=critical_error_review` irrespective of its total.
A scenario comparison cannot prove superiority or change standard Veka.

**Do not input real study data into this scenario model as if it were a
validated estimator.** For actual human study provenance, use the existing
`global-audit`, `lexical-readiness`, `cohort-plan` and `global-score`
workflows; they have their own review and data-integrity limits.

## Future root-selection workflow

1. **Preserve high-frequency structural grammar.** Start with optional
   content vocabulary. Map every proposed change to a specific semantic
   sense, not only an English gloss.
2. **Look for internationalisms across families**, including Mandarin/Sinitic,
   Indo-Aryan, Romance/Germanic/Slavic, Arabic/Semitic, Malay/Austronesian,
   Swahili/Niger-Congo, and other relevant learner groups. Language count,
   family count, loanword ancestry and actual familiarity are different
   variables. Never treat several Romance languages as independent families.
3. **Review donor sources independently**, including pronunciation,
   false friends, local usage and registered sense. Keep provenance for
   every donor-language assertion. For example, Portuguese `data` usually
   means calendar date, not English `data`.
4. **Respect Veka phonotactics and parser markers.** Run
   `international-audit` and the full regression suite. Check undelimited
   spoken segmentation and compound compatibility; a root replacement
   propagates to existing compounds.
5. **Compare against baseline**, not only unrelated nonce words:
   first-sight comprehension, time to learn, retention after a delay,
   independently recorded speech-in-noise, actual utterance length, repairs,
   and high-consequence semantic mistakes. Use balanced learner-language
   cohorts and preregistered statistical criteria.
6. **Migrate only with compelling empirical results.** Preserve the frozen
   lexicon, grammar and exact-number/logic rules unless adopting a new
   separately versioned canonical language profile with text-conversion
   rules and compound/teaching materials updated together. Inconclusive
   evidence means leave the canonical word unchanged.

For existing limits and research protocols see
`docs/lexical_readiness_v09.md`,
`docs/international_v04.md` and `docs/crossfamily_study_v10.md`.
