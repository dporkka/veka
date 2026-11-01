"""Explicit structural semantics for canonical, transparent noun compounds.

A silent hyphen does not encode a distinction from the corresponding
noun-adjective phrase. This module only normalizes *compositional surface
structure*, not pragmatics, lexical connotations or spoken comprehension.
The existing parser AST and canonical dictionary are unchanged.
"""
from __future__ import annotations

import unicodedata

from .core import Discourse, Lexicon, VekaError, _np


def normalize_nominal_surface(phrase: str, lex: Lexicon) -> tuple[str, ...]:
    """Return an inspectable canonical NP token sequence.

    Expand every registered transparent noun-adjective compound to its
    component words, preserving quantifiers, modifiers, numbers, possession
    and other overt tokens. Input must be a complete valid noun phrase.
    """
    if not isinstance(phrase, str) or not phrase.strip():
        raise VekaError("expected a nonempty nominal phrase")
    words = unicodedata.normalize("NFC", phrase).split()
    parsed, consumed = _np(words, 0, lex, Discourse(), strict=True)
    if consumed != len(words):
        raise VekaError("nominal phrase has unparsed or unsupported tokens")
    result = []
    for token in parsed.split():
        entry = lex.get(token)
        if entry is None or entry.kind != "compound":
            result.append(token)
            continue
        head = lex.get(entry.head)
        modifier = lex.get(entry.modifier)
        if (entry.pos != "noun"
                or entry.form != f"{entry.head}-{entry.modifier}"
                or head is None or head.kind != "root" or head.pos != "noun"
                or modifier is None or modifier.kind != "root"
                or modifier.pos != "adjective"):
            raise VekaError(f"invalid transparent compound metadata: {token}")
        result.extend((entry.head, entry.modifier))
    return tuple(result)
