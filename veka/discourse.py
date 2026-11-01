"""Veka 0.6 optional discourse semantics: overt scope and fail-closed parsing.

This module intentionally does not mutate the 0.5 canonical lexicon or parser.
No listener-level efficiency, focus exhaustivity, or time-order accuracy is implied.
"""
from __future__ import annotations

from .core import Lexicon, VekaError, _normalize_sentence, validate_word
from .extended import parse_extended

TOPIC = "sas"
FOCUS = "kol"
LOCATION_DOMAIN = "gin"
BEFORE = "sik"
AFTER = "men"
END = "yu"
MARKERS = frozenset({TOPIC, FOCUS, LOCATION_DOMAIN, BEFORE, AFTER})
MAX_TOKENS = 128
ALLOWED_ROLES = ("subject", "object", "recipient", "location", "time")


def _check_inventory(lex: Lexicon):
    for marker in MARKERS:
        if not validate_word(marker) or marker in lex:
            raise VekaError("experimental marker invalid or collides with vocabulary: " + marker)


def _parse_v05(tokens: list[str], lex: Lexicon) -> dict:
    return parse_extended(" ".join(tokens), lex, strict=True)


def _unwrap_information(tokens: list[str]) -> tuple[list[str], dict]:
    """Unwrap in-situ markers; preserve intended noun phrases and their positions."""
    unpacked = []
    candidates = {}
    i = 0
    while i < len(tokens):
        token = tokens[i].lower()
        if token not in (TOPIC, FOCUS):
            unpacked.append(tokens[i])
            i += 1
            continue
        kind = "topic" if token == TOPIC else "focus"
        if kind in candidates:
            raise VekaError("duplicate information-structure marker")
        try:
            end = next(j for j in range(i + 1, len(tokens)) if tokens[j].lower() == END)
        except StopIteration as exc:
            raise VekaError("information-structure marker must close with yu") from exc
        contents = tokens[i + 1:end]
        if not contents or len(contents) > 2:
            raise VekaError("topic/focus supports only bare or quantified noun heads")
        if len(contents) == 2 and contents[0].lower() not in ("al", "kis"):
            raise VekaError("two-word topic/focus must be a quantified head")
        if any(t.lower() in MARKERS or t.lower() == END for t in contents):
            raise VekaError("nested topic/focus scope is unsupported")
        candidates[kind] = " ".join(contents).lower()
        unpacked.extend(contents)
        i = end + 1
    return unpacked, candidates


def _unwrap_location_domain(tokens: list[str], lex: Lexicon) -> tuple[list[str], dict | None]:
    """Parse 'al|kis noun gin place yu' as a restricted quantifier.

    The place predicate is attached to the quantified participant. Actual
    domain membership/truth comes from the world, not the grammar parser.
    """
    positions = [i for i, word in enumerate(tokens) if word.lower() == LOCATION_DOMAIN]
    if not positions:
        return tokens, None
    if len(positions) != 1:
        raise VekaError("only one domain-restricted quantifier is supported")
    i = positions[0]
    if i < 2 or i + 2 >= len(tokens) or tokens[i + 2].lower() != END:
        raise VekaError("domain restriction must be 'quantifier noun gin place yu'")
    q, head = tokens[i - 2].lower(), tokens[i - 1].lower()
    if q not in ("al", "kis"):
        raise VekaError("domain restriction requires an overt al/kis quantifier")
    if head not in lex or lex[head].pos != "noun":
        raise VekaError("domain restriction requires an explicit lexical noun class")
    place = tokens[i + 1].lower()
    if place not in lex or lex[place].pos != "noun" or lex[place].domain != "places":
        raise VekaError("located_in restrictor requires a place-class noun")
    reduced = tokens[:i] + tokens[i + 3:]
    return reduced, {
        "head": head, "quantifier": ("every" if q == "al" else "some"),
        "phrase": q + " " + head, "relation": "located_in", "place": place,
    }


def _role_for_value(ast: dict, value: str) -> str:
    roles = [r for r in ALLOWED_ROLES if ast.get(r) == value]
    if len(roles) != 1:
        raise VekaError("marked constituent must occupy one unique overt clause role")
    return roles[0]


def _parse_main(tokens: list[str], lex: Lexicon) -> dict:
    if not tokens:
        raise VekaError("missing main clause")
    unwrapped, marks = _unwrap_information(tokens)
    reduced, restriction = _unwrap_location_domain(unwrapped, lex)
    if any(token.lower() in MARKERS for token in reduced):
        raise VekaError("discourse operator in unsupported position")
    result = _parse_v05(reduced, lex)

    if (marks or restriction) and result.get("mood") is None:
        raise VekaError("discourse marking requires a single atomic statement, not coordination")
    if marks and (result["mood"] != "statement" or result["question"]):
        raise VekaError("topic/focus markers are limited to declarative clauses")
    for kind, head in marks.items():
        role = _role_for_value(result, head)
        result[kind] = {"role": role, "value": head}

    if restriction:
        role = _role_for_value(result, restriction.pop("phrase"))
        if role not in ("subject", "object", "recipient", "location"):
            raise VekaError("quantifier restrictor must modify a nominal participant")
        if result.get(f"{role}_quantifier") != restriction["quantifier"]:
            raise VekaError("quantifier scope and place restriction disagree")
        result["quantifier_domain"] = {
            "role": role, "quantifier": restriction["quantifier"],
            "head": restriction["head"], "relation": restriction["relation"],
            "place": restriction["place"],
        }
    return result


def parse_discourse(sentence: str, lex: Lexicon) -> dict:
    """Parse one optional temporal subordinate plus one explicit main clause.

    'sik SUB yu MAIN' => main event precedes subordinate event.
    'men SUB yu MAIN' => main event follows subordinate event.
    Neither asserts a causal link or automatically anchors events on a timeline.
    """
    _check_inventory(lex)
    tokens = _normalize_sentence(sentence)
    if len(tokens) > MAX_TOKENS:
        raise VekaError("discourse expression exceeds token limit")
    lower = [x.lower() for x in tokens]
    temporal = [i for i, t in enumerate(lower) if t in (BEFORE, AFTER)]
    if not temporal:
        return _parse_main(tokens, lex)
    if temporal != [0]:
        raise VekaError("temporal operator must appear once at the beginning")
    if lower.count(END) != 1:
        raise VekaError("temporal clause must have exactly one end marker")
    end = lower.index(END)
    if end < 2 or end >= len(tokens) - 1:
        raise VekaError("temporal operator requires a complete subordinate and main clause")
    subordinate = tokens[1:end]
    main = tokens[end + 1:]
    # Avoid pretending that interactions of nested scopes have been specified.
    if any(t.lower() in MARKERS or t.lower() in ("ri", "ka", END) for t in subordinate + main):
        raise VekaError("nested or combined temporal scopes are not yet defined")
    sub_ast = _parse_v05(subordinate, lex)
    main_ast = _parse_v05(main, lex)
    if any(a.get("mood") != "statement" or a.get("question") for a in (sub_ast, main_ast)):
        raise VekaError("temporal clauses must be complete assertive statements")
    main_ast["temporal"] = {
        "relation": "main_before_subordinate" if lower[0] == BEFORE else "main_after_subordinate",
        "clause": sub_ast,
    }
    return main_ast
