"""Package researcher-authored dialogue stimuli without semantic answers.

This module does not translate, validate translation equivalence, recruit,
collect observations, or certify independently reviewed material.
"""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

from .core import VekaError
from .everyday import load_dialogues
from .language_transfer import LANGUAGES, PSEUDONYM

MANIFEST_FIELDS = ('participant_id', 'trial_id', 'scenario_id',
                   'language', 'context', 'utterance')
SESSION_VERSION = 'veka.conversation-session.v01'
TRIAL_ID = re.compile(r'D01-[0-9a-f]{16}\Z', re.ASCII)
MAX_TRIALS = 40


def _validate_rows(rows: list[dict[str, str]]) -> str:
    """Fail closed on extra fields, answer keys, repeated exposure or mixed IDs."""
    if not isinstance(rows, list) or not 2 <= len(rows) <= MAX_TRIALS:
        raise VekaError('conversation session needs 2 to 40 human-authored stimuli')
    known = {row['id'] for row in load_dialogues()}
    participants = set()
    trials = set()
    scenarios = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != set(MANIFEST_FIELDS)
                or any(not isinstance(row[k], str) for k in MANIFEST_FIELDS)):
            raise VekaError('researcher manifest must contain only exact participant fields')
        pid, tid, scenario, lang = (row[k] for k in MANIFEST_FIELDS[:4])
        if (not PSEUDONYM.fullmatch(pid) or not TRIAL_ID.fullmatch(tid)
                or scenario not in known or lang not in LANGUAGES):
            raise VekaError('invalid pseudonym, opaque trial ID, scenario, or language')
        if tid in trials or scenario in scenarios:
            raise VekaError('duplicate trial or repeated semantic scenario exposure')
        for field in ('context', 'utterance'):
            value = row[field]
            if (not 1 <= len(value.strip()) <= 2000 or value != value.strip()
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)
                    or value[0] in '=+@-'):
                raise VekaError('stimuli must be nonempty safe plain text, not formulas or controls')
        participants.add(pid)
        trials.add(tid)
        scenarios.add(scenario)
    if len(participants) != 1:
        raise VekaError('one pseudonymous participant per session file')
    return next(iter(participants))


def read_conversation_manifest(path: str | Path) -> list[dict[str, str]]:
    try:
        with Path(path).open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle, strict=True)
            if tuple(reader.fieldnames or ()) != MANIFEST_FIELDS:
                raise VekaError('researcher manifest schema mismatch; keys or results not permitted')
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError('cannot read researcher conversation manifest') from exc
    _validate_rows(rows)
    return rows


def write_conversation_session(rows: list[dict[str, str]], output: str | Path) -> dict:
    """Write participant-only session with exclusive creation and no answers."""
    pid = _validate_rows(rows)  # protect direct Python callers too
    session = {
        'schema_version': SESSION_VERSION,
        'participant_id': pid,
        'trials': [
            {key: row[key] for key in ('trial_id', 'language', 'context', 'utterance')}
            for row in rows
        ],
    }
    path = Path(output)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(session, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
    except FileExistsError as exc:
        raise VekaError('refusing to overwrite an existing study session or manifest') from exc
    except (OSError, UnicodeError) as exc:
        raise VekaError('could not create conversation session') from exc
    return {
        'schema_version': SESSION_VERSION, 'participant_id': pid,
        'trials': len(rows), 'output': str(path), 'answer_key_embedded': False,
        'canonical_changes': 0, 'human_data_collected': False,
        'stimulus_review_authenticated': False,
        'warning': ('Researcher-authored stimuli have not been independently validated by this '
                    'tool. Participant JSON contains no scenario IDs or expected meanings. '
                    'Do not score raw responses before independent human adjudication.'),
    }
