"""Structural readiness for human-reviewed everyday dialogue translations.

A passed syntax/act screen is *not* a translation or communicative-success
claim. The English requirements remain frozen and untranslated by this module.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .core import VekaError
from .everyday import load_dialogues
from .registers import REGISTERS, inspect_register
from .profiles import PROFILES

SCHEMA = "veka.dialogue-attempts.v01"
ACTS = frozenset({"statement", "polar_question", "content_question", "request"})


def load_attempts(path: str | Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise VekaError(f"cannot load dialogue attempts: {exc}") from exc
    if not isinstance(data, dict):
        raise VekaError("dialogue attempts must be a JSON object")
    return data


def _validate(data: dict, requirements: list[dict]) -> list[dict]:
    if (not isinstance(data, dict)
            or set(data) != {"schema_version", "attempts"}
            or data.get("schema_version") != SCHEMA
            or not isinstance(data.get("attempts"), list)):
        raise VekaError("unknown dialogue attempts schema or invalid fields")
    attempts = data["attempts"]
    known = {item["id"] for item in requirements}
    if len(attempts) > len(known):
        raise VekaError("too many dialogue attempts")
    seen = set()
    for item in attempts:
        if not isinstance(item, dict) or set(item) != {"id", "turns"}:
            raise VekaError("attempt must contain only id and turns")
        identifier = item["id"]
        if not isinstance(identifier, str) or identifier not in known or identifier in seen:
            raise VekaError("unknown or duplicate dialogue scenario id")
        seen.add(identifier)
        turns = item["turns"]
        if not isinstance(turns, list) or len(turns) != 2:
            raise VekaError("each dialogue attempt must have exactly two turns")
        for turn, speaker in zip(turns, ("A", "B")):
            if (not isinstance(turn, dict)
                    or set(turn) != {"speaker", "veka", "intended_act"}
                    or turn.get("speaker") != speaker
                    or not isinstance(turn.get("intended_act"), str)
                    or turn["intended_act"] not in ACTS
                    or not isinstance(turn.get("veka"), str)
                    or not turn["veka"].strip()
                    or len(turn["veka"]) > 1024):
                raise VekaError(f"invalid {speaker} turn in {identifier}")
    return attempts


def _observed_act(ast: dict) -> str:
    if ast.get("mood") == "imperative":
        return "request"  # Structural proxy; politeness/intent are not certified.
    if ast.get("question_type") == "content":
        return "content_question"
    if ast.get("question"):
        return "polar_question"
    if ast.get("mood") == "statement" or ast.get("op") in {"and", "or", "if", "not", "atom"}:
        return "statement"
    return "unknown"


def evaluate_attempts(
    data: dict, *, max_register: str = "core", profile: str = "tonal"
) -> dict:
    """Screen 100-dialogue requirements; never certify translation equivalence."""
    if profile not in PROFILES:
        raise VekaError(f"unknown vocabulary profile: {profile!r}")
    if max_register not in REGISTERS:
        raise VekaError(f"unknown maximum register: {max_register!r}")
    requirements = load_dialogues()
    attempts = _validate(data, requirements)
    id_to_domain = {row["id"]: row["domain"] for row in requirements}
    results = []
    syntactic = 0
    aligned = 0
    reviewable = 0
    by_domain = Counter()
    for item in attempts:
        turns = []
        for attempt in item["turns"]:
            entry = {
                "speaker": attempt["speaker"],
                "intended_act": attempt["intended_act"],
                "syntax_accepted": False,
                "speech_act_aligned": False,
                "observed_act": None,
                "grammar_register": None,
            }
            try:
                result = inspect_register(attempt["veka"], profile=profile, max_register=max_register)
            except VekaError as exc:
                entry["syntax_error"] = str(exc)
            else:
                entry["syntax_accepted"] = True
                entry["grammar_register"] = result["grammar_register"]
                entry["observed_act"] = _observed_act(result["ast"])
                entry["speech_act_aligned"] = entry["observed_act"] == attempt["intended_act"]
                syntactic += 1
                aligned += int(entry["speech_act_aligned"])
            turns.append(entry)
        ready = all(t["syntax_accepted"] and t["speech_act_aligned"] for t in turns)
        reviewable += int(ready)
        by_domain[id_to_domain[item["id"]]] += int(ready)
        results.append({
            "id": item["id"], "domain": id_to_domain[item["id"]],
            "turns": turns,
            "ready_for_semantic_review": ready,
            "meaning_equivalence_verified": False,
        })
    return {
        "schema_version": "veka.dialogue-check.v01",
        "total_scenarios": len(requirements),
        "attempted_scenarios": len(attempts),
        "unattempted_scenarios": len(requirements) - len(attempts),
        "syntax_accepted_turns": syntactic,
        "speech_act_aligned_turns": aligned,
        "ready_for_semantic_review": reviewable,
        "ready_by_domain": dict(sorted(by_domain.items())),
        "verified_translations": 0,
        "human_comprehension_validated": False,
        "language_coverage_established": False,
        "limitations": [
            "Parser acceptance checks syntax, not intended English meaning.",
            "Speech-act alignment is structural only; pragmatic equivalence is unreviewed.",
            "All passing attempts still require independent translation review and human comprehension studies.",
        ],
        "attempts": results,
    }
