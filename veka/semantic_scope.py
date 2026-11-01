"""Optional Veka semantic-scope projection over the existing canonical parser.

No new spoken operators, inflection or lexical senses are introduced. The
representation distinguishes negation and the one supported quantified noun
phrase by making their nesting explicit. It is not a model of worldly truth.
"""
from __future__ import annotations

from .compounds import normalize_nominal_surface
from .core import Lexicon, VekaError
from .logic import parse_logic

SCHEMA_VERSION = "veka.semantic-scope.v01"

# Only lexical participant labels with a clear, explicitly reviewed reading.
# For every other verb, retain the known structural subject/object slots.
# 'to', 'en', and time are grammatical adjuncts, not additional obligatory
# predicate slots or inferred destinations, sources, dates, etc.
FRAMES = {
    "dak": ("sender", "sent_item"),
    "ton": ("receiver", "received_item"),
    "gos": ("mover",),
    "lin": ("perceiver", "perceived_entity"),
}


def _nominal(phrase: str, lex: Lexicon) -> tuple[dict, str | None]:
    tokens = list(normalize_nominal_surface(phrase, lex))
    quantifier = tokens.pop(0) if tokens and tokens[0] in ("al", "kis") else None
    # The canonical parser intentionally does not assign quantifier scope
    # inside possessors. Reject rather than silently losing that meaning.
    if any(token in ("al", "kis") for token in tokens):
        raise VekaError("quantified possessors require an explicit binding grammar")
    if not tokens:
        raise VekaError("quantifier requires a nominal restrictor")
    return {"tokens": tokens}, quantifier


def _atomic(clause: dict, lex: Lexicon) -> dict:
    if clause["mood"] != "statement" or clause["question"] or clause["compressed"]:
        raise VekaError("semantic projection requires explicit declarative roles")

    # Normalize every grammatical noun phrase before computing scope.
    phrases = {}
    quantifiers = []
    for role in ("subject", "object", "recipient", "location"):
        phrase = clause.get(role)
        if phrase is None:
            continue
        normalized, quant = _nominal(phrase, lex)
        phrases[role] = normalized
        if quant is not None:
            if clause.get(role + "_quantifier") != {"al": "every", "kis": "some"}[quant]:
                raise VekaError("quantifier metadata disagrees with noun phrase")
            quantifiers.append((role, quant, normalized))

    if len(quantifiers) > 1:
        raise VekaError("multiple quantifiers require an explicit scope grammar")

    predicate = clause["predicate"]
    labels = FRAMES.get(predicate, ())
    expected = 1 if clause["copula"] or clause["object"] is None else 2
    if labels and len(labels) != expected:
        raise VekaError("lexical predicate frame conflicts with canonical valency")

    quantified_role = quantifiers[0][0] if quantifiers else None
    arguments = []
    for index, role in enumerate(("subject", "object"), start=1):
        if role not in phrases:
            continue
        arguments.append({
            "slot": index,
            "role": role,
            "label": labels[index - 1] if labels else role,
            "value": {"variable": "x1"} if role == quantified_role else phrases[role],
        })

    adjuncts = []
    for role in ("recipient", "location", "time"):
        value = phrases.get(role)
        if role == "time" and clause.get("time") is not None:
            value = {"tokens": [clause["time"]]}
        if value is not None:
            adjuncts.append({
                "role": role,
                "value": {"variable": "x1"} if role == quantified_role else value,
            })

    predication = {
        "op": "predicate",
        "predicate": predicate,
        "copula": bool(clause["copula"]),
        "arguments": arguments,
        "adjuncts": adjuncts,
        "tense": clause["tense"],
        "progressive": bool(clause["progressive"]),
    }
    body = {"op": "not", "argument": predication} if clause["negative"] else predication

    if not quantifiers:
        return body

    role, quant, domain = quantifiers[0]
    return {
        "op": "forall" if quant == "al" else "exists",
        "binder": {"variable": "x1", "role": role, "domain": domain},
        "body": body,
    }


def _project(node: dict, lex: Lexicon) -> dict:
    op = node["op"]
    if op == "atom":
        return _atomic(node["clause"], lex)
    if op == "not":
        return {"op": "not", "argument": _project(node["argument"], lex)}
    if op in ("and", "or_inclusive", "if"):
        projected = {
            "op": op,
            "left": _project(node["left"], lex),
            "right": _project(node["right"], lex),
        }
        if op == "if":
            projected["interpretation"] = "material_implication"
        return projected
    raise VekaError("unsupported formal connective: " + str(op))


def analyze_scope(sentence: str, lex: Lexicon) -> dict:
    """Explain the existing canonical grammar as an explicit scope tree.

    A for-all binder is interpreted with an implicit restrictor implication;
    an exists binder with an implicit restrictor conjunction. Neither clause
    domain membership nor predicate truth is evaluated. The source grammar
    still admits just one quantified noun phrase per atomic clause.
    """
    syntax = parse_logic(sentence, lex, strict=True)
    return {
        "schema_version": SCHEMA_VERSION,
        "tree": _project(syntax, lex),
        "quantifier_semantics": {
            "forall": "for every value in the noun restrictor, the body holds",
            "exists": "some value satisfies both noun restrictor and body",
        },
        "truth_evaluated": False,
        "human_comprehension_validated": False,
        "grammatical_changes": False,
    }
