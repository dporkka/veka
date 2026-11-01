# Veka v0.10 — English/Esperanto-inspired grammar contrasts

**Status:** Read-only, optional learner exercises. **NOT** a Veka 0.10
canonical language release. The v0.3 grammar, v0.4 lexical contract,
strict parser, experimental profiles, and lexicon remain unchanged.

## Why this teaching tool exists

- English offers little mandatory nominal agreement, but has irregular
  verbs, opaque spelling, and hard-to-learn tense/aspect conventions.
- Esperanto is broadly regular, but its required accusative and adjective
  agreement create extra obligatory morphology.
- Veka already has an invariant core, explicit particles, predictable
  spellings and fixed argument order. Adding yet another agreement rule
  would make learning harder without providing a demonstrated benefit.
- Learners need to **see what changes meaning**, not merely read lists of
  rules. These six curated pairs alter just one token, while the strict
  parser validates the structural difference is limited to its intended
  feature (including the linked quantified subject).

## Practice

```shell
python3 -m veka contrast-drills --lang en
python3 -m veka contrast-drills --lang zh
python3 -m veka contrast-drills --lang pt-BR
python3 -m veka contrast-drills --lang pt-BR --format json
python3 -m veka contrast-drills --profile toneless
python3 -m unittest discover -s tests -p 'test_contrast_drills_v10.py' -v
```

The drills cover speaker pronouns, past marking, future marking, negation,
every/some scope, and object identity. Each pair has:

1. One inserted, removed or substituted token (orthographic units).
2. Strict canonical grammar parses for **both** utterances.
3. An exact, declared difference in structural parse fields; unexpected
   parse changes cause the whole packet to fail.
4. Explicit English/Mandarin/Brazilian Portuguese editorial readings and
   word-level glosses with **zero silently substituted English fallbacks**.
5. Schema metadata saying that no human comprehension test has occurred and
   no canonical vocabulary has changed.

For example, `Mi pa dak mel.` vs `Mi pa ne dak mel.` isolates the predicate
negation particle `ne`. Likewise, `Al ren pa gos.` vs `Kis ren pa gos.`
changes an `every` subject quantifier to `some`, and the parser records
both the subject and quantifier changes. The paraphrases do **not** claim to
be the only valid translations; e.g. unspecified tense need not denote
English simple present in every context.

## Boundaries, not claims

- These are **reading exercises**, not speech recognition or listening
  experiments. Orthographic one-token differences do not guarantee acoustic
  discriminability under noise or accented speech.
- English, Mandarin and Portuguese examples are **editorial** and need
  independent bilingual review. The parser proves structural differences,
  **not** truth-conditional equivalence to the prose translations.
- This does not resolve Veka's silent compound hyphen, limited everyday
  discourse, tone accessibility, or international recognition of roots.
- Do not use these paired answers as a blinded comprehension corpus: the
  displayed answers would leak test stimuli. Recruit independent native
  speakers and use held-out tasks for any human validation.
- Esperanto/English are **design comparisons**. No comparative learner
  performance data has been collected and this tool does not establish Veka
  as globally easier, more efficient, or more neutral.

For the **separate human editorial review gate**, two-reviewer CSV workflow,
blinded held-out comprehension preparation, and reuse of existing tonal vs.
toneless listening tooling, see `docs/contrast_human_study_v10.md`.

See `docs/esperanto_interlingua_design_review_v06.md`,
`docs/international_root_plan_v10.md` and
`docs/everyday_learning_v09.md` for experimental priorities.
