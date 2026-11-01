"""Veka 0.7 opt-in international cognate pilot; never modifies canonical vocabulary.

Mechanical eligibility is not donor provenance, human recognition, or acoustic safety.
"""
from __future__ import annotations

import csv
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path

from .core import Lexicon, VekaError, syllabify, validate_word
from .international import audit_evidence, summarize_recognition_scores
from .international import FORBIDDEN_SEGMENTS

FIELDS = ("concept_id", "gloss", "pos", "category", "core_form",
          "candidate_form", "control_form", "priority", "status", "note")
CATEGORIES = {"addition", "replacement"}


def read_pilot(path: str | Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise VekaError("invalid cognate pilot CSV headers")
        return list(reader)


def audit_pilot(rows: list[dict], lex: Lexicon,
                evidence: list[dict] | None = None) -> dict:
    if not rows:
        raise VekaError("cognate pilot is empty")
    seen_concepts = set()
    seen_forms = set()
    seen_controls = set()
    seen_priorities = set()
    counts = Counter()
    assessments = []
    for row in rows:
        if not set(FIELDS).issubset(row) or any(not isinstance(row[k], str) for k in FIELDS):
            raise VekaError("incomplete cognate candidate row")
        cid = row["concept_id"]
        form = row["candidate_form"]
        category = row["category"]
        if (not cid or cid in seen_concepts or not form or form in seen_forms
                or category not in CATEGORIES
                or row["status"] != "unverified_draft"
                or not row["gloss"].strip() or not row["note"].strip()
                or row["pos"] not in ("noun", "adjective", "verb")):
            raise VekaError(f"invalid or duplicate cognate candidate: {cid}")
        if not row["priority"].isascii() or not row["priority"].isdecimal():
            raise VekaError("candidate priority must be a positive integer")
        priority = int(row["priority"])
        if priority < 1 or priority in seen_priorities:
            raise VekaError("candidate priority is duplicated or invalid")
        seen_priorities.add(priority)
        seen_concepts.add(cid)
        seen_forms.add(form)
        core = row["core_form"]
        control = row["control_form"]
        if category == "addition":
            if core or any(e.gloss == row["gloss"] and e.pos == row["pos"]
                           for e in lex.values() if e.kind == "root"):
                raise VekaError("addition overlaps an existing core meaning")
            if not control or control in seen_controls or control == form:
                raise VekaError("addition needs a unique nonce control form")
            seen_controls.add(control)
        else:
            if control:
                raise VekaError("replacement must not contain nonce control")
            if (core not in lex or lex[core].kind != "root"
                    or (lex[core].gloss, lex[core].pos)
                    != (row["gloss"], row["pos"])):
                raise VekaError("replacement does not preserve a canonical root meaning")
        reasons = []
        parts = []
        if not validate_word(form):
            reasons.append("invalid Veka phonotactics")
        else:
            parts = syllabify(form)
            if not 2 <= len(parts) <= 8:
                reasons.append("experiment supports 2 to 8 syllables")
            if any(any(c in "áéíóú" for c in p) for p in parts):
                reasons.append("loan trial must be toneless")
            if any(p in FORBIDDEN_SEGMENTS for p in parts):
                reasons.append("contains a protected grammar or pronoun syllable")
        if form in lex:
            reasons.append("collides with canonical lexicon")
        if category == "addition":
            if not validate_word(control):
                reasons.append("invalid nonce-control phonotactics")
            else:
                control_parts = syllabify(control)
                if len(control_parts) != len(parts):
                    reasons.append("nonce control must match candidate syllable count")
                if any(p in FORBIDDEN_SEGMENTS for p in control_parts):
                    reasons.append("nonce control contains protected syllable")
                if any(any(c in "áéíóú" for c in p) for p in control_parts):
                    reasons.append("nonce control must be toneless")
            if control in lex:
                reasons.append("nonce control collides with canonical lexicon")
        counts[category] += 1
        assessments.append({
            "concept_id": cid, "category": category, "gloss": row["gloss"],
            "current_root": core or None, "candidate_form": form,
            "candidate_syllables": len(parts),
            "core_syllables": 1 if core else None,
            "status": "rejected" if reasons else "structurally_testable",
            "reasons": reasons,
        })
    if seen_controls & seen_forms:
        raise VekaError("nonce controls and international candidates overlap")
    donor = audit_evidence(evidence or [], rows)
    return {
        "schema_version": "veka.cognate-pilot.v07",
        "candidate_count": len(rows),
        "categories": dict(counts),
        "rejected_count": sum(r["status"] == "rejected" for r in assessments),
        "structurally_testable": sum(r["status"] == "structurally_testable" for r in assessments),
        "adopted_count": 0,
        "verified_evidence_records": donor["verified_records"],
        "evidence": donor,
        "recognition_measured": False,
        "audio_recorded": False,
        "assessments": assessments,
        "warning": "Draft spellings are not donor attestations. No candidate is canonical.",
    }


def make_pilot_manifest(rows: list[dict], lex: Lexicon, participant_id: str,
                        *, seed: int = 20261101, arm: int) -> tuple[list[dict], list[dict]]:
    if not isinstance(participant_id, str) or not participant_id.strip():
        raise VekaError("participant pseudonym is required")
    if isinstance(arm, bool) or arm not in (0, 1):
        raise VekaError("arm must be 0 or 1")
    audit = audit_pilot(rows, lex)
    if audit["rejected_count"]:
        raise VekaError("pilot contains structurally rejected candidate forms")
    replacements = sorted(r["concept_id"] for r in rows if r["category"] == "replacement")
    if len(replacements) < 2 or len(replacements) % 2:
        raise VekaError("pilot needs a positive even number of core replacement trials")
    random.Random(f"assignment:{seed}").shuffle(replacements)
    core_set = set(replacements[:len(replacements)//2])
    additions = sorted(r["concept_id"] for r in rows if r["category"] == "addition")
    if len(additions) < 2 or len(additions) % 2:
        raise VekaError("pilot needs a positive even number of addition trials")
    random.Random(f"nonce-assignment:{seed}").shuffle(additions)
    nonce_set = set(additions[:len(additions)//2])
    visible, key = [], []
    for row in rows:
        category = row["category"]
        core = category == "replacement" and ((row["concept_id"] in core_set) != bool(arm))
        nonce = category == "addition" and ((row["concept_id"] in nonce_set) != bool(arm))
        condition = "core" if core else "nonce_control" if nonce else "international"
        token = (row["core_form"] if core else row["control_form"] if nonce
                 else row["candidate_form"])
        trial_id = "C07-" + hashlib.sha256(
            f"{seed}:{participant_id}:{row['concept_id']}".encode("utf-8")
        ).hexdigest()[:16]
        visible.append({
            "participant_id": participant_id, "trial_id": trial_id,
            "presented_form": token, "response_gloss": "",
            "response_ms": "", "prior_exposure": "",
        })
        key.append({
            "participant_id": participant_id, "trial_id": trial_id,
            "concept_id": row["concept_id"], "target_gloss": row["gloss"],
            "category": category, "condition": condition,
            "presented_form": token, "status": "unverified_draft",
        })
    order = list(range(len(rows)))
    random.Random(f"order:{seed}:{participant_id}").shuffle(order)
    return [visible[i] for i in order], [key[i] for i in order]


def score_pilot(key: list[dict], scored: list[dict]) -> dict:
    """Summarize judged responses, never claim real participants from CSV alone."""
    if not key or any(k.get("category") not in CATEGORIES
                      or k.get("condition") not in ("core", "international", "nonce_control")
                      or (k.get("category") == "addition"
                          and k.get("condition") not in ("international", "nonce_control"))
                      or (k.get("category") == "replacement"
                          and k.get("condition") not in ("international", "core"))
                      for k in key):
        raise VekaError("invalid cognate pilot answer key")
    # Reuse the established strict score validator (completeness, duplicate
    # trials, numeric correctness, duration, and annotated repairs).
    summarize_recognition_scores(key, scored)
    by_id = {r["trial_id"]: r for r in key}
    groups = defaultdict(list)
    for trial in scored:
        trial_type = by_id[trial["trial_id"]]
        group = f"{trial_type['category']}:{trial_type['condition']}"
        groups[group].append(trial)
    summary = {}
    for group, records in sorted(groups.items()):
        times = [float(r["response_ms"]) for r in records if r.get("response_ms")]
        summary[group] = {
            "n": len(records),
            "correct": sum(int(r["correct"]) for r in records),
            "accuracy": sum(int(r["correct"]) for r in records) / len(records),
            "mean_response_ms": sum(times) / len(times) if times else None,
            "timed_trials": len(times),
            "total_repairs": sum(int(r["repair_count"]) for r in records),
        }
    return {
        "schema_version": "veka.cognate-results.v07",
        "trials": len(scored), "groups": summary,
        "recognition_measured_without_human_data": False,
        "human_participants_verified": False,
        "causal_effect_established": False,
        "warning": "These are descriptive scores of supplied annotations; no collection provenance is independently verified.",
    }
