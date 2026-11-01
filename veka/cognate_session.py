"""Generate participant-only JSON for blinded Veka cognate first-sight sessions.

No targets, allocations, semantic keys or scores are ever included.
Researcher-only answer keys remain separate from this tool.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .core import VekaError, validate_word

PARTICIPANT_COLUMNS = (
    "participant_id", "trial_id", "presented_form",
    "response_gloss", "response_ms", "prior_exposure",
)
SESSION_VERSION = "veka.cognate-session.v07"
PARTICIPANT_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z", re.ASCII)
TRIAL_ID = re.compile(r"C07-[0-9a-f]{16}\Z", re.ASCII)
EXPECTED_TRIALS = 18


def read_blind_manifest(path: str | Path) -> list[dict[str, str]]:
    """Reject answer keys, pre-filled responses and structurally invalid rows."""
    try:
        with Path(path).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != PARTICIPANT_COLUMNS:
                raise VekaError("expected participant-only cognate manifest; NEVER use the researcher key")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read participant cognate manifest") from exc

    if len(rows) != EXPECTED_TRIALS:
        raise VekaError(f"cognate session needs exactly {EXPECTED_TRIALS} trials")
    participants: set[str] = set()
    trial_ids: set[str] = set()
    for row in rows:
        if (set(row) != set(PARTICIPANT_COLUMNS)
                or any(not isinstance(row.get(field), str) for field in PARTICIPANT_COLUMNS)):
            raise VekaError("malformed participant manifest row")
        pid = row["participant_id"]
        tid = row["trial_id"]
        form = row["presented_form"]
        if (not PARTICIPANT_ID.fullmatch(pid) or not TRIAL_ID.fullmatch(tid)
                or not validate_word(form) or len(form) > 64
                or any(row[field] for field in ("response_gloss", "response_ms", "prior_exposure"))):
            raise VekaError("invalid trial stimulus, identifier, or pre-filled response")
        participants.add(pid)
        if tid in trial_ids:
            raise VekaError("duplicate participant trial identifier")
        trial_ids.add(tid)
    if len(participants) != 1:
        raise VekaError("manifest mixes multiple participants")
    return rows


def write_blind_session(rows: list[dict[str, str]], output: str | Path) -> dict:
    """Write JSON only after validating all records and refusing overwrites."""
    if not rows:
        raise VekaError("empty cognate session")
    # Public API must be safe even if called directly with fabricated rows.
    if len(rows) != EXPECTED_TRIALS:
        raise VekaError("wrong number of participant trials")
    for row in rows:
        if set(row) != set(PARTICIPANT_COLUMNS):
            raise VekaError("participant-only manifest required")
        if any(row.get(field) for field in ("response_gloss", "response_ms", "prior_exposure")):
            raise VekaError("cannot package pre-filled response")
    participant = rows[0]["participant_id"]
    if not PARTICIPANT_ID.fullmatch(participant):
        raise VekaError("invalid participant pseudonym")
    seen = set()
    for row in rows:
        if (row["participant_id"] != participant
                or not TRIAL_ID.fullmatch(row["trial_id"])
                or row["trial_id"] in seen
                or not validate_word(row["presented_form"])
                or len(row["presented_form"]) > 64):
            raise VekaError("invalid or duplicate session stimulus")
        seen.add(row["trial_id"])
    result = {
        "schema_version": SESSION_VERSION,
        "participant_id": participant,
        "trials": [
            {"trial_id": row["trial_id"], "presented_form": row["presented_form"]}
            for row in rows
        ],
    }
    destination = Path(output)
    try:
        with destination.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError as exc:
        raise VekaError("refusing to overwrite an existing participant session") from exc
    except (OSError, UnicodeError) as exc:
        raise VekaError("cannot write participant session") from exc
    return {
        "schema_version": SESSION_VERSION, "participant_id": participant,
        "trials": len(rows), "session_file": str(destination),
        "answer_key_embedded": False, "human_data_collected": False,
        "warning": "No answer key in session; browser timings are exploratory, not calibrated.",
    }


KEY_FIELDS = (
    "participant_id", "trial_id", "concept_id", "target_gloss",
    "category", "condition", "presented_form", "status",
)
RESPONSE_FIELDS = (
    "participant_id", "trial_id", "presented_form", "response_gloss",
    "response_ms", "prior_exposure", "first_language",
    "language_background_family", "timing_interrupted",
)
JUDGE_FIELDS = (
    "trial_id", "presented_form", "response_gloss", "target_gloss",
    "response_ms", "prior_exposure", "first_language",
    "language_background_family", "timing_interrupted",
    "correct", "repair_count",
)


def _read_study_csv(path: str | Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with Path(path).open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != columns:
                raise VekaError("researcher data CSV has an invalid header")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot read researcher data CSV") from exc
    if (len(rows) != EXPECTED_TRIALS
            or any(set(row) != set(columns)
                   or any(not isinstance(row[column], str) for column in columns)
                   for row in rows)):
        raise VekaError("incomplete or malformed researcher data CSV")
    if len(set(r["trial_id"] for r in rows)) != EXPECTED_TRIALS:
        raise VekaError("duplicate researcher data trial")
    return rows


def prepare_judge_sheet(
    key_file: str | Path, responses_file: str | Path, output_file: str | Path
) -> dict:
    """Build a *private* blank judgment sheet; never infer a correct answer.

    The judgment sheet shows target meanings but hides experimental condition
    labels from the adjudicator. It must NEVER be given to participants.
    """
    destinations = {
        Path(key_file).resolve(), Path(responses_file).resolve(),
        Path(output_file).resolve(),
    }
    if len(destinations) != 3:
        raise VekaError("researcher key, raw responses, and judgment output must be separate files")
    key = _read_study_csv(key_file, KEY_FIELDS)
    observed = _read_study_csv(responses_file, RESPONSE_FIELDS)
    by_id = {r["trial_id"]: r for r in key}
    if set(by_id) != {r["trial_id"] for r in observed}:
        raise VekaError("raw responses do not cover the researcher answer key")
    participants = {r["participant_id"] for r in observed + key}
    if len(participants) != 1 or not PARTICIPANT_ID.fullmatch(next(iter(participants))):
        raise VekaError("key and responses must belong to one participant")
    prepared = []
    for row in observed:
        match = by_id[row["trial_id"]]
        if (row["presented_form"] != match["presented_form"]
                or not row["response_gloss"].strip()
                or not row["first_language"].strip()
                or row["prior_exposure"] not in ("yes", "no", "unsure")
                or row["timing_interrupted"] not in ("yes", "no")
                or not match["target_gloss"].strip()
                or not TRIAL_ID.fullmatch(row["trial_id"])
                or match["status"] != "unverified_draft"):
            raise VekaError("invalid response/answer-key pairing or missing metadata")
        try:
            duration = float(row["response_ms"])
        except (ValueError, TypeError) as exc:
            raise VekaError("invalid response duration") from exc
        if not 0 < duration < 3_600_000:
            raise VekaError("response duration is not finite and positive")
        prepared.append({
            "trial_id": row["trial_id"],
            "presented_form": row["presented_form"],
            "response_gloss": row["response_gloss"],
            "target_gloss": match["target_gloss"],
            "response_ms": row["response_ms"],
            "prior_exposure": row["prior_exposure"],
            "first_language": row["first_language"],
            "language_background_family": row["language_background_family"],
            "timing_interrupted": row["timing_interrupted"],
            "correct": "", "repair_count": "",
        })
    try:
        with Path(output_file).open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=JUDGE_FIELDS)
            writer.writeheader()
            writer.writerows(prepared)
    except FileExistsError as exc:
        raise VekaError("refusing to overwrite a judgment sheet") from exc
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError("cannot write judgment sheet") from exc
    return {
        "trials": len(prepared), "judge_sheet": str(output_file),
        "automatically_judged": False, "human_data_verified": False,
        "answer_key_embedded_for_participants": False,
        "warning": "Private researcher-only sheet. Mark correct=0/1 and repair_count; do not expose to participants.",
    }
