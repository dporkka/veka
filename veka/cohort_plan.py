"""Blinded, blocked cognate-study *planning*, not human data collection.

A researcher must supply pseudonymous participants. Separate participant and
researcher directories prevent accidentally delivering condition keys to subjects.
The CSV deliberately contains no real names, emails or demographic data.
"""
from __future__ import annotations

import csv
import json
import os
import random
import re
from collections import defaultdict
from pathlib import Path

from .cognates import audit_pilot, make_pilot_manifest
from .core import Lexicon, VekaError

ROSTER_FIELDS = ('participant_id', 'background_stratum')
PSEUDONYM = re.compile(r'[A-Za-z0-9_-]{2,64}\Z', re.ASCII)


def read_cohort_roster(path: str | Path) -> list[dict[str, str]]:
    try:
        with open(path, newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream, strict=True)
            if tuple(reader.fieldnames or ()) != ROSTER_FIELDS:
                raise VekaError('roster must contain only participant_id,background_stratum')
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError('could not read study roster') from exc
    if any(set(row) != set(ROSTER_FIELDS) or
           any(not isinstance(row[key], str) for key in ROSTER_FIELDS)
           for row in rows):
        raise VekaError('invalid or truncated study roster record')
    return rows


def plan_cognate_cohorts(candidates: list[dict], lex: Lexicon,
                         roster: list[dict[str, str]], *, seed: int = 20261101) -> dict:
    """Randomize *within* language-background strata; no pretend recruitment."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise VekaError('seed must be an integer')
    audit = audit_pilot(candidates, lex)
    if audit['rejected_count']:
        raise VekaError('cannot run cohort plan on rejected lexical candidates')
    if not roster:
        raise VekaError('a real pseudonymous study roster is required')
    seen = set()
    grouped = defaultdict(list)
    for row in roster:
        if not isinstance(row, dict) or set(row) != set(ROSTER_FIELDS) or any(
            not isinstance(row[k], str) for k in ROSTER_FIELDS
        ):
            raise VekaError('invalid roster fields')
        pid, stratum = row['participant_id'], row['background_stratum']
        if not PSEUDONYM.fullmatch(pid) or pid in seen:
            raise VekaError('invalid or duplicate participant pseudonym')
        if (not 2 <= len(stratum) <= 64 or stratum != stratum.strip() or
                stratum[0] in '=+-@' or
                any(ord(c) < 32 or c in '/\\' for c in stratum)):
            raise VekaError('invalid background stratum')
        seen.add(pid)
        grouped[stratum].append(pid)
    if any(len(group) < 2 or len(group) % 2 for group in grouped.values()):
        raise VekaError('each background stratum needs an even number of at least two participants')

    participants, keys, assignments, by_stratum = {}, [], [], {}
    for stratum in sorted(grouped):
        ids = sorted(grouped[stratum])
        random.Random(f'{seed}:stratum:{stratum}').shuffle(ids)
        half = len(ids) // 2
        for i, pid in enumerate(ids):
            arm = int(i >= half)
            sheet, key = make_pilot_manifest(candidates, lex, pid, seed=seed, arm=arm)
            participants[pid] = sheet
            keys.extend(key)
            assignments.append(dict(participant_id=pid, background_stratum=stratum,
                                    arm=str(arm), seed=str(seed)))
        by_stratum[stratum] = {'arm_0': half, 'arm_1': half}
    return {
        'summary': {
            'schema_version': 'veka.cohort-plan.v10',
            'planned_participants': len(participants),
            'trials_per_participant': len(next(iter(participants.values()))),
            'background_strata': by_stratum,
            'human_data_collected': False,
            'recognition_measured': False,
            'canonical_vocabulary_modified': False,
            'warning': ('Assignments are plans, not completed trials. Human recruitment, '
                        'consent, real exposure, blinded response adjudication and '
                        'preregistration remain external responsibilities.'),
        },
        'participants': dict(sorted(participants.items())),
        'researcher_keys': keys,
        'assignments': sorted(assignments, key=lambda x:x['participant_id']),
    }


def _private_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise VekaError('empty study output is forbidden')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_cohort_plan(plan: dict, participants_dir: str | Path,
                      researcher_dir: str | Path) -> dict:
    participants = Path(participants_dir).resolve()
    researcher = Path(researcher_dir).resolve()
    if participants == researcher or participants in researcher.parents or researcher in participants.parents:
        raise VekaError('researcher and participant directories must not overlap')
    if participants.exists() or researcher.exists():
        raise VekaError('study output directories must not exist; refusing overwrite')
    if not participants.parent.is_dir() or not researcher.parent.is_dir():
        raise VekaError('study output parent directories must already exist')
    if not plan.get('participants') or not plan.get('researcher_keys'):
        raise VekaError('empty plan is not writable')
    try:
        participants.mkdir(mode=0o700)
        researcher.mkdir(mode=0o700)
        for pid, rows in plan['participants'].items():
            if not PSEUDONYM.fullmatch(pid):
                raise VekaError('invalid output pseudonym')
            _private_csv(participants / f'{pid}.csv', rows)
        _private_csv(researcher / 'researcher-key.csv', plan['researcher_keys'])
        _private_csv(researcher / 'assignments.csv', plan['assignments'])
    except OSError as exc:
        raise VekaError('failed to write separated study packets; inspect partial output manually') from exc
    return {**plan['summary'], 'participant_files': len(plan['participants']),
            'participant_dir': str(participants), 'researcher_dir': str(researcher),
            'researcher_key_shared_with_participants': False}
