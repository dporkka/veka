# Core, Precise, and Research registers (noncanonical tooling v0.8)

**Status:** a machine-enforced **usage contract**, not a new language release.
Canonical Veka remains the frozen 0.4 tonal lexicon and 0.3 reference grammar.
No forms, definitions, parser semantics, or compatibility manifests are changed
by this addition. Language-tagged research extensions remain opt-in.

## Why this exists

A human learner should not have to infer from separate CLI commands which
examples are canonical and which are research proposals. The
`register-check` command accepts a maximum allowed usage tier and labels
the **least experimental** parser/profile that actually accepts the utterance.

It enforces **syntax provenance**, not an evaluation of a real listener's
understanding, fluency, cultural accessibility, or physical safety.

| Register | Allowed syntax | Vocabulary | Specification status |
|---|---|---|---|
| Core | Strict single-clause v0.3 `parse` (no guessed omitted valency or unresolved `sa`) | Canonical tonal | Canonical |
| Precise | Core plus fully delimited propositional v0.3 `logic` | Canonical tonal | Canonical, restricted formal meaning |
| Research | Core/Precise plus opt-in `extend` (v0.5) and `discourse` (v0.6) | Tonal or experimental toneless | Experimental if extensions or toneless substitutions are used |

Core/Precise/Research are **usage tiers**, not separate grammars and not an
automatic judgement that any given sentence is suitable for a consequential
task. In particular, the formal `fi` operator means *material implication*,
not ordinary causal, predictive or counterfactual "if."

## Try it

```sh
# Canonical everyday clause, requiring every argument:
python3 -m veka register-check "Mi pa dak mel."

# Fully scoped canonical logic, deliberately not available under Core:
python3 -m veka register-check "Zi mi gos ve ti gos yu." --max-register precise

# Experimental v0.5 concise conjunction; requires explicit opt-in:
python3 -m veka register-check "Mi gos zi ti gos." --max-register research

# Experimental v0.6 topic/focus:
python3 -m veka register-check "Sas mi yu pa dak kol mel yu." --max-register research

# Even an ordinary sentence using an experimental lexicon is Research:
python3 -m veka register-check "Mi fok mel." --profile toneless --max-register research
```

Disallowed input exits with code 2 and `VEKA ERROR:` rather than returning
an acceptance or silently converting forms. Core is the default; consumers
must explicitly request broader tiers. With `--max-register research`,
canonical sentences still report `register: core` or `precise` if accepted
at that tier. The separate `grammar_register` and `canonical_lexicon`
fields prevent experimental toneless input from being misrepresented as
canonical just because the grammar itself is canonical.

The structured output includes `schema_version`, `ast`, `parser`,
`register`, `grammar_register`, `allowed_through`, `profile`,
`canonical_grammar`, `canonical_lexicon`, `limitations`, and two
explicitly false evidence claims:
`human_comprehension_validated` and `communication_safety_certified`.

## Limitations and evaluation gate

- The gate does **not** detect whether a context is jointly shared or a
  proposition is true. Strict Core excludes guessing omitted roles, but an
  overt reference can still be pragmatically confusing.
- The gate does **not** certify that logical, numeric or grammatical forms
  are understandable in noisy speech. Syntax tests do not replace ABX
  listening, first-sight comprehension or actual conversation tests.
- The gate does **not** promote experimental morphology, discourse markers,
  toneless substitutes, international-looking associations, or research loans
  into the frozen canonical language.
- Existing v0.5/v0.6 parsers are intentionally bounded; unsupported nesting,
  more complex quantifier scope, and general discourse interpretation are
  still not available.
- The tier schema itself is tooling v0.8, independent of canonical language
  versions. Its labels are a policy for educational and developer tools, not
  a claim of universal natural-language grammar.

**Next measured experiment:** use existing blinded listening study tooling
to compare trained Core and research forms on realistic messages with varied
speaker/listener backgrounds. Measure correctly interpreted meanings per
minute **including** teaching and clarification costs, plus critical errors.
No candidate should become canonical from parser acceptance alone.
