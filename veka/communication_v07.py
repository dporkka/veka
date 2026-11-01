"""Noncanonical Veka 0.7 structural communication contrast corpus.

This is synthetic parser-contract coverage, NOT a speech experiment,
human comprehension score, observed frequency model, or validated risk metric.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re

from .core import Discourse, Lexicon, VekaError, parse

SCHEMA = "veka.communication-audit.v07"
CATEGORIES = frozenset({
    "role_reversal", "negation", "tense", "polar_question", "quantity",
    "recipient", "location", "quantifier", "equivalent_control", "unsafe_ellipsis",
})
COUNTABLE_EXAMPLES = frozenset({"mel", "pal", "dol", "te", "nol"})
SUBJECT_PAIRS = (("mi", "ti"), ("mi", "ni"), ("ti", "ni"))
SUBJECTS = ("mi", "ti")
ID = re.compile(r"[a-z][a-z0-9_]{1,63}\Z")


def _validate_seeds(seeds: dict, lex: Lexicon) -> None:
    if not isinstance(seeds, dict) or seeds.get("schema_version") != "veka.communication-domains.v07":
        raise VekaError("unknown communication domain schema")
    if seeds.get("status") != "curated_synthetic_templates_not_human_conversation":
        raise VekaError("corpus provenance must be synthetic and explicit")
    used = set()
    for category, valency in (("transitive", "transitive"), ("intransitive", "intransitive")):
        rows = seeds.get(category)
        if not isinstance(rows, list) or not rows:
            raise VekaError("missing curated " + category + " domains")
        for item in rows:
            if not isinstance(item, dict):
                raise VekaError("malformed domain")
            name, verb = item.get("id"), item.get("verb")
            if not isinstance(name, str) or not ID.fullmatch(name) or name in used:
                raise VekaError("duplicate or unsafe domain identifier")
            used.add(name)
            if verb not in lex or lex[verb].pos != "verb" or lex[verb].valency != valency:
                raise VekaError("domain verb has wrong lexical valency: " + str(verb))
            if category == "transitive":
                noun = item.get("object")
                if noun not in lex or lex[noun].pos != "noun":
                    raise VekaError("transitive domain requires a lexical noun")
                if type(item.get("countable")) is not bool:
                    raise VekaError("domain must declare whether quantities are plausible")
                if item["countable"] and noun not in COUNTABLE_EXAMPLES:
                    raise VekaError("quantity domain not curated as countable: " + noun)
                if type(item.get("recipient", False)) is not bool:
                    raise VekaError("recipient flag must be boolean")
            elif set(item) != {"id", "verb"}:
                raise VekaError("intransitive domain has unknown fields")
    places = seeds.get("locations")
    if (not isinstance(places, list) or len(places) != 2
            or len(set(places)) != 2 or any(not isinstance(x, str)
            or x not in lex or lex[x].pos != "noun"
            or lex[x].domain != "places" for x in places)):
        raise VekaError("two different lexical place nouns are required")


def generate_cases(seeds: dict, lex: Lexicon) -> list[dict]:
    """Build reproducible contrast and negative-control clauses from audited seeds."""
    _validate_seeds(seeds, lex)
    result = []

    def add(category: str, suffix: str, a: str, b: str, differences: list[str],
            **extra) -> None:
        result.append({
            "id": category + "_" + suffix, "category": category,
            "provenance": "synthetic_template", "critical": category != "equivalent_control",
            "a": a, "b": b, "expected_differences": differences, **extra,
        })

    for item in seeds["transitive"]:
        stem, verb, obj = item["id"], item["verb"], item["object"]
        for left, right in SUBJECT_PAIRS:
            add("role_reversal", stem + "_" + left + "_" + right,
                f"{left} pa {verb} {obj}.", f"{right} pa {verb} {obj}.", ["subject"])
        for subject in SUBJECTS:
            s = subject + "_" + stem
            clause = f"{subject} pa {verb} {obj}"
            add("negation", s, clause + ".", f"{subject} pa ne {verb} {obj}.", ["negative"])
            add("tense", s, clause + ".", f"{subject} fu {verb} {obj}.", ["tense"])
            add("polar_question", s, clause + ".", clause + " ke.", ["question"])
            if item["countable"]:
                add("quantity", s, f"{clause} wen ran.", f"{clause} wen kuk.",
                    ["object", "object_quantity"])
            if item.get("recipient", False):
                add("recipient", s, clause + " to ti.", clause + " to ni.", ["recipient"])
        add("equivalent_control", stem,
            f"Mi pa {verb} {obj}.", f"mi pa {verb} {obj}", [])

    for item in seeds["intransitive"]:
        stem, verb = item["id"], item["verb"]
        for subject in SUBJECTS:
            s = subject + "_" + stem
            clause = f"{subject} pa {verb}"
            add("location", s, clause + " en " + seeds["locations"][0] + ".",
                clause + " en " + seeds["locations"][1] + ".", ["location"])
            add("negation", s, clause + ".", f"{subject} pa ne {verb}.", ["negative"])
            add("unsafe_ellipsis", s, clause + ".", f"Pa {verb}.",
                ["compressed"], unique_subject=subject, ambiguous_subjects=["mi", "ti"])
        add("quantifier", stem, f"Al ren pa {verb}.", f"Kis ren pa {verb}.",
            ["subject", "subject_quantifier"])
        add("equivalent_control", stem + "_intrans",
            f"Mi pa {verb}.", f"mi pa {verb}", [])
    return result


def validate_cases(cases: list[dict], lex: Lexicon) -> dict[str, int]:
    """Reject changed meanings, malformed controls, hidden context or duplicates."""
    if not isinstance(cases, list) or not cases:
        raise VekaError("empty communication benchmark corpus")
    seen: set[str] = set()
    categories: Counter[str] = Counter()
    for case in cases:
        if not isinstance(case, dict):
            raise VekaError("malformed communication case")
        ident = case.get("id")
        category = case.get("category")
        if (not isinstance(ident, str) or not ID.fullmatch(ident) or ident in seen
                or category not in CATEGORIES):
            raise VekaError("invalid or duplicate communication case")
        seen.add(ident)
        if (case.get("provenance") != "synthetic_template"
                or type(case.get("critical")) is not bool
                or case["critical"] != (category != "equivalent_control")):
            raise VekaError("misleading benchmark provenance or consequence flag")
        expected = case.get("expected_differences")
        if (not isinstance(expected, list) or not all(isinstance(x, str) for x in expected)
                or len(expected) != len(set(expected))):
            raise VekaError("invalid semantic difference contract")
        a, b = case.get("a"), case.get("b")
        if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
            raise VekaError("empty benchmark utterance")
        if category == "unsafe_ellipsis":
            unique = case.get("unique_subject")
            ambiguous = case.get("ambiguous_subjects")
            if (unique not in ("mi", "ti")
                    or not isinstance(ambiguous, list) or len(ambiguous) < 2
                    or len(set(ambiguous)) != len(ambiguous)
                    or unique not in ambiguous
                    or any(x not in ("mi", "ti", "ni") for x in ambiguous)):
                raise VekaError("ellipsis control lacks competing overt referents")
            explicit = parse(a, lex, strict=True)
            recovered = parse(b, lex, context=Discourse(subjects=(unique,)), strict=False)
            if (explicit.get("subject") != unique or not recovered.get("compressed")
                    or explicit != dict(recovered, compressed=False)
                    or expected != ["compressed"]):
                raise VekaError("unique-context ellipsis changes structural meaning")
            try:
                parse(b, lex, context=Discourse(subjects=tuple(ambiguous)), strict=False)
            except VekaError:
                pass
            else:
                raise VekaError("ambiguous compact utterance was incorrectly accepted")
            # Overt explicit wording must not depend on resolving the ambiguous context.
            if parse(a, lex, context=Discourse(subjects=tuple(ambiguous)), strict=True) != explicit:
                raise VekaError("explicit wording depends on hidden context")
        else:
            if "unique_subject" in case or "ambiguous_subjects" in case:
                raise VekaError("context-only metadata on ordinary contrast")
            left, right = parse(a, lex, strict=True), parse(b, lex, strict=True)
            changed = sorted(k for k in left if left[k] != right[k])
            if changed != sorted(expected):
                raise VekaError(f"unexpected meaning differences in {ident}: {changed}")
            if category == "equivalent_control" and (changed or a == b):
                raise VekaError("equivalent control must differ in harmless surface form")
            if category != "equivalent_control" and not changed:
                raise VekaError("contrast does not change any meaning feature")
        categories[category] += 1
    return dict(sorted(categories.items()))


def audit_communication(cases: list[dict], lex: Lexicon, profile: str = "tonal") -> dict:
    categories = validate_cases(cases, lex)
    canonical = json.dumps(cases, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": SCHEMA,
        "profile": profile,
        "scenarios": len(cases),
        "verified": len(cases),
        "structural_failures": 0,
        "contrast_pairs": sum(n for c, n in categories.items()
                              if c not in ("equivalent_control", "unsafe_ellipsis")),
        "equivalent_controls": categories.get("equivalent_control", 0),
        "unsafe_ellipsis_rejections": categories.get("unsafe_ellipsis", 0),
        "critical_scenarios": sum(n for c, n in categories.items()
                                  if c != "equivalent_control"),
        "by_category": categories,
        "corpus_sha256": hashlib.sha256(canonical).hexdigest(),
        "synthetic_template_data": True,
        "human_participants": 0,
        "human_accuracy": None,
        "acoustic_validation": False,
        "warning": "Parser-consistency research only. No human comprehension, "
                   "spoken speed, natural-corpus representativeness, or acoustic risk measured.",
    }
