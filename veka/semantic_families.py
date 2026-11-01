"""Read-only semantic families; family membership does not imply synonymy.

No canonical word, parser rule, or lexicalized sense is added by this tool.
"""
from __future__ import annotations
from .core import Lexicon, VekaError
from .extended import DERIVATIONS, derive
from .international import audit_candidates
from .profiles import DATA


def _active_root(canonical_form: str, lex: Lexicon, canonical: Lexicon) -> str:
    """Resolve frozen root identities across tonal / toneless profiles."""
    if canonical_form not in canonical or canonical[canonical_form].kind != "root":
        raise VekaError("compound references an unknown canonical root")
    original = canonical[canonical_form]
    if canonical_form in lex and lex[canonical_form].kind == "root" and (
        lex[canonical_form].gloss, lex[canonical_form].pos
    ) == (original.gloss, original.pos):
        return canonical_form
    matches = [
        k for k, e in lex.items() if e.kind == "root"
        and (e.gloss, e.pos) == (original.gloss, original.pos)
    ]
    if len(matches) != 1:
        raise VekaError("cannot map root unambiguously across profiles")
    return matches[0]


def describe_family(
    form: str, lex: Lexicon, candidates: list[dict], *,
    limit: int = 12, include_cues: bool = True,
) -> dict:
    """Return structural relatives of an accepted Veka word, read-only."""
    if not isinstance(form, str) or form not in lex:
        raise VekaError("family lookup requires an accepted Veka headword")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise VekaError("family limit must be between 1 and 100")

    canonical = Lexicon.from_csv(DATA / "lexicon.csv")
    entry = lex[form]
    base_form = _active_root(entry.head, lex, canonical) if entry.kind == "compound" else form
    base = lex[base_form]
    if base.kind != "root":
        raise VekaError("family base must be a primitive root")
    canonical_matches = [
        k for k, e in canonical.items() if e.kind == "root"
        and (e.gloss, e.pos) == (base.gloss, base.pos)
    ]
    if len(canonical_matches) != 1:
        raise VekaError("root cannot be uniquely matched to the canonical contract")
    original_form = canonical_matches[0]
    interpretation = None
    if entry.kind == "compound":
        if entry.head not in canonical or entry.modifier not in canonical:
            raise VekaError("compound decomposition missing")
        interpretation = canonical[entry.head].gloss + " + " + canonical[entry.modifier].gloss

    result = {
        "queried_form": form,
        "base_form": base_form,
        "base_gloss": base.gloss,
        "base_pos": base.pos,
        "lexeme_id": "core:" + original_form,
        "root_is_canonical": base_form == original_form,
        "canonical_root_concept_preserved": True,
        "family_type": "atomic",
        "canonical_entry_count": 1,
        "canonical_compounds": [],
        "canonical_compound_total": 0,
        "family_truncated": False,
        "experimental_derivations": [],
        "compound_interpretation": interpretation,
        "silent_hyphen": entry.kind == "compound",
        "lexicalized_distinct_sense": False,
        "international_association": None,
        "human_recognition_measured": False,
        "sense_disambiguation_verified": False,
        "meaning_policy": "Structural relations and English glosses; not independently verified senses or synonyms.",
        "canonical_vocabulary_changed": False,
    }
    if base.pos in ("noun", "adjective"):
        relation = "noun_head" if base.pos == "noun" else "adjective_modifier"
        hits = [
            e for e in lex.values() if e.kind == "compound"
            and (e.head == original_form if base.pos == "noun" else e.modifier == original_form)
        ]
        hits.sort(key=lambda e: e.form)
        for item in hits[:limit]:
            if item.head not in canonical or item.modifier not in canonical:
                raise VekaError("invalid canonical compound decomposition")
            result["canonical_compounds"].append({
                "form": item.form,
                "relation": relation,
                "head": item.head,
                "modifier": item.modifier,
                "compositional_gloss": canonical[item.head].gloss + " + " + canonical[item.modifier].gloss,
                "silent_hyphen": True,
                "accepted_vocabulary": True,
                "distinct_lexicalized_sense": False,
            })
        result["canonical_compound_total"] = len(hits)
        result["family_truncated"] = len(hits) > limit
        result["canonical_entry_count"] += len(hits)
        if hits:
            result["family_type"] = "canonical_compounds"

    if base.pos == "verb":
        result["family_type"] = "event_derivations"
        for suffix in DERIVATIONS:
            try:
                item = derive(f"{base_form}-{suffix}", lex)
            except VekaError:
                continue  # undefined valency/phonotactics: not a valid derivative
            result["experimental_derivations"].append({
                "form": item["form"],
                "operation": item["operation"],
                "pos": item["pos"],
                "valency": item["valency"],
                "semantic_contract": item["semantic_contract"],
                "accepted_vocabulary": False,
                "status": "opt_in_0_5_extension",
            })

    if include_cues:
        report = audit_candidates(candidates, canonical)
        allowed = {row["concept_id"] for row in report["candidates"]
                   if row["status"] == "structurally_testable"}
        for item in candidates:
            if item["concept_id"] in allowed and (
                item["gloss"], item["pos"]
            ) == (base.gloss, base.pos):
                result["international_association"] = {
                    "concept_id": item["concept_id"],
                    "reference_spelling": item["reference_spelling"],
                    "draft_form": item["candidate_form"],
                    "status": "unverified_draft",
                    "accepted_vocabulary": False,
                    "human_recognition_measured": False,
                }
                break
    return result


def format_semantic_family(family: dict) -> str:
    lines = [
        f'{family["base_form"]} [{family["base_gloss"]}]: {family["family_type"]}',
        "Family relationships are compositional, not synonymous or human validated.",
    ]
    if family["compound_interpretation"] is not None:
        lines.append(
            f'Queried compound: {family["queried_form"]} = {family["compound_interpretation"]} '
            "(silent hyphen; not a distinct lexicalized sense)"
        )
    if family["canonical_compounds"]:
        lines.append("Established transparent compounds:")
        for item in family["canonical_compounds"]:
            lines.append(f'  {item["form"]} = {item["compositional_gloss"]}')
        if family["family_truncated"]:
            lines.append(f'  ... {family["canonical_compound_total"]} total')
    if family["experimental_derivations"]:
        lines.append("Experimental event derivations (NOT accepted core Veka):")
        for item in family["experimental_derivations"]:
            lines.append(f'  {item["form"]}: {item["operation"]}')
    if family["international_association"]:
        cue = family["international_association"]
        lines.append(
            f'Illustrative international cue (NOT accepted Veka): '
            f'{cue["reference_spelling"]} / {cue["draft_form"]}'
        )
    return "\n".join(lines)
