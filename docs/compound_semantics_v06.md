# Veka 0.6 — spoken-compound review and typed derivation contracts

**Status: opt-in research tooling and annotation metadata, not a revised canonical language.**
Veka's 1,025 headwords, original grammar, tonal/toneless profiles, orthographic rules, and `parse` behavior remain untouched. The accepted [Veka 0.6 structural-alias specification](specification_status_v06.md) already defines all 708 transparent compounds as compositionally equivalent to the corresponding noun-adjective phrase. This tool **does not challenge or redefine that normative structural meaning**. It audits possible specialized pragmatic associations for future review. There are **no human recordings, listeners, comprehension or phonetic results** behind these editorial labels.

## Why the audit exists

All 708 noun–adjective dictionary compounds are written `noun-adjective`. Because the hyphen is *silent* in the current specification, the compound and an ordinary `noun adjective` phrase have the same **specified segmental sequence**. This does not establish that their meanings differ, that listeners make mistakes, or that they possess identical prosodic boundaries in actual human speech.

For example, the lexicon glosses `ren-sak` as *expert*, while `ren sak` composes as *knowledgeable person*. **Both have the same canonical compositional meaning**; the dictionary gloss is not a separate truth-conditional predicate. Whether the compact English gloss suggests a specialized conventional or pragmatic association in actual use remains a research question, not a recognized extra lexical sense.

## Editorial classifications (not adoption decisions)

- **unreviewed** (default): the *optional specialized-sense hypothesis* has not been editorially assessed. Canonical compositional equivalence still holds. A distinct intended pragmatic meaning needs context or paraphrase if precision matters.
- **compositional_alias**: an editor proposes treating the lexical entry as the same compositional meaning as the ordinary phrase. This remains an editorial hypothesis, not a human comprehension result.
- **potential_lexicalization**: an editor flags a hypothetical **future noncanonical** conventional sense, **without** claiming that it is part of current Veka or can be detected from the bare sound. Avoid relying on a silent hyphen for critical distinctions.

An optional CSV is deliberately empty by default; the language does not automatically classify 708 semantics from their glosses. The review file must have *exactly* `compound,classification,evidence_note`. Each nonempty row must refer to a real canonical compound, have one of the two explicit editorial classifications, and carry a nonempty rationale. Duplicate or unrecognized entries fail closed. The current reviewer metadata is an **editorial note**, not an independent etymological citation or a validated measurement.

## Usage

```sh
# Show deterministic sample; 708 compounds are assessed, none reviewed by default
python3 -m veka compound-semantics --top 5
# Export all 708 surfaces without altering the dictionary
python3 -m veka compound-semantics --top 5 --output /dev/shm/compound_report.json
# Run an external manually prepared review; do not modify the blank template
python3 -m veka compound-semantics --review-file my_compound_review.csv --top 5
python3 -m veka compound-semantics --profile toneless --top 5

# Existing derive command now adds a typed semantic_contract without changing
# the legacy semantics.{relation,event_lemma} structure:
python3 -m veka derive dak-nes
python3 -m veka derive dak-mol
python3 -m veka derive dak-kas
python3 -m veka derive gos-vuk
python3 -m unittest discover -s tests -q
```

Sample **research-only** review CSV:

```csv
compound,classification,evidence_note
ren-sak,potential_lexicalization,expert may conventionally mean more than knowledgeable person
```

Do not silently promote the row as canonical or change pronunciation. The CLI `--output` report contains **all** rows, whereas `--top` only limits the console preview. Both include accurate full-count statistics.

## Existing experimental derivational semantics made explicit

The `derive` and `extend` API outputs now include an additive `semantic_contract` object; the legacy `semantics` field remains unchanged, preserving existing integrations. The contract exposes:

- `input_roles`: available base-event argument positions: subject, and object only for transitive roots.
- `output_roles`: grammatical argument positions for the derived predicate (empty for noun/adjective word classes).
- `argument_map`: e.g. `gos-vuk` maps new subject to *causer* and new object to the original event's subject (causee). `dak-koin` preserves base subject/object.
- `denoted_role`: e.g. `dak-nes` = base subject of sending; `dak-mol` = base direct object; `dak-vau` is a property of the base object, **not** the sender.
- `event_relation`: e.g. `dak-kas` = attempt to reverse a prior event. It does **not** entail that reversing succeeds.
- `bare_form_asserts_event_occurrence: false` means a bare word form is not a truth-assertive sentence; a complete affirmative clause can assert an event.
- `success_entails_reversal` is explicitly `false` for `-kas` only, and `null` where the property is not applicable.

Important: these are **symbolic schema contracts** for the limited parser, not a full compositional event ontology. They do not independently establish whether real events occurred, what a cause is, whether a person intended something, or whether successful undoing is possible. Unsupported verb valencies and suffix stacking continue to fail.

## Reproducibility, quality gate, and pending studies

Run the focused tests and complete repository suite with Python's built-in `unittest`. No dependency change is necessary. The tests verify all canonical compounds, untouched headword counts, failed review import validation, both lexical profiles, representative semantic role mapping, and existing prohibited derivations.

Future promotion requires independent human review for conventional meanings, recorded spoken compounds *and* adjective phrases from multiple speakers, contextual meaning judgments (not just orthographic segmentation), audio discrimination in quiet and noise, and comparisons of clarification time. A semantic alias or separator should only become canonical after a versioned proposal and evidence that it improves net understood communication. If no gain is shown, keep the language unchanged.

This work implements the first two technical gates in the [draft design RFC PR #10](https://github.com/dporkka/veka/pull/10). It does **not** depend on merging that RFC, and avoids interference with the existing experimental discourse parser in Veka 0.6.
