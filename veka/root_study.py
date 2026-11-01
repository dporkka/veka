"""Balanced, blinded, language-stratified international-root study planning.

Each participant sees either the canonical root or experimental international
form for a meaning, not both. Neither recruitment nor human data are fabricated.
"""
from __future__ import annotations

import hashlib
import random
from collections import defaultdict

from .cohort_plan import PSEUDONYM, ROSTER_FIELDS
from .core import Lexicon, VekaError
from .international import audit_candidates


def plan_root_cohorts(candidates: list[dict], lex: Lexicon,
                      roster: list[dict], *, seed: int = 20261101) -> dict:
    """Prepare 8-word cross-language randomized comparison; no responses."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise VekaError("study seed must be an integer")
    audited = audit_candidates(candidates, lex)
    valid = [row for row in audited["candidates"]
             if row["status"] == "structurally_testable"]
    if not valid or audited["rejected_forms"] or len(valid) % 2:
        raise VekaError("study needs an even number of valid experimental words")
    if not roster:
        raise VekaError("a researcher-supplied pseudonymous roster is required")

    groups, seen = defaultdict(list), set()
    for row in roster:
        if (not isinstance(row, dict) or set(row) != set(ROSTER_FIELDS)
                or any(not isinstance(row[k], str) for k in ROSTER_FIELDS)):
            raise VekaError("invalid or private roster fields")
        participant, stratum = row["participant_id"], row["background_stratum"]
        if not PSEUDONYM.fullmatch(participant) or participant in seen:
            raise VekaError("invalid or repeated participant pseudonym")
        if (not 2 <= len(stratum) <= 64 or stratum != stratum.strip()
                or stratum[0] in "=+-@" or any(ord(ch) < 32 or ch in "/\\"
                                                 for ch in stratum)):
            raise VekaError("unsafe language-background stratum")
        seen.add(participant)
        groups[stratum].append(participant)
    if any(len(people) < 2 or len(people) % 2 for people in groups.values()):
        raise VekaError("each language-background stratum requires even participants")

    # Meaning order is independently randomized from participant presentation
    # order. Opposite arms within every stratum reverse conditions per item.
    order = list(valid)
    random.Random(f"{seed}:root-concept-slots").shuffle(order)
    participants, keys, assignments, strata = {}, [], [], {}
    for stratum in sorted(groups):
        ids = sorted(groups[stratum])
        random.Random(f"{seed}:root-stratum:{stratum}").shuffle(ids)
        half = len(ids) // 2
        strata[stratum] = {"arm_0": half, "arm_1": half}
        for idx, participant in enumerate(ids):
            arm = int(idx >= half)
            sheet = []
            for position, concept in enumerate(order):
                condition = "core" if (position + arm) % 2 == 0 else "candidate"
                token = concept["core_form" if condition == "core" else "candidate_form"]
                opaque = hashlib.sha256(
                    f"V12:{seed}:{participant}:{concept['concept_id']}".encode()
                ).hexdigest()[:16]
                trial = f"V12-{opaque}"
                sheet.append({
                    "participant_id": participant, "trial_id": trial,
                    "presented_form": token, "response_gloss": "",
                    "response_ms": "", "prior_exposure": "",
                    "presentation_modality": "written",
                })
                keys.append({
                    "participant_id": participant, "trial_id": trial,
                    "concept_id": concept["concept_id"],
                    "target_gloss": concept["gloss"],
                    "condition": condition,
                    "presented_form": token,
                    "background_stratum": stratum,
                })
            random.Random(f"{seed}:root-order:{participant}").shuffle(sheet)
            participants[participant] = sheet
            assignments.append({
                "participant_id": participant, "background_stratum": stratum,
                "arm": str(arm), "seed": str(seed),
            })

    return {
        "summary": {
            "schema_version": "veka.root-study.v12",
            "planned_participants": len(participants),
            "trials_per_participant": len(valid),
            "background_strata": strata,
            "human_data_collected": False,
            "recognition_measured": False,
            "adoption_authorized": False,
            "canonical_vocabulary_modified": False,
            "warning": (
                "Study sheets are plans, not participants or results. Independently "
                "recruit and consent participants, prespecify acceptable senses and "
                "analyse actual first-sight accuracy, training/retention and repairs. "
                "Written recognition is not evidence of acoustic comprehension."
            ),
        },
        "participants": dict(sorted(participants.items())),
        "researcher_keys": sorted(keys, key=lambda r: (r["participant_id"], r["trial_id"])),
        "assignments": sorted(assignments, key=lambda r: r["participant_id"]),
    }
