"""Read-only, Globasa-inspired concept review for Veka's existing research queue.

The Globasa lexical-development process motivates three questions: can an
existing expression already do the job, what donor/sense evidence exists, and
would the proposed surface be confusable? This is a structural checklist, NOT
an automatic source selector, acoustic model, or vocabulary adoption tool.
"""
from __future__ import annotations

from .core import Lexicon, VekaError
from .global_comprehension import EVIDENCE_FIELDS, audit_global_candidates
from .international import audit_candidates
from .international_plan import build_international_plan
from .phonology import edit_distance
from .semantic_families import describe_family
from .learner_locales import LANGUAGES, localized_gloss
from .source_leads import audit_screening_leads

VERSION = "veka.root-review.v01"


def near_spelling_forms(candidate: str, forms, *, limit: int = 20) -> list[dict]:
    """Find identical and one-edit undelimited *written* surfaces.

    Compound hyphens are not audible. Character-level Levenshtein is a
    deliberately weak proxy: spelling similarity is not phonetic similarity.
    """
    if not isinstance(candidate, str):
        raise VekaError("candidate form must be text")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise VekaError("near pair limit must be positive")
    if not candidate:
        return []
    surface = candidate.replace("-", "").casefold()
    result = []
    for form in sorted(set(forms)):
        if not isinstance(form, str):
            raise VekaError("comparison forms must be text")
        if form == candidate:
            continue
        other = form.replace("-", "").casefold()
        if abs(len(surface) - len(other)) > 1:
            continue
        edits = edit_distance(surface, other)
        if edits <= 1:
            result.append({
                "form": form,
                "edits": edits,
                "silent_hyphen_ambiguity": edits == 0 and form != candidate,
            })
    return sorted(result, key=lambda x: (x["edits"], x["form"]))[:limit]


def build_root_review(concept_id: str, candidates: list[dict], lex: Lexicon,
                      priorities: list[dict], evidence: list[dict], *,
                      leads: list[dict] | None = None) -> dict:
    """Join existing audited Veka research instead of creating another ranking.

    Reviewer flags are assertions; even a verified semantic attestation does
    not establish independent *etymological origins*, recognition or efficacy.
    """
    if not isinstance(concept_id, str) or not concept_id.strip():
        raise VekaError("concept id is required")
    # Existing plan enforces canonical meaning identity, queue/priorities
    # completeness, candidate phonotactics and silent-hyphen collisions.
    plan = build_international_plan(candidates, lex, priorities, evidence)
    queue = {item["concept_id"]: item for item in plan["queue"]}
    if concept_id not in queue:
        raise VekaError(f"unknown international root concept: {concept_id}")
    screened = audit_screening_leads(leads if leads is not None else [], candidates)
    # Validate all source records against the structural candidate contracts.
    global_report = audit_global_candidates(candidates, lex, evidence)
    structural = audit_candidates(candidates, lex)
    by_concept = {row["concept_id"]: row for row in structural["candidates"]}
    item = queue[concept_id]
    core = lex[item["core_form"]]
    family = describe_family(core.form, lex, candidates, limit=5, include_cues=False)
    candidate_form = item["candidate_form"]
    candidate_structural = by_concept.get(concept_id)
    sources = sorted((
        {
            "language": row["language"],
            "language_family": row["language_family"],
            "language_branch": row["language_branch"],
            "attested_form": row["attested_form"],
            "source_url": row["source_url"],
            "semantic_reviewer": row["semantic_reviewer"],
            "attestation_verified_claimed": row["attestation_verified"] == "yes",
            "semantic_equivalent_claimed": row["semantic_equivalent"],
            "notes": row["notes"],
        }
        for row in evidence if row["concept_id"] == concept_id
    ), key=lambda row: (row["language"].casefold(), row["attested_form"]))
    other_forms = set(lex)
    other_forms.update(r["candidate_form"] for r in plan["queue"]
                       if r["candidate_form"] and r["structural_status"] == "structurally_testable")
    nearest = (near_spelling_forms(candidate_form, other_forms)
               if candidate_form else None)
    if nearest is not None:
        for near in nearest:
            near["accepted_vocabulary"] = near["form"] in lex
    arms = [{"condition": "core", "form": core.form, "accepted_vocabulary": True}]
    if candidate_form:
        arms.append({"condition": "candidate", "form": candidate_form,
                     "accepted_vocabulary": False})
    audit = global_report["candidates"].get(concept_id, {})
    glosses = {}
    for language in LANGUAGES:
        gloss, used_language = localized_gloss(core.form, core.gloss, language)
        glosses[language] = {
            "gloss": gloss, "gloss_language": used_language,
            "status": "curated_word_gloss_not_full_translation",
        }
    return {
        "schema_version": VERSION,
        "concept_id": concept_id,
        "canonical": {
            "form": core.form, "gloss": core.gloss, "pos": core.pos,
            "valency": core.valency, "accepted_vocabulary": True,
            "expressible_with_existing_root": True,
            "compound_examples": family["canonical_compounds"],
            "affected_compounds": item["existing_compounds_affected"],
        },
        "candidate": {
            "form": candidate_form,
            "status": item["structural_status"],
            "structural_reasons": item["structural_reasons"],
            "extra_syllables": item["added_syllables_vs_core"],
            "undelimited_surface_collisions": item["spoken_surface_collisions"],
            "spelling_near_pairs": nearest,
            "structural_screen_passed": bool(candidate_structural and
                                             candidate_structural["status"] == "structurally_testable" and
                                             not item["spoken_surface_collisions"]),
            "written_near_pairs_are_acoustic_evidence": False,
            "recognized_vocabulary": False,
        },
        "etymology": {
            "attested_language_families_claimed": audit.get("verified_families", 0),
            "verified_independent_origins": None,
            "review_status": "not_established",
            "note": "Language families are not independent borrowing histories; donor senses and loan chains require manual source review.",
        },
        "source_records": sources,
        "source_leads": [lead for lead in screened if lead["concept_id"] == concept_id],
        "learner_glosses": glosses,
        "review_gates": {
            "already_expressible": True,
            "meaning_and_false_friends_reviewed": False,
            "screening_leads_independently_reviewed": False,
            "etymological_independence_reviewed": False,
            "phonological_listening_tested": False,
            "human_recognition_measured": False,
            "human_retention_measured": False,
        },
        "comparison_arms": arms,
        "next_research_action": item["next_action"],
        "exposure_tier_is_editorial": True,
        "human_benefit_established": False,
        "adoption_authorized": False,
        "canonical_changes": 0,
        "warning": (
            "Do not copy a Globasa word as automatically verified Veka vocabulary. "
            "Candidate forms, source assertions, derived examples and spelling pairs "
            "do not prove semantic equivalence, independent etymology, acoustic clarity "
            "or human comprehension. No canonical changes are made."
        ),
    }


def format_root_review(report: dict, *, language: str = "en") -> str:
    """Print a readable learner/researcher card with unambiguous status tags."""
    if language not in LANGUAGES:
        raise VekaError(f"unsupported root review language: {language}")
    core, draft = report["canonical"], report["candidate"]
    local = report["learner_glosses"][language]
    lines = [
        f'{report["concept_id"]}: {core["gloss"]} ({core["pos"]})',
        f'Veka Core: {core["form"]} (accepted; already expresses this concept)',
        f'Learner gloss ({language}): {local["gloss"]} '
        f'[source language: {local["gloss_language"]}; editorial word gloss]',
    ]
    if draft["form"]:
        lines.append(
            f'Candidate: {draft["form"]} (unverified; {draft["status"]}; '
            f'{draft["extra_syllables"]:+d} syllables vs Core)'
        )
        if draft["undelimited_surface_collisions"]:
            lines.append("Undelimited surface collisions: " +
                         ", ".join(draft["undelimited_surface_collisions"]))
        if draft["spelling_near_pairs"]:
            lines.append("Written near-pairs (not acoustic evidence): " +
                         ", ".join(item["form"] for item in draft["spelling_near_pairs"]))
    else:
        lines.append("Candidate: none proposed; no new word invented")
    lines.extend([
        f'Existing compounds affected: {core["affected_compounds"]}',
        f'Source records: {len(report["source_records"])} '
        '(reviewer assertions, not recognition evidence)',
        f'unreviewed source leads: {len(report["source_leads"])} '
        '(not verified attestations)',
        'Etymological borrowing-chain independence: not established',
        'Compare: ' + ' vs '.join(f'{arm["condition"]} {arm["form"]}'
                                 for arm in report["comparison_arms"]),
        f'Next: {report["next_research_action"]}',
        'No human recognition or spoken listening evidence; '
        'no canonical vocabulary changes or adoption approval.',
    ])
    if report["source_leads"]:
        lines.append("Source-screening forms (none independently reviewed):")
        for lead in report["source_leads"]:
            lines.append(
                f'  {lead["language"]}: {lead["sourced_form"]} '
                f'({lead["relation_to_draft"]}; {lead["review_status"]})'
            )
    return "\n".join(lines)
