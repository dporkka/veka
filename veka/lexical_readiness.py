"""Evidence-first lexical research backlog; intentionally no adoption mechanism.

Synthetic tests and reviewer-entered attestations do not establish human
recognition. This report prioritizes the *next research action* per concept,
not whether to replace the published Veka dictionary.
"""
from __future__ import annotations

from collections import Counter

from .core import Lexicon, VekaError
from .international import audit_candidates
from .global_comprehension import audit_global_candidates, summarize_global_trials

# Research sampling policy, NOT evidence of global recognition or an adoption bar.
MIN_INDEPENDENT_FAMILIES_FOR_PILOT = 2
MIN_BALANCED_FAMILIES_FOR_REVIEW = 2

ACTION_PRIORITY = {
    "investigate_critical_errors": 0,
    "manual_preregistered_review": 1,
    "collect_balanced_human_trials": 2,
    "verify_cross_family_attestations": 3,
    "repair_candidate": 4,
    "propose_candidate": 5,
}


def build_lexical_readiness(candidates: list[dict], lex: Lexicon,
                            evidence: list[dict], trials: list[dict]) -> dict:
    """Join existing structural, family and descriptive-trial contracts.

    The trial parser validates numeric inputs but cannot authenticate human
    participants, blinding, recordings, consent or randomization. None of the
    stages below is a release/adoption decision.
    """
    structure = audit_candidates(candidates, lex)
    global_audit = audit_global_candidates(candidates, lex, evidence)
    by_form = {item["concept_id"]: item for item in structure["candidates"]}
    vetted = global_audit["candidates"]
    mapping = {cid: item["candidate_form"] for cid, item in vetted.items()}
    if not mapping and trials:
        raise VekaError("cannot score trials without structurally valid candidates")
    observations = (summarize_global_trials(trials, mapping) if mapping else
                    {"observed": False, "by_concept": {}})
    pending = Counter(r["concept_id"] for r in global_audit["review_queue"])

    items = []
    for row in candidates:
        cid = row["concept_id"]
        structural = by_form.get(cid)
        attested = vetted.get(cid, {})
        observed = observations["by_concept"].get(cid, {})
        by_condition = observed.get("conditions", {})
        core = by_condition.get("core", {})
        candidate = by_condition.get("candidate", {})
        critical = candidate.get("critical_errors", 0)
        balanced = observed.get("balanced_families", [])
        families = attested.get("verified_families", 0)

        if not structural:
            action = "propose_candidate"
        elif structural["status"] == "rejected":
            action = "repair_candidate"
        elif critical:
            action = "investigate_critical_errors"
        elif families < MIN_INDEPENDENT_FAMILIES_FOR_PILOT:
            action = "verify_cross_family_attestations"
        elif len(balanced) < MIN_BALANCED_FAMILIES_FOR_REVIEW:
            action = "collect_balanced_human_trials"
        else:
            action = "manual_preregistered_review"

        items.append({
            "concept_id": cid,
            "gloss": row["gloss"],
            "core_form": row["core_form"],
            "candidate_form": structural["candidate_form"] if structural else None,
            "structural_status": structural["status"] if structural else "not_proposed",
            "structural_reasons": structural["reasons"] if structural else [],
            "added_syllables_vs_core": structural["added_syllables_vs_core"] if structural else None,
            "verified_families": families,
            "family_labels": attested.get("family_labels", []),
            "pending_attestation_reviews": pending[cid],
            "balanced_trial_families": balanced,
            "core_trials": core.get("trials", 0),
            "candidate_trials": candidate.get("trials", 0),
            "candidate_critical_errors": critical,
            "human_benefit_established": False,
            "next_action": action,
        })

    items.sort(key=lambda x: (ACTION_PRIORITY[x["next_action"]], x["concept_id"]))
    return {
        "schema_version": "veka.lexical-readiness.v09",
        "candidate_count": len(items),
        "counts": dict(sorted(Counter(x["next_action"] for x in items).items())),
        "observed_trial_rows": len(trials),
        "verified_attestations_claimed": global_audit["verified_attestations"],
        "canonical_changes": 0,
        "adoption_authorized": False,
        "candidates": items,
        "warning": (
            "Attestation labels are reviewer assertions; participant rows are not independently "
            "authenticated. Two-family coverage is only a research sampling heuristic. "
            "Structural suitability and descriptive trials cannot authorize a vocabulary change; "
            "independent human testing, preregistered analysis and critical-error review are required."
        ),
    }
