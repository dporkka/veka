# Veka-T: proposed technical register (design only)

**Status:** concept proposal, **no parser, vocabulary, compiler, or accepted
keywords**. Canonical Veka grammar and lexicon remain unchanged.

The objective is to reduce *time to correct shared technical meaning* for
international software teams, not simply shorten code or replace English.

## Minimum viable semantics

An experimental terminology registry should have immutable, language-neutral
`concept_id` values (e.g. `messaging.send`), verified definitions, argument
roles, optional type and effect signatures, versioned translations with
reviewer provenance, and an explicit ambiguity policy. Human-facing Veka
labels are a display layer, never the authoritative machine identifier.

A prototype should define no more than 25 concepts initially. Compare
correct understanding of short specifications and error reports across
English-based, translated, and Veka-T displays with equal training time.
Report subgroup results, edit cost, and misunderstandings. Avoid favoring
English/French/Portuguese/Spanish as if they were independent language
families when evaluating international recognizability.

**Do not** invent a Veka programming language or source-to-source transpiler
before measuring whether shared stable IDs and localized terminology help
existing teams. For code, use Unicode-safe/ASCII-compatible IDs and established
languages' existing parsers; separate spoken labels from program syntax.
