"""Veka 0.5: opt-in, typed morphology, correlatives, and bounded clause embedding.

All new forms are experimental. Canonical Veka 0.4 remains unchanged.
No contextual guessing; one embedded structure per sentence at present.
"""
from __future__ import annotations

from .core import (
    Discourse, Entry, Lexicon, VekaError, _normalize_sentence, parse,
    validate_word,
)

# Bound suffixes: transparent event relations, not idiomatic translations.
# "reverse" means attempting to undo the previous event, not its logical negation.
DERIVATIONS = {
    "nes": ("agent", "noun"),
    "sul": ("instrument", "noun"),
    "zel": ("place", "noun"),
    "dil": ("result", "noun"),
    "vuk": ("cause", "verb"),
    "kas": ("attempt_reverse", "verb"),
    "mol": ("patient", "noun"),
    "koin": ("repeat", "verb"),
    "vau": ("passive_able", "adjective"),
}
# Semantic commitments are descriptive AST metadata; no events are evaluated.
# The existing minimal "semantics" dictionary is preserved for API compatibility.
DENOTED_ROLES = {
    "agent": "base_subject",
    "patient": "base_object",
    "instrument": "event_instrument",
    "place": "event_location",
    "result": "event_result",
    "passive_able": "base_object",
}
EVENT_RELATIONS = {
    "cause": "cause_base_event",
    "repeat": "repeat_event",
    "attempt_reverse": "attempt_to_reverse_prior_event",
}


def _semantic_contract(operation: str, base_valency: str, output_pos: str) -> dict:
    """Explicit participant mapping, without asserting actual event occurrence."""
    input_roles = ["subject"] + (["object"] if base_valency == "transitive" else [])
    output_roles = (
        (["subject", "object"] if operation == "cause" else list(input_roles))
        if output_pos == "verb" else []
    )
    mapping = ({"subject": "causer", "object": "base_subject"} if operation == "cause"
               else {role: f"base_{role}" for role in output_roles})
    return {
        "input_roles": input_roles,
        "output_roles": output_roles,
        "argument_map": mapping,
        "denoted_role": DENOTED_ROLES.get(operation),
        "event_relation": EVENT_RELATIONS.get(operation, "relation_to_base_event"),
        "bare_form_asserts_event_occurrence": False,
        "success_entails_reversal": False if operation == "attempt_reverse" else None,
    }

SERIES = {
    "hon": "interrogative", "hal": "demonstrative",
    "nis": "indefinite", "pan": "universal",
}
DOMAINS = {
    "ren": ("person", "pronoun"),
    "ril": ("thing", "pronoun"),
    "lok": ("place", "noun"),
    "kel": ("time", "time"),
    "wek": ("manner", "correlative"),
    "gas": ("quantity", "correlative"),
}
# The two openers, gap and closer are intentionally explicit.
RELATIVE = "ri"
COMPLEMENT = "ka"
GAP = "wek"
CLOSE = "yu"
SENTINEL_CLAUSE = "Vekaclause"
SENTINEL_GAP = "Vekahole"
CLAUSAL_PREDICATES = frozenset({"sen"})  # understand [that <proposition>]
MAX_WORDS = 128

def _guard_markers(lex: Lexicon) -> None:
    """No shadowing existing headwords, and all grammatical forms are legal."""
    markers = set(DERIVATIONS) | set(SERIES) | set(DOMAINS) | {RELATIVE, COMPLEMENT, GAP}
    if not all(validate_word(w) for w in markers):
        raise VekaError("extension contains an illegal grammatical form")
    reserved = set(DERIVATIONS) | set(SERIES) | {RELATIVE, COMPLEMENT}
    # Domain labels may coincide with canonical roots: only bound forms use them.
    # The standalone gap, unlike suffix use, cannot collide.
    reserved |= {GAP}
    collisions = reserved & set(lex)
    if collisions:
        raise VekaError("extension marker conflicts with lexicon: " + ", ".join(sorted(collisions)))

def derive(form: str, lex: Lexicon) -> dict:
    """Return a compositional derivation; never quietly reinterpret a headword."""
    _guard_markers(lex)
    if form in lex:
        raise VekaError("existing headword cannot be redefined as a derivation")
    if form.count("-") != 1:
        raise VekaError("derivation requires exactly one root-suffix boundary")
    base, suffix = form.split("-")
    e = lex.get(base)
    if not e or e.pos != "verb" or e.kind != "root":
        raise VekaError("derivation requires a primitive verb root")
    if suffix not in DERIVATIONS:
        raise VekaError("unknown derivational operator")
    if not validate_word(form):
        raise VekaError("derived form violates phonotactics")
    operation, part_of_speech = DERIVATIONS[suffix]
    if operation == "cause" and e.valency != "intransitive":
        raise VekaError("causative of transitive verb requires unimplemented third role")
    if operation == "attempt_reverse" and e.valency != "transitive":
        raise VekaError("reverse-event operator currently accepts transitive verbs only")
    if operation in ("patient", "passive_able") and e.valency != "transitive":
        raise VekaError(f"{operation} requires a direct-object transitive verb")
    valency = ("transitive" if operation == "cause" else
               e.valency if part_of_speech == "verb" else "")
    return {
        "form": form, "base": base, "operation": operation,
        "pos": part_of_speech, "valency": valency,
        "semantics": {"relation": operation, "event_lemma": base},
        "semantic_contract": _semantic_contract(operation, e.valency, part_of_speech),
        "lexicalized": False,
    }

def correlative(form: str, lex: Lexicon) -> dict:
    """A systematic 4 × 6 cross-product with explicit semantic domains."""
    _guard_markers(lex)
    if form.count("-") != 1:
        raise VekaError("correlative must contain one series-domain boundary")
    prefix, suffix = form.split("-")
    if prefix not in SERIES or suffix not in DOMAINS:
        raise VekaError("unknown correlative series or domain")
    if form in lex:
        raise VekaError("correlative conflicts with canonical headword")
    if not validate_word(form):
        raise VekaError("correlative violates phonotactics")
    domain, pos = DOMAINS[suffix]
    return {
        "form": form, "series": SERIES[prefix],
        "domain": domain, "pos": pos,
    }

def extended_lexicon(lex: Lexicon) -> Lexicon:
    _guard_markers(lex)
    result = Lexicon(lex)
    for prefix in SERIES:
        for suffix in DOMAINS:
            word = f"{prefix}-{suffix}"
            c = correlative(word, lex)
            result[word] = Entry(word, f"{c['series']} {c['domain']}",
                                 c["pos"], "experimental", "reference", "", "", "")
    return result

def _expand_lexicon(tokens: list[str], base: Lexicon) -> Lexicon:
    result = extended_lexicon(base)
    for token in tokens:
        word = token.lower()
        if "-" in word and word not in result:
            d = derive(word, base)
            result[word] = Entry(word, d["operation"] + " of " + d["base"],
                                 d["pos"], "experimental", "derivation",
                                 d["base"], word.split("-")[-1], d["valency"])
    return result

def _annotate(result: dict, tokens: list[str], lex: Lexicon) -> dict:
    """Add semantic quantifier or question metadata without hiding scope."""
    out = dict(result)
    roles = ("subject", "object", "recipient", "location", "time")
    quantified = sum(
        out.get(f"{role}_quantifier") is not None
        for role in ("subject", "object", "recipient", "location")
    )
    found_questions = []
    refs = {}
    for role in roles:
        value = out.get(role)
        if not value:
            continue
        for word in value.split():
            if word.count("-") != 1 or word.split("-")[0] not in SERIES:
                continue
            c = correlative(word, lex)
            if c["pos"] == "correlative":
                raise VekaError("manner/quantity correlatives are not yet integrated into clauses")
            refs.setdefault(role, []).append(c)
            if c["series"] in ("universal", "indefinite"):
                if out.get(f"{role}_quantifier") is not None:
                    raise VekaError("quantifier repeated within one noun phrase")
                quantified += 1
                if role == "time":
                    out["time_quantifier"] = "every" if c["series"] == "universal" else "some"
                else:
                    out[f"{role}_quantifier"] = "every" if c["series"] == "universal" else "some"
            elif c["series"] == "interrogative":
                found_questions.append({"role": role, "domain": c["domain"], "form": word})
    if quantified > 1:
        raise VekaError("two quantified roles require explicit scope grammar")
    if found_questions:
        if len(found_questions) != 1 or result["question"] or result["mood"] != "statement":
            raise VekaError("content question cannot mix with a polar question or another interrogative")
        out["question"] = True
        out["question_type"] = "content"
        out["content_question"] = found_questions[0]
    elif result["question"]:
        out["question_type"] = "polar"
    if refs:
        out["correlatives"] = refs
    derived = {}
    for role in ("subject", "object", "recipient", "location", "predicate"):
        value = out.get(role)
        if not value:
            continue
        for word in value.split():
            if word.count("-") == 1 and word not in lex and word.split("-")[-1] in DERIVATIONS:
                derived.setdefault(role, []).append(derive(word, lex))
    if derived:
        out["derivations"] = derived
    return out

def _parse_atomic(tokens: list[str], lex: Lexicon, strict: bool) -> dict:
    words = _expand_lexicon(tokens, lex)
    result = parse(" ".join(tokens), words, context=Discourse(), strict=strict)
    return _annotate(result, tokens, lex)

def _parse_subordinate(tokens: list[str], lex: Lexicon, gap: bool = False) -> dict:
    if not tokens:
        raise VekaError("empty subordinate clause")
    if any(t.lower() in (RELATIVE, COMPLEMENT, CLOSE) for t in tokens):
        raise VekaError("nested extensions are not supported")
    if any(t.lower().startswith("hon-") for t in tokens):
        raise VekaError("subordinate propositions cannot be content questions")
    if gap:
        if sum(t.lower() == GAP for t in tokens) != 1:
            raise VekaError("relative clause requires exactly one explicit gap")
        tokens = [SENTINEL_GAP if t.lower() == GAP else t for t in tokens]
    elif GAP in [t.lower() for t in tokens]:
        raise VekaError("gap is only legal inside a relative clause")
    parsed = _parse_atomic(tokens, lex, True)
    if parsed["question"] or parsed["mood"] != "statement":
        raise VekaError("embedded clause must be an assertive proposition")
    return parsed

def parse_extended(sentence: str, lex: Lexicon, strict: bool = True) -> dict:
    """Single-clause baseline, or one relative OR propositional complement.

    Relative: noun ri [clause containing exactly one wek gap] yu ...
    Complement: subject sen ka [complete proposition] yu
    No implicit relative binding, recursive embedding, or multi-quantifier scope.
    """
    tokens = _normalize_sentence(sentence)
    if len(tokens) > MAX_WORDS:
        raise VekaError("extension exceeds token bound")
    lowered = [t.lower() for t in tokens]
    if any(t in (SENTINEL_CLAUSE.lower(), SENTINEL_GAP.lower()) for t in lowered):
        raise VekaError("reserved internal placeholder cannot appear in source")
    opens = [i for i, t in enumerate(lowered) if t in (RELATIVE, COMPLEMENT)]
    if len(opens) > 1:
        raise VekaError("only one subordinate structure allowed per sentence")
    if not opens:
        # A conversational two-atom register reuses the *same* logical
        # connectives. Only one infix operator is allowed: no precedence,
        # implicit grouping, commands, questions, or context-based guessing.
        infix = [i for i, word in enumerate(lowered) if word in ("zi", "oi")]
        if infix:
            if len(infix) != 1 or not 0 < infix[0] < len(tokens) - 1:
                raise VekaError("concise register requires exactly two atomic clauses")
            from .logic import parse_logic
            pos = infix[0]
            explicit = " ".join([lowered[pos], *tokens[:pos], "ve", *tokens[pos + 1:], "yu"])
            return parse_logic(explicit, lex, strict=True)
        if CLOSE in lowered or GAP in lowered:
            raise VekaError("orphaned scope boundary or relative gap")
        return _parse_atomic(tokens, lex, strict)
    start = opens[0]
    if lowered.count(CLOSE) != 1:
        raise VekaError("embedded clause requires exactly one end marker")
    end = lowered.index(CLOSE)
    if end <= start + 1:
        raise VekaError("missing embedded proposition")
    subordinate = tokens[start + 1:end]
    marker = lowered[start]
    if marker == COMPLEMENT:
        nested = _parse_subordinate(subordinate, lex)
        main_tokens = tokens[:start] + [SENTINEL_CLAUSE] + tokens[end + 1:]
        out = _parse_atomic(main_tokens, lex, strict)
        if out["predicate"] not in CLAUSAL_PREDICATES or out["object"] != SENTINEL_CLAUSE:
            raise VekaError("clause complement only licensed as object of a cognition verb")
        out["object"] = None
        out["object_clause"] = nested
        return out

    # Syntactic attachment requires a unique, bare noun head immediately before ri.
    if start < 1:
        raise VekaError("relative clause has no preceding nominal head")
    head = lowered[start - 1]
    if head not in lex or lex[head].pos != "noun":
        raise VekaError("relative must attach to a bare canonical noun head")
    relative = _parse_subordinate(subordinate, lex, gap=True)
    gaps = [k for k in ("subject", "object") if relative.get(k) == SENTINEL_GAP]
    if len(gaps) != 1:
        raise VekaError("relative gap must occupy subject or direct-object role")
    main_tokens = tokens[:start] + tokens[end + 1:]
    out = _parse_atomic(main_tokens, lex, strict)
    heads = [k for k in ("subject", "object") if out.get(k) == head]
    if len(heads) != 1:
        raise VekaError("relative attachment head must have one unambiguous clause role")
    out[heads[0] + "_relative"] = {
        "head": head, "gap_role": gaps[0], "clause": relative,
    }
    return out
