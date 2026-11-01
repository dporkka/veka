# Experimental Veka quotation and repair — v0.1

**Status:** research-only grammar and reference parser. No word in this document
is added to the canonical 1,025-entry dictionary, and the core, precise,
extended, discourse and register-check parsers are unchanged. These markers
are untested **experimental shapes**, not established human conversational
forms or historically attested international cognates.

## Motivation and scope

Interlingua is already capable of ordinary requests for repetition,
confirmation, correction and quotation in natural discourse. Veka's strict
reference grammar primarily handles independently parsed propositions, so
it cannot safely infer *which prior utterance* is meant by an ambiguous
clarification request.

The new `repair` command accepts a bounded, explicit research structure
that quotes exactly one **strict canonical Core** clause and, for a
correction, one replacement clause. For discourse-linked operations,
the caller **must** supply the previous spoken/textual utterance as `--prior`;
the quoted source must produce the **same full Core AST** as that prior.
This is a structural match, not evidence that a human interlocutor actually
heard, shared, intended or understood the quoted meaning.

## Grammar

The three-syllable markers are deliberately overt and are not canonical
words. Written hyphens are **silent**; acoustic distinctiveness and whether
these strings can be reliably segmented in natural speech are entirely
unmeasured.

```ebnf
quote       = "ko-ta-ra", canonical_core_clause, "yu" ;
repeat      = "re-pe-ta", canonical_core_clause, "yu" ;
confirm     = "kon-fi-ra", canonical_core_clause, "yu" ;
correction  = "ko-re-ta", canonical_assertion, "yu",
              canonical_assertion, "yu" ;
```

All quoted clauses must be *complete*, explicit-argument Core clauses;
contextually omitted arguments and `sa` are rejected by strict parsing.
The quoted content cannot contain nested repair operators or `yu`.
Only the whole repair utterance may have terminal punctuation.
Quoted polar questions are allowed for repetition/confirmation/quotation,
but corrections require two distinct assertions.

- **Quotation:** `Ko-ta-ra Mi pa dak mel yu.` labels the proposition as
  quoted material; it does **not** assert it and does not require a prior.
- **Request repetition:** `Re-pe-ta Mi pa dak mel yu.` with prior
  `Mi pa dak mel.` requests that *specific* prior proposition be repeated.
- **Request confirmation:** `Kon-fi-ra Ti gos ke yu.` with prior
  `Ti gos ke.` asks for confirmation of the quoted yes/no question's
  wording. This does not yet encode a full natural-language question about
  the truth of an embedded proposition.
- **Correction:** `Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu.`
  with prior `Mi pa dak mel.` presents a replacement proposition,
  explicitly distinct in its negation. The parser does **not** prove the
  replacement true or independently verify who uttered the original.

## Run

```sh
python3 -m veka repair 'Ko-ta-ra Mi pa dak mel yu.'
python3 -m veka repair 'Re-pe-ta Mi pa dak mel yu.' --prior 'Mi pa dak mel.'
python3 -m veka repair 'Kon-fi-ra Ti gos ke yu.' --prior 'Ti gos ke.'
python3 -m veka repair 'Ko-re-ta Mi pa dak mel yu Mi pa ne dak mel yu.' \
  --prior 'Mi pa dak mel.'
python3 -m veka repair 'Ko-ta-ra Mi fok mel yu.' --profile toneless
```

The machine-readable result distinguishes quoted material, verified AST
anchoring, and a replacement *presented* without claiming its truth.
The `--prior` argument is forbidden for free quotations to prevent
inventing provenance. Missing/incorrect prior, missing/extra closers,
duplicate quoted scopes, question-to-assertion corrections, repeated
identical propositions and unsupported syntaxes fail closed.

## Human and compatibility gates

This prototype does not solve general anaphora, semantic paraphrase,
clarification of unknown words, requests to slow speech, conversational
turn-taking, natural pragmatics or politeness. Even its four research
operators are not proven comprehensible or acoustically separable.
Before promotion to Veka Core, compare them against unmarked alternatives
using blind recorded conversation trials with several first-language groups.
Measure teaching time, correct interpretation, critical referent/number/
negation errors, listener response times and successful repairs.

**Do not merge the markers into the canonical dictionary or claim
spoken effectiveness without those findings.** For now, `repair` remains a
separate command; neither `parse` nor `register-check` accepts it.
