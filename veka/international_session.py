"""Strict participant-only export for the 24-item international v0.10 study.

Never writes the answer key to a participant file, judges answers, or
converts candidate words into accepted Veka vocabulary.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .core import VekaError, validate_word

PARTICIPANT_COLUMNS = (
    "participant_id", "trial_id", "presented_form", "response_gloss",
    "response_ms", "prior_exposure", "presentation_modality"
)
SCHEMA = "veka.international-session.v10"
PARTICIPANT_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}\Z", re.ASCII)
TRIAL_PATTERN = re.compile(r"V04-[0-9a-f]{12}\Z", re.ASCII)
EXPECTED_TRIALS = 24


def validate_international_manifest(rows: list[dict]) -> str:
    if len(rows) != EXPECTED_TRIALS:
        raise VekaError(f"international manifest requires {EXPECTED_TRIALS} rows")
    participants = set()
    trial_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(PARTICIPANT_COLUMNS):
            raise VekaError("expected participant-only international manifest, NOT the answer key")
        if any(not isinstance(value, str) for value in row.values()):
            raise VekaError("malformed international manifest row")
        pid, trial, form = row["participant_id"], row["trial_id"], row["presented_form"]
        if (not PARTICIPANT_PATTERN.fullmatch(pid)
                or not TRIAL_PATTERN.fullmatch(trial) or trial in trial_ids
                or not validate_word(form) or len(form) > 64
                or row["presentation_modality"] != "written"
                or any(row[field] for field in ("response_gloss", "response_ms", "prior_exposure"))):
            raise VekaError("invalid or prefilled participant trial")
        trial_ids.add(trial)
        participants.add(pid)
    if len(participants) != 1:
        raise VekaError("international manifest mixes participants")
    return next(iter(participants))


def read_international_manifest(path: str | Path) -> list[dict]:
    try:
        with Path(path).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != PARTICIPANT_COLUMNS:
                raise VekaError("expected participant-only international CSV; NEVER pass a researcher key")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("unable to read participant-only international manifest") from exc
    validate_international_manifest(rows)
    return rows


def write_international_session(rows: list[dict], path: str | Path) -> dict:
    participant = validate_international_manifest(rows)
    payload = {
        "schema_version": SCHEMA,
        "participant_id": participant,
        "trials": [{"trial_id": row["trial_id"], "presented_form": row["presented_form"]}
                   for row in rows],
    }
    target = Path(path)
    try:
        with target.open("x", encoding="utf-8") as out:
            json.dump(payload, out, indent=2, ensure_ascii=False)
            out.write("\n")
    except FileExistsError as exc:
        raise VekaError("refusing to overwrite participant session") from exc
    except (OSError, UnicodeError) as exc:
        raise VekaError("cannot write international session") from exc
    return {
        "schema_version": SCHEMA, "participant_id": participant,
        "trials": len(rows), "session_file": str(target),
        "answer_key_embedded": False, "human_data_collected": False,
        "warning": "Participant-only blinded stimuli; no human observations exist.",
    }

RESEARCHER_KEY_COLUMNS = (
    "participant_id", "trial_id", "concept_id", "target_gloss",
    "condition", "presented_form", "status", "judge_correct", "repair_count"
)
BROWSER_RESPONSE_COLUMNS = (
    "participant_id", "trial_id", "presented_form", "response_gloss",
    "response_ms", "prior_exposure", "first_language",
    "language_background_family", "timing_interrupted"
)
JUDGE_COLUMNS = (
    "trial_id", "presented_form", "response_gloss", "target_gloss",
    "response_ms", "prior_exposure", "first_language",
    "language_background_family", "timing_interrupted", "correct", "repair_count"
)


def _read_private_rows(path: str | Path, headers: tuple[str, ...]) -> list[dict]:
    try:
        with Path(path).open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream, strict=True)
            if tuple(reader.fieldnames or ()) != headers:
                raise VekaError("incorrect researcher CSV schema")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("could not read researcher CSV") from exc
    if (len(rows) != EXPECTED_TRIALS
            or any(set(row) != set(headers) or
                   any(not isinstance(row.get(k), str) for k in headers)
                   for row in rows)):
        raise VekaError("missing or malformed researcher trial")
    return rows


def _spreadsheet_safe(value: str) -> str:
    """Prevent pasted participant text from activating CSV spreadsheet formulas."""
    return "'" + value if re.match(r"^[\t\r\n ]*[=+@-]", value) else value


def prepare_international_judge_sheet(
    key_file: str | Path, responses_file: str | Path, output_file: str | Path
) -> dict:
    """Match private answer key to browser responses, leaving scoring blank.

    Judges see target meanings but NOT condition labels. The output is PRIVATE.
    Do not infer answer correctness or overwrite another research artifact.
    """
    paths = [Path(x).resolve() for x in (key_file, responses_file, output_file)]
    if len(set(paths)) != 3:
        raise VekaError("private key, raw responses and review output must differ")
    key = _read_private_rows(key_file, RESEARCHER_KEY_COLUMNS)
    responses = _read_private_rows(responses_file, BROWSER_RESPONSE_COLUMNS)
    by_trial = {row["trial_id"]: row for row in key}
    if len(by_trial) != EXPECTED_TRIALS or len({r["trial_id"] for r in responses}) != EXPECTED_TRIALS:
        raise VekaError("duplicate trial ID")
    if set(by_trial) != {r["trial_id"] for r in responses}:
        raise VekaError("participant responses do not cover the answer key")
    participants = {r["participant_id"] for r in key + responses}
    if len(participants) != 1 or not PARTICIPANT_PATTERN.fullmatch(next(iter(participants))):
        raise VekaError("mixed or invalid participant identifiers")

    reviewed = []
    for row in responses:
        target = by_trial[row["trial_id"]]
        try:
            millis = int(row["response_ms"])
        except ValueError as exc:
            raise VekaError("invalid participant response duration") from exc
        if (not TRIAL_PATTERN.fullmatch(row["trial_id"])
                or row["presented_form"] != target["presented_form"]
                or target["condition"] not in ("core", "international")
                or target["status"] != "unverified_draft"
                or any(target[field].strip() for field in ("judge_correct", "repair_count"))
                or not target["target_gloss"].strip() or not row["response_gloss"].strip()
                or not row["first_language"].strip()
                or row["prior_exposure"] not in ("yes", "no", "unsure")
                or row["timing_interrupted"] not in ("yes", "no")
                or not row["response_ms"].isascii() or not row["response_ms"].isdecimal()
                or millis <= 0):
            raise VekaError("invalid first-sight trial or answer-key mismatch")
        reviewed.append({
            "trial_id": row["trial_id"], "presented_form": row["presented_form"],
            "response_gloss": _spreadsheet_safe(row["response_gloss"]),
            "target_gloss": _spreadsheet_safe(target["target_gloss"]),
            "response_ms": row["response_ms"], "prior_exposure": row["prior_exposure"],
            "first_language": _spreadsheet_safe(row["first_language"]),
            "language_background_family": _spreadsheet_safe(row["language_background_family"]),
            "timing_interrupted": row["timing_interrupted"],
            "correct": "", "repair_count": "",
        })

    try:
        with Path(output_file).open("x", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=JUDGE_COLUMNS)
            writer.writeheader()
            writer.writerows(reviewed)
    except FileExistsError as exc:
        raise VekaError("refusing to overwrite existing judgment sheet") from exc
    except (OSError, UnicodeError) as exc:
        raise VekaError("could not write researcher judgment sheet") from exc
    return {
        "schema_version": "veka.international-judge-sheet.v10",
        "trials": len(reviewed), "output": str(output_file),
        "manually_scored": 0, "human_benefit_established": False,
        "warning": ("Private review only: independently judge each meaning; assess "
                    "response validity, interruptions, and prior exposure before scoring."),
    }
