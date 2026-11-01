"""Research-only language-design transfers and *descriptive* conversation outcomes.

Never defines new Veka words, changes its grammar, certifies translations, or
infers causal superiority from observational data.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from .core import VekaError
from .everyday import load_dialogues

PROPOSAL_SCHEMA = 'veka.language-transfer.v01'
PROPOSAL_FIELDS = frozenset({
    'id', 'source_languages', 'principle', 'hypothesis', 'contrasts',
    'scenario_ids', 'risks', 'decision_gate', 'status', 'boundary',
})
CONVERSATION_FIELDS = (
    'participant_id', 'background_family', 'scenario_id', 'language',
    'correct', 'elapsed_ms', 'repair_ms', 'critical_error',
)
LANGUAGES = frozenset({'veka', 'globasa', 'esperanto', 'interlingua', 'indonesian'})
PSEUDONYM = re.compile(r'[A-Za-z0-9_-]{2,64}\Z', re.ASCII)


def load_proposals(path: str | Path) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError) as exc:
        raise VekaError('cannot load language transfer research catalog') from exc
    if not isinstance(doc, dict):
        raise VekaError('research catalog must be an object')
    return doc


def audit_proposals(doc: dict, requirements: list[dict] | None = None) -> dict:
    """Link precise *meaning* contrasts to existing unverified dialogue needs."""
    if (not isinstance(doc, dict) or set(doc) != {'schema_version', 'proposals'}
            or doc.get('schema_version') != PROPOSAL_SCHEMA
            or not isinstance(doc.get('proposals'), list)
            or not doc['proposals']):
        raise VekaError('invalid language transfer schema')
    known = {r['id'] for r in (load_dialogues() if requirements is None else requirements)}
    seen = set()
    items = []
    for p in doc['proposals']:
        if not isinstance(p, dict) or set(p) != PROPOSAL_FIELDS:
            raise VekaError('proposal has missing or unexpected fields')
        ident = p['id']
        if (not isinstance(ident, str) or not re.fullmatch(r'[a-z][a-z0-9_]{2,63}', ident)
                or ident in seen or p['status'] != 'hypothesis'
                or p['boundary'] != 'research_only'):
            raise VekaError('invalid, duplicate, or incorrectly promoted proposal')
        seen.add(ident)
        for field in ('principle', 'hypothesis', 'decision_gate'):
            if not isinstance(p[field], str) or not p[field].strip():
                raise VekaError(f'{ident}: missing {field}')
        for field in ('source_languages', 'contrasts', 'risks', 'scenario_ids'):
            values = p[field]
            if (not isinstance(values, list) or not values or
                    any(not isinstance(s, str) or not s.strip() for s in values) or
                    len(values) != len(set(values))):
                raise VekaError(f'{ident}: invalid or duplicate {field}')
        if len(p['contrasts']) < 2 or not set(p['scenario_ids']).issubset(known):
            raise VekaError(f'{ident}: need two contrasts and existing dialogue scenario ids')
        items.append({'id': ident, 'source_languages': p['source_languages'],
                      'principle': p['principle'], 'hypothesis': p['hypothesis'],
                      'contrasts': p['contrasts'], 'scenario_ids': p['scenario_ids'],
                      'risks': p['risks'], 'decision_gate': p['decision_gate'],
                      'status': 'hypothesis', 'requires_human_validation': True})
    items.sort(key=lambda p: p['id'])
    return {
        'schema_version': 'veka.borrowing-audit.v01',
        'proposals': len(items), 'scenarios_referenced': len({s for p in items for s in p['scenario_ids']}),
        'approved_proposals': 0, 'canonical_changes': 0,
        'human_benefit_established': False, 'items': items,
        'warning': ('These are hypotheses and English meaning contrasts, not approved Veka '
                    'words, licensed example translations, syntax, or observed trials. '
                    'Each requires reviewed translations and preregistered listening/learning tests.'),
    }


def read_conversation_trials(path: str | Path) -> list[dict[str, str]]:
    try:
        with Path(path).open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, strict=True)
            if tuple(reader.fieldnames or ()) != CONVERSATION_FIELDS:
                raise VekaError('invalid conversation trial CSV header')
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise VekaError('cannot read conversation trial CSV') from exc
    if any(set(row) != set(CONVERSATION_FIELDS) or
           any(not isinstance(row[f], str) for f in CONVERSATION_FIELDS)
           for row in rows):
        raise VekaError('malformed conversation trial CSV row')
    return rows


def _stats(rows: list[dict]) -> dict:
    total = sum(r['duration_ms'] for r in rows)
    good = sum(r['correct'] for r in rows)
    return {'trials': len(rows), 'correct': good,
            'critical_errors': sum(r['critical_error'] for r in rows),
            'total_ms': total,
            'correct_per_minute': (round(good * 60000 / total, 4) if total else None)}


def score_conversations(rows: list[dict[str, str]],
                        requirements: list[dict] | None = None) -> dict:
    """Descriptive correct meanings per *total response+repair* minute by cohort."""
    known = {r['id'] for r in (load_dialogues() if requirements is None else requirements)}
    seen = set()
    participants = {}
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(CONVERSATION_FIELDS) or any(
            not isinstance(v, str) for v in row.values()
        ):
            raise VekaError('malformed conversation observation')
        pid, family, scenario, lang = (row[k] for k in (
            'participant_id', 'background_family', 'scenario_id', 'language'))
        if (not PSEUDONYM.fullmatch(pid) or not family.strip()
                or family != family.strip() or len(family) > 64
                or not re.fullmatch(r'[A-Za-z][A-Za-z -]{1,63}', family, re.ASCII)
                or scenario not in known or lang not in LANGUAGES):
            raise VekaError('invalid participant, background family, scenario or language')
        key = (pid, scenario)
        if key in seen:
            raise VekaError('participant saw the same scenario in multiple language conditions')
        seen.add(key)
        if pid in participants and participants[pid] != family:
            raise VekaError('participant has inconsistent background family')
        participants[pid] = family
        if row['correct'] not in ('0', '1') or row['critical_error'] not in ('0', '1'):
            raise VekaError('correct and critical_error must be 0 or 1')
        if row['correct'] == '1' and row['critical_error'] == '1':
            raise VekaError('a critical meaning error cannot be correct')
        for name in ('elapsed_ms', 'repair_ms'):
            value = row[name]
            if not value.isascii() or not value.isdecimal() or len(value) > 13 or (name == 'elapsed_ms' and int(value) == 0):
                raise VekaError('durations must be nonnegative ASCII decimal milliseconds; elapsed positive')
        normalized.append({
            'participant_id': pid, 'family': family, 'scenario': scenario,
            'language': lang, 'correct': int(row['correct']),
            'critical_error': int(row['critical_error']),
            'duration_ms': int(row['elapsed_ms']) + int(row['repair_ms']),
        })
    groups = defaultdict(set)
    for r in normalized:
        groups[(r['family'], r['scenario'])].add(r['language'])
    paired = sorted([{'background_family': f, 'scenario_id': s,
                      'languages': sorted(langs)}
                     for (f, s), langs in groups.items()
                     if 'veka' in langs and len(langs) > 1],
                    key=lambda r: (r['background_family'], r['scenario_id']))
    return {
        'schema_version': 'veka.conversation-score.v01',
        'observed': bool(normalized), 'participants': len(participants),
        'trial_count': len(normalized),
        'languages_observed': sorted({r['language'] for r in normalized}),
        'by_language': {lang: _stats([r for r in normalized if r['language'] == lang])
                        for lang in sorted({r['language'] for r in normalized})},
        'by_family': {
            family: {lang: _stats([r for r in normalized if r['family'] == family and r['language'] == lang])
                     for lang in sorted({r['language'] for r in normalized if r['family'] == family})}
            for family in sorted(set(participants.values()))
        },
        'balanced_scenario_family_cells': len(paired),
        'veka_comparator_cells': paired,
        'unpaired_scenario_family_cells': len(groups) - len(paired),
        'canonical_changes': 0, 'human_benefit_established': False,
        'comparative_benefit_established': False,
        'warning': ('Purely descriptive; labels, recordings, translations, participant independence '
                    'and randomization are not authenticated. Paired cells indicate coverage, not '
                    'matched statistical power. No confidence intervals, winner or adoption authorization.'),
    }
