# Optional Veka semantic scope and argument frames (v0.1)

**Status:** a machine-tested interpretation aid for the **existing canonical**
Veka 0.3 grammar and fully bracketed propositional logic. This does not add a
spoken particle, word, grammatical rule or new meaning to the frozen dictionary.
It takes inspiration from Lojban's explicit predicate places, but does not claim
Lojban's full formal semantics. It is **not** a theorem prover, translator, or
listener-comprehension result.

## Try it

```sh
python3 -m veka semantic 'Al ren ne gos.'
python3 -m veka semantic 'Na al ren gos yu.'
python3 -m veka semantic 'Mi dak mel to ti en pas sun.'
python3 -m veka semantic 'Mi lin kis ren.'
```

The output uses stable `veka.semantic-scope.v01` nodes with a top-level
`tree`. Canonical `parse`, `logic`, `extend`, `discourse`, the register gate,
and the canonical word list remain unchanged.

## Operator scope (not just string matching)

| Veka | Logical reading | Tree shape |
| --- | --- | --- |
| `Al ren ne gos.` | For every person x, x does not go | `forall(x, not(go(x)))` |
| `Na al ren gos yu.` | It is not the case that every person goes | `not(forall(x, go(x)))` |
| `Kis ren gos.` | Some person goes | `exists(x, go(x))` |
| `Na kis ren gos yu.` | No person goes | `not(exists(x, go(x)))` |

The restrictor is part of the quantification: universal quantification is read
as `∀x(person(x) ⇒ body(x))` and existential quantification as
`∃x(person(x) ∧ body(x))`. The domain is **not** asserted to be all people in
the world: `ren` is the speaker's contextual person category, and domain
membership and truth are unknown to the parser. The tree preserves lexical
restriction tokens separately from the bound participant role.

The existing `ne` negation has narrower scope **inside** the sole quantified
noun phrase; `na ... yu` negates the entire scoped expression. For nested
`zi` / `oi` / `fi` expressions, the tree preserves every existing
mandatory bracket. `fi` is **material implication** only.

## Predicate places without arbitrary extra learning burden

`Mi dak mel to ti en pas sun.` maps to `dak` with two *core* places:
`x1 = mi` (sender) and `x2 = mel` (sent item). `to ti`, `en pas`
and `sun` remain **optional grammatical adjuncts** (recipient, location,
time). In particular, the locative `en` does not imply a destination, route,
source or specific timestamp.

The projection has reviewed lexical labels only for `dak` (sender, item),
`ton` (receiver, item), `gos` (mover) and `lin` (perceiver, perceived
entity). All other lexical predicates use **structural** subject/object labels.
The parser never guesses agents or patients from English glosses. No canonical
lexeme or valency is altered. Derived predicates and experimental grammar
remain outside this canonical projection.

A quantified subject or object replaces just that participant with a local
variable `x1`. The parser still prohibits more than one quantified noun
phrase per atom. Quantifiers inside a possessor are **rejected** by this
projection because canonical syntax does not give them scope, even if the
ordinary syntax parser can represent their words.

Canonical noun/adjective compounds are expanded to compositional token
sequences using the existing surface-normalization contract:
`ren-sak` and `ren sak` receive the same structural nominal tokens.
This **does not** prove their pragmatic meanings are interchangeable or that
a listener can hear a silent written hyphen.

## Boundaries

This output records grammatical structure and the four reviewed lexical
argument frames, **not** full first-order truth conditions. It does not
interpret open discourse referents, the real-world meaning of tense/aspect,
quantifier domain membership, a noun's numeric/possessive pragmatics, or
multi-quantifier scope. It also rejects unsupported v0.5/v0.6 research syntax,
missing mandatory arguments, unresolved `sa` reference, and embedded questions
or imperatives. No change to human spoken fluency is established.

**Next experiment:** collect blinded comprehension judgments for the minimal
pair `al ren ne gos` / `na al ren gos yu` with explicit domain context and
varying learner language backgrounds; measure accuracy and repair time before
adopting any *new* spoken formal markers.
