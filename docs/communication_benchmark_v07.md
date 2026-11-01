# Veka 0.7 — structural communication benchmark (research-only)

**Status:** noncanonical machine-testing instrument. **No human speech, participants,
recognition scores, acoustic recordings, or observed error rates.**

The established 0.4 lexicon and 0.3 grammar remain unchanged. The synthetic
domain manifest in `data/communication_domains_v07.json` provides 16 curated
transitive predicates and 8 intransitive predicates. A deterministic generator
combines these into approximately 250 short **template-generated, not naturally
sampled** communication contrasts.

## Usage

```sh
python -m veka communication-audit
python -m veka communication-audit --profile toneless
python -m unittest discover -s tests -q
make validate
```

The command checks, for every generated case, that both strict clause parses
have **exactly** the declared changed semantic fields. Equivalence controls
differ only in case or punctuation. Ambiguous ellipsis cases prove three
different properties:

1. Explicit speech parses independently of discourse context.
2. Compressed speech agrees with explicit speech when the subject has
   precisely one overt, mutually established candidate in supplied context.
3. Compressed speech **fails** when the context contains competing referents.

The output includes a stable SHA-256 fingerprint of the generated corpus, case
counts by category, and explicit `human_participants: 0`,
`human_accuracy: null`, and `acoustic_validation: false` flags.

## Case categories

| Category | Machine property being checked |
| --- | --- |
| `role_reversal` | Changing `mi`, `ti`, or `ni` changes the subject |
| `negation` | Changing `ne` changes predicate negation |
| `tense` | Changing `pa` to `fu` changes temporal marking |
| `polar_question` | Adding `ke` changes the utterance question flag |
| `quantity` | `ran` vs `kuk` changes exact decimal quantity |
| `recipient` | Switching recipient pronouns changes the recipient role |
| `location` | Room vs office changes the location role |
| `quantifier` | `al` vs `kis` changes quantified participant semantics |
| `equivalent_control` | Harmless orthographic difference preserves the complete AST |
| `unsafe_ellipsis` | Ambiguous context makes role omission fail closed |

All contrast classifications reflect *parser output*, not independent semantic
truth. Some combinations are more artificial than natural speech; participants
must not be tested on this generated corpus without an independent human
review of content, semantics, training, context cards, preregistration, and
consent. The same templates cannot support population-level generalization or
conclusions about Veka's efficiency relative to any other language.

## Purpose and limits

The benchmark is a **regression gate**, not an optimization reward or
phonetic-confusion model. More passing template cases do not indicate a
faster language. The `critical` flag marks an *assumed* semantic consequence,
not a measured risk. Exact AST differences detect unexpected parser behavior
but do not prove a listener would recognize the intended interpretation.

The existing blinded meaning-recovery packet (`meaning-plan`) remains the
appropriate basis for consenting human studies. Its participant and researcher
materials must not be replaced with this unblinded structural benchmark.

**Next research step:** independently sample real communicative situations,
include noncompressible and multiple-referent negative controls, obtain
trained-human recordings, and preregister correct propositions/minute
including repairs and subgroup-specific critical-error bounds. Then use
observed confusion matrices to prioritize proposed phonological changes.
