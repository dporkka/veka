# Veka 0.6 — experimental information structure, restricted domains and temporal clauses

**1 November 2026. Status:** opt-in machine-tested grammar, **not** a full natural-language grammar; no human speech or comprehension data. Existing Veka 0.4/0.5 vocabularies, tonal profiles, and default parse paths are unchanged.

The new parser is invoked with `python -m veka discourse '...'`, optionally with `--profile toneless`. The v0.5 `extend` command remains a separate, backward-compatible parser. Every accepted v0.6 extension is explicit and returns structured AST metadata; it does not automatically infer speaker intent.

## 1. Information structure: topic and focus

In-situ bracketed noun phrases make grammatical role recovery deterministic.

| Form | Meaning | Parse |
| --- | --- | --- |
| `Sas ren yu pa gos.` | As for the person, that person went | `topic={role:subject,value:ren}` |
| `Mi pa dak kol mel yu.` | I sent **the message** (message is in focus) | `focus={role:object,value:mel}` |
| `Sas mi yu pa dak kol mel yu.` | I (topic) sent the message (focus) | separate topic/focus nodes |

`sas` opens a topic constituent, `kol` opens a focus constituent, and `yu` closes either one. The marker replaces neither the referent nor the normal SVO order. Unmarked v0.5 concise coordination remains accepted unchanged, but topic/focus or domain restriction **inside** a coordinated proposition is rejected until cross-clause scope is specified. One topic and one focus at most, each a bare noun/pronoun/proper form or a single explicitly quantified noun `al/kis + noun`. The annotated word must map to **exactly one role** (subject, object, recipient, location or time) in the parsed clause. Two identical noun phrases in separate roles are rejected rather than matched by guesswork. No topic/focus in questions or commands. No exhaustivity, contrastive alternatives, or uniqueness assertion is implied by focus.

## 2. Explicit location-restricted quantifier

`gin` is an overt *located-in* restriction, not a generic set-membership operator:

```ebnf
restricted_np = ("al" | "kis"), canonical_noun, "gin", place_noun, "yu";
```

- `Al ren gin pas yu pa gos.` — Every person **in the room** went.
- `Mi lin kis ren gin pas yu.` — I see some person **in the room**.
- `Sas al ren yu gin pas yu pa gos.` — As for every person in the room, each went.

The AST records `{role, quantifier, head, relation:"located_in", place}`. The place must be a canonical noun from the explicit `places` lexical class; `pas` is a room. Missing quantifier, absent scope closer, non-place `mel`, duplicate restrictions, or two quantified roles fail closed.

This records **linguistic syntax and scope** only: the parser does not determine who is physically in a room, which domain of speakers is shared, or whether the universal proposition is true. The restrictions are kept *inside* the quantifier, not as a clause-level location adjunct.

## 3. Bounded temporal subordination

```ebnf
temporal_utterance = ("sik" | "men"), assertive_clause, "yu", assertive_clause ;
```

The **first** clause describes the reference event; the second is the main event.

- `Sik ti ton mel yu mi dak mel.` — I send the message **before** you receive the message.
- `Men ti ton mel yu mi dak mel.` — I send the message **after** you receive the message.

`sik` encodes `main_before_subordinate`; `men` encodes `main_after_subordinate`. These describe temporal ordering, **not** causation, evidential certainty, counterfactuality, or a precise timestamp. Both clauses must be complete declarative statements with explicit required objects. Embedded questions, imperatives, nested temporal clauses, cross-embedded relatives and clausal complements are rejected. Veka 0.6 permits only **one temporal relation** per utterance.

## Phonology and compatibility

All five new markers `sas kol gin sik men` are legal under both Veka 0.4 tonal and tone-free sound inventories and are not canonical dictionary headwords. A structural sound check is not sufficient to certify intelligibility; the markers have not been recorded or evaluated by listeners. Existing parser APIs and the 1,025-entry canonical lexicon remain unchanged.

## Run

```sh
python3 -m veka discourse 'Sas mi yu pa dak kol mel yu.'
python3 -m veka discourse 'Al ren gin pas yu pa gos.'
python3 -m veka discourse 'Sik ti ton mel yu mi dak mel.'
python3 -m veka discourse 'Men ti ton mel yu mi dak mel.'
python3 -m unittest discover -s tests -q
```

## What remains unresolved

Nested or relative clauses inside temporal expressions, true compositional scope interactions among multiple quantifiers, clauses under focus, natural-language conditionals and counterfactuals, open-domain reference resolution, and conversational prosody are not yet implemented. Veka is an experimental language and its efficiency compared with existing spoken languages is unproven.

**Next evidence-driven step:** see [the proposed listening protocol](listening_protocol_v06.md) and [seven mechanically validated stimulus contrasts](../data/discourse_stimuli_v06.json). Record several trained producers saying balanced temporal/topic/focus stimuli, conduct blind listener comprehension tests in quiet and noise with varied language backgrounds, and measure correct interpretations per minute including error repair. Compare marked and unmarked controls rather than asserting that new markers are automatically beneficial.
