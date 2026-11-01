"""Strict manual adjudication and descriptive results for Veka root-study v1.2.

Not a participant collector, human-authentication system, or automatic
vocabulary-change mechanism. The participant workbook remains separate from
the researcher key; judge sheets hide conditions, language strata and forms.
"""
from __future__ import annotations

import csv
import os
import re
from collections import defaultdict
from pathlib import Path

from .cohort_plan import PSEUDONYM
from .core import VekaError

KEY_FIELDS = (
    "participant_id", "trial_id", "concept_id", "target_gloss",
    "condition", "presented_form", "background_stratum",
)
RESPONSE_FIELDS = (
    "participant_id", "trial_id", "presented_form", "response_gloss",
    "response_ms", "prior_exposure", "presentation_modality",
)
JUDGE_FIELDS = (
    "trial_id", "target_gloss", "response_gloss",
    "correct", "critical_error", "judge_id",
)
TRIAL_ID = re.compile(r"V12-[0-9a-f]{16}\Z", re.ASCII)
CONCEPT_ID = re.compile(r"C[0-9]{3}\Z", re.ASCII)
MAX_DURATION_MS = 3_600_000


def read_root_study_csv(path: str | Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with Path(path).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != fields:
                raise VekaError("invalid root study CSV schema")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read root study CSV") from exc
    if any(not isinstance(row, dict) or set(row) != set(fields)
           or any(not isinstance(row[field], str) for field in fields)
           for row in rows):
        raise VekaError("truncated or invalid root study CSV row")
    return rows


def _number(text: str) -> int:
    if not text or not text.isascii() or not text.isdecimal() or len(text) > 7:
        raise VekaError("response time must be integer milliseconds")
    number = int(text)
    if not 0 < number < MAX_DURATION_MS:
        raise VekaError("response time outside allowed range")
    return number


def _safe_text(text: str) -> bool:
    # Avoid formulas in private CSV files opened in spreadsheet programs.
    return (bool(text) and text == text.strip() and len(text) <= 250
            and text[0] not in "=+-@"
            and all(ord(ch) >= 32 for ch in text))


def _pair(key: list[dict], responses: list[dict]) -> tuple[dict, dict]:
    if not key or len(key) != len(responses):
        raise VekaError("a complete researcher key and all responses are required")
    mapping = {}
    by_participant = defaultdict(list)
    for row in key:
        if not isinstance(row, dict) or set(row) != set(KEY_FIELDS):
            raise VekaError("invalid researcher-key columns")
        if any(not isinstance(row[field], str) for field in KEY_FIELDS):
            raise VekaError("invalid researcher-key values")
        pid, tid, concept = row["participant_id"], row["trial_id"], row["concept_id"]
        if (not PSEUDONYM.fullmatch(pid) or not TRIAL_ID.fullmatch(tid)
                or not CONCEPT_ID.fullmatch(concept)
                or not _safe_text(row["target_gloss"])
                or not _safe_text(row["presented_form"])
                or not _safe_text(row["background_stratum"])
                or row["condition"] not in ("core", "candidate")
                or tid in mapping):
            raise VekaError("invalid or duplicate research trial in key")
        mapping[tid] = row
        by_participant[pid].append(row)
    concepts = {r["concept_id"] for r in key}
    if len(concepts) != 8:
        raise VekaError("V12 root-study key requires eight distinct concepts")
    for pid, group in by_participant.items():
        if (len(group) != 8 or {r["concept_id"] for r in group} != concepts
                or len({r["background_stratum"] for r in group}) != 1
                or sum(r["condition"] == "core" for r in group) != 4):
            raise VekaError("researcher key is not a complete balanced root-study plan")
    # Every condition must map to a single, stable stimulus and every concept
    # to one invariant meaning across participants. Otherwise even a complete,
    # balanced-looking CSV can silently mix experimental arms or target senses.
    for concept in concepts:
        group = [row for row in key if row['concept_id'] == concept]
        if len({row['target_gloss'] for row in group}) != 1:
            raise VekaError('inconsistent target sense across participants')
        forms = {
            cond: {row['presented_form'] for row in group if row['condition'] == cond}
            for cond in ('core', 'candidate')
        }
        if (len(forms['core']) != 1 or len(forms['candidate']) != 1
                or forms['core'] == forms['candidate']):
            raise VekaError('inconsistent or identical condition stimuli')
    strata = defaultdict(list)
    for group in by_participant.values():
        strata[group[0]["background_stratum"]].append(group)
    for groups in strata.values():
        if len(groups) < 2 or len(groups) % 2:
            raise VekaError("language stratum must contain an even number of complete participants")
        for concept in concepts:
            conditions = [r["condition"] for group in groups for r in group
                          if r["concept_id"] == concept]
            if conditions.count("core") != conditions.count("candidate"):
                raise VekaError("unbalanced experiment for a concept and language stratum")

    observed = {}
    for row in responses:
        if not isinstance(row, dict) or set(row) != set(RESPONSE_FIELDS):
            raise VekaError("invalid participant response columns")
        if any(not isinstance(row[field], str) for field in RESPONSE_FIELDS):
            raise VekaError("invalid participant response values")
        tid = row["trial_id"]
        expected = mapping.get(tid)
        if (expected is None or tid in observed
                or row["participant_id"] != expected["participant_id"]
                or row["presented_form"] != expected["presented_form"]
                or row["presentation_modality"] != "written"
                or row["prior_exposure"] not in ("yes", "no", "unsure")
                or not _safe_text(row["response_gloss"])):
            raise VekaError("response does not match the blinded researcher key")
        _number(row["response_ms"])
        observed[tid] = row
    if set(observed) != set(mapping):
        raise VekaError("responses do not cover every planned trial")
    return mapping, observed


def prepare_root_judge_sheet(key_file: str | Path, responses_file: str | Path,
                             output_file: str | Path) -> dict:
    """Export a private, condition-blind judgment sheet, NEVER automatic answers."""
    paths = {Path(p).resolve() for p in (key_file, responses_file, output_file)}
    if len(paths) != 3:
        raise VekaError("researcher key, responses and judge sheet must be different files")
    key = read_root_study_csv(key_file, KEY_FIELDS)
    responses = read_root_study_csv(responses_file, RESPONSE_FIELDS)
    mapping, observed = _pair(key, responses)
    rows = [{
        "trial_id": tid,
        "target_gloss": mapping[tid]["target_gloss"],
        "response_gloss": observed[tid]["response_gloss"],
        "correct": "", "critical_error": "", "judge_id": "",
    } for tid in sorted(mapping)]
    destination = Path(output_file)
    try:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=JUDGE_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    except FileExistsError as exc:
        raise VekaError("refusing to overwrite existing judge sheet") from exc
    except (OSError, UnicodeError) as exc:
        raise VekaError("cannot write private judge sheet") from exc
    return {
        "schema_version": "veka.root-study-judge.v13",
        "unscored_trials": len(rows), "blinded_to_condition": True,
        "participant_ids_in_sheet": False, "source_forms_in_sheet": False,
        "human_judgments_collected": False, "adoption_authorized": False,
        "warning": "Keep the judge sheet private. Do not expose researcher keys to participants.",
    }


def _stats(rows: list[dict]) -> dict:
    n = len(rows)
    correct = sum(r["correct"] for r in rows)
    total_ms = sum(r["elapsed_ms"] for r in rows)
    return {
        "trials": n, "correct": correct,
        "critical_errors": sum(r["critical_error"] for r in rows),
        "total_response_ms": total_ms,
        "accuracy": correct / n if n else None,
        "correct_per_minute": correct * 60000 / total_ms if total_ms else None,
    }


def _conditions(rows: list[dict]) -> dict:
    return {
        cond: _stats([r for r in rows if r["condition"] == cond])
        for cond in ("core", "candidate")
    }


def score_root_study(key: list[dict], responses: list[dict],
                     judges: list[dict]) -> dict:
    """Aggregate adjudicated *claims*; never infer participant authenticity."""
    mapping, observed = _pair(key, responses)
    if len(judges) != len(mapping):
        raise VekaError("all trials require manual adjudication")
    judged = {}
    for row in judges:
        if not isinstance(row, dict) or set(row) != set(JUDGE_FIELDS):
            raise VekaError("invalid judge-sheet columns")
        if any(not isinstance(row[field], str) for field in JUDGE_FIELDS):
            raise VekaError("invalid judge-sheet values")
        tid = row["trial_id"]
        match = mapping.get(tid)
        if (match is None or tid in judged
                or row["target_gloss"] != match["target_gloss"]
                or row["response_gloss"] != observed[tid]["response_gloss"]
                or row["correct"] not in ("0", "1")
                or row["critical_error"] not in ("0", "1")
                or (row["correct"] == "1" and row["critical_error"] == "1")
                or not PSEUDONYM.fullmatch(row["judge_id"])):
            raise VekaError("missing, tampered, contradictory or duplicate judgment")
        judged[tid] = row
    if set(judged) != set(mapping):
        raise VekaError("missing manual judgments")

    all_rows = [{
        "stratum": key_row["background_stratum"],
        "concept": key_row["concept_id"],
        "condition": key_row["condition"],
        "correct": int(judged[tid]["correct"]),
        "critical_error": int(judged[tid]["critical_error"]),
        "elapsed_ms": _number(observed[tid]["response_ms"]),
        "prior_exposure": observed[tid]["prior_exposure"],
    } for tid, key_row in mapping.items()]
    first = [r for r in all_rows if r["prior_exposure"] == "no"]
    strata = sorted({r["stratum"] for r in all_rows})
    concepts = sorted({r["concept"] for r in all_rows})
    return {
        "schema_version": "veka.root-study-results.v13",
        "submitted_trials": len(all_rows),
        "participants_claimed": len({r["participant_id"] for r in key}),
        "first_sight_trials": len(first),
        "excluded_for_prior_exposure": len(all_rows) - len(first),
        "all_submitted_critical_errors": sum(r["critical_error"] for r in all_rows),
        "by_condition": _conditions(first),
        "by_stratum": {name: _conditions([r for r in first if r["stratum"] == name])
                       for name in strata},
        "by_concept": {cid: _conditions([r for r in first if r["concept"] == cid])
                       for cid in concepts},
        "condition_balance_in_key": True,
        "independent_human_verification": False,
        "human_benefit_established": False,
        "acoustic_comprehension_measured": False,
        "retention_measured": False,
        "adoption_authorized": False,
        "canonical_changes": 0,
        "warning": (
            "Descriptive claimed human judgments only. Study recruitment, consent, "
            "actual exposure, timing, independence, reviewer blinding and translations "
            "are not authenticated. Excludes yes/unsure prior exposure from first-sight "
            "metrics. No causal estimate, uncertainty interval, release threshold, "
            "listening evidence or vocabulary adoption follows from these summaries."
        ),
    }
