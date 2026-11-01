# Veka dialogue screening v0.1 (noncanonical, no translation claim)

This tool makes the 100 existing two-turn English requirements **actionable** for
human translation study. It does not translate English, change the canonical
dictionary, add a grammar rule, or prove a communicative feature is supported.

## Proposed attempt input

Create a local JSON file with this exact schema:

```json
{
  "schema_version": "veka.dialogue-attempts.v01",
  "attempts": [
    {
      "id": "ED-001",
      "turns": [
        {"speaker": "A", "veka": "Hon-ren pa gos.", "intended_act": "content_question"},
        {"speaker": "B", "veka": "Mi pa gos.", "intended_act": "statement"}
      ]
    }
  ]
}
```

**These sentences intentionally do not translate ED-001.** They demonstrate
that even a mechanically valid question/statement pair can be completely
wrong in meaning. Never present passing examples as verified translations.

The admitted `intended_act` values are `statement`, `polar_question`,
`content_question`, and `request`. The last compares to the parser's
imperative mood only, not to politeness or a speaker's true intention.

Run:

```sh
python3 -m veka dialogue-check --attempts attempts.json --max-register research
python3 -m veka dialogue-check --attempts attempts.json  # strict Core only
```

The report distinguishes:

- **Syntax accepted**: each utterance parses at or below the permitted
  grammar register (research-only forms do not silently become canonical).
- **Speech act aligned**: parsed question type or imperative/statement shape
  matches the submitter's *provisional* structural label.
- **Ready for semantic review**: both turns pass those preliminary checks.
- **Meaning equivalence verified**: always false; only independent reviewers
  can determine whether the source English intent is preserved.
- **Human comprehension validated**: always false; requires real participants.

Invalid schema, duplicate/unknown scenario IDs, reordered speakers, invalid
speech-act tags, or nonempty unsupported metadata all fail closed. Invalid
Veka is reported per turn so the researcher can diagnose missing grammar.

## Next study protocol

1. Two independent, trained bilingual reviewers draft Veka translations for
   a stratified selection of the frozen requirements. Preserve intended
   pragmatic function and label their turns with the supplied speech-act tags.
2. Run `dialogue-check`. Resolve rejected syntax with a separate,
   versioned opt-in grammar proposal **or** note the unresolved need. Do not
   make a sentence syntactically valid by replacing its intended message.
3. Independently adjudicate translation equivalence, referent resolution,
   politeness, and ambiguity. Record disagreements; no review artifact
   automatically changes the canonical language.
4. Conduct preregistered human learning and comprehension trials, with
   native-language backgrounds sampled independently and held-out cases.
   Measure training time, correct message recovery, repairs, serious errors,
   and delayed recall.

The CLI operates offline with the Python standard library. There are **no
human results or certified Veka translations** in this release.
