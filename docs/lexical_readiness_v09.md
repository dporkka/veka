# Veka 0.9 — Cross-family lexical research readiness

**Opt-in research tooling; no canonical language, lexicon, parser or phonology changes.**

Veka currently combines several unrelated design ideas. It shares analytic
particle syntax with Mandarin/Indonesian, formal scope discipline with Lojban,
regular derivation research with Esperanto, short compositional roots with
Toki Pona, and a separate Korean-inspired script prototype. Interlingua's
first-sight vocabulary recognition is the most promising *hypothesis* for
reducing Veka's initial learning cost, but the current proposed forms have no
verified cross-family recognition results. These are design analogies, not
linguistic similarity measurements.

## Use

```sh
python3 -m veka lexical-readiness
python3 -m veka lexical-readiness \
  --candidates data/international_candidates_v04.csv \
  --evidence data/global_evidence_v07.csv \
  --trials data/global_trials_v07.csv \
  --output /tmp/lexical-readiness.json
python3 -m unittest discover -s tests -p 'test_lexical_readiness_v09.py' -v
```

This command joins the existing structural candidate audit, cross-family
attestation review and descriptive observed-trial report; it does **not**
substitute string similarity or English spelling for comprehension data. The
result includes every proposed or unproposed concept, its canonical root,
syllable-length cost, structural problems, **reviewer-asserted** independently
attested language families, outstanding source-review count, condition-balanced
language-family coverage, critical errors and a suggested next research action.

The actions are ordered to triage scarce research effort, not to rank word
quality or predict adoption:

| Next action | Why it appears |
| --- | --- |
| `investigate_critical_errors` | An observed candidate-condition critical error requires review regardless of other progress |
| `manual_preregistered_review` | At least two independent attested families and two groups with both study conditions; **not approval** |
| `collect_balanced_human_trials` | Cross-family prefilter satisfied, but fewer than two trial-background families have both comparators |
| `verify_cross_family_attestations` | Fewer than two independent genealogical families have verified, meaning-equivalent source records |
| `repair_candidate` | Candidate violates the existing mechanical phonotactic or collision contract |
| `propose_candidate` | No draft international form exists |

Two families is an **explicit research-scheduling heuristic only**, not a
statistically justified adoption threshold, representative population sample,
or proof of independent loanword origin. Related language branches within one
family count as one family. Actual native/second-language comprehension can
only be evaluated with human speakers and listeners. The trial files do not
authenticate participants, recordings, recruitment, blinding, consent, or
preregistration; manually entered study data can be fabricated or biased.

Even when the `manual_preregistered_review` action is returned, **no adoption
is authorized**. A new canonical word would require an independent, predeclared
comparison of correct meanings communicated per total time, delayed retention,
acoustic confusion and critical semantic errors across relevant learner groups;
a versioned migration must explicitly address old texts, teaching materials,
and software compatibility. Do not interpret fewer syllables as necessarily
faster communication; do not assume longer international-looking words are
universally familiar.

## Current built-in dataset and compatibility

The default research queue has 100 concepts, eight experimental international
forms and 92 without a proposed form. The bundled global attestation and
human-trial templates contain headers only: **zero verified attestations and
zero recorded participants**. On the bundled files, eight forms require source
verification and 92 require proposals. No old forms are deprecated, all
1,025 existing headwords retain their meaning, and `parse` and `extend`
behavior are unchanged.

The machine-readable output is versioned as `veka.lexical-readiness.v09`.
`adoption_authorized` is always `false`; `human_benefit_established` is always
`false` for each row. This is deliberate: mechanical readiness is not evidence
of learning, recognition, cultural neutrality or audible intelligibility.

For evidence intake and protected human-subject practices, see
[global-comprehension protocol](global_comprehension_v07.md) and
[cognate pilot protocol](cognate_pilot_v07.md).
