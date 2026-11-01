"""Strict, noncanonical first-sight root study adjudication.

Separates the private researcher key from an unscored reviewer sheet.
The program never judges natural-language synonyms and cannot authenticate
recruitment, participant consent, independent reviewers or recorded answers.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from .cohort_plan import PSEUDONYM, _private_csv
from .core import Lexicon, VekaError
from .global_comprehension import read_global_csv
from .international import audit_candidates

KEY_FIELDS = ('participant_id', 'trial_id', 'concept_id', 'target_gloss',
              'condition', 'presented_form', 'background_stratum')
PARTICIPANT_FIELDS = ('participant_id', 'trial_id', 'presented_form',
                      'response_gloss', 'response_ms', 'prior_exposure',
                      'presentation_modality')
REVIEW_FIELDS = ('participant_id', 'trial_id', 'target_gloss', 'response_gloss',
                 'correct', 'critical_error', 'reviewer_id', 'review_note')
TRIAL_ID = re.compile(r'V12-[0-9a-f]{16}\Z', re.ASCII)


def read_root_review(path: str | Path) -> list[dict[str, str]]:
    return read_global_csv(path, REVIEW_FIELDS)


def _validated_keys(keys: list[dict], candidates: list[dict], lex: Lexicon) -> dict:
    audited = audit_candidates(candidates, lex)
    usable = {item['concept_id']: item for item in audited['candidates']
              if item['status'] == 'structurally_testable'}
    if not usable or audited['rejected_forms'] or len(usable) % 2 or not keys:
        raise VekaError('root study requires valid experimental concepts and a private key')
    seen, participants, cells, trials = set(), defaultdict(list), Counter(), {}
    for row in keys:
        if (not isinstance(row, dict) or tuple(row) != KEY_FIELDS
                or any(not isinstance(row[f], str) for f in KEY_FIELDS)):
            raise VekaError('malformed root study researcher key')
        pid, trial, cid = row['participant_id'], row['trial_id'], row['concept_id']
        condition = row['condition']
        if (not PSEUDONYM.fullmatch(pid) or not TRIAL_ID.fullmatch(trial)
                or cid not in usable or condition not in ('core', 'candidate')):
            raise VekaError('invalid root study participant, trial, concept or condition')
        concept = usable[cid]
        expected = concept['core_form' if condition == 'core' else 'candidate_form']
        if (row['presented_form'] != expected or row['target_gloss'] != concept['gloss']):
            raise VekaError('researcher key does not match frozen research vocabulary')
        background = row['background_stratum']
        if (not 2 <= len(background) <= 64 or background != background.strip()
                or background[0] in '=+-@'
                or any(ord(ch) < 32 or ch in '/\\' for ch in background)):
            raise VekaError('unsafe root study background label')
        if trial in trials or (pid, cid) in seen:
            raise VekaError('duplicate trial or repeated concept exposure')
        seen.add((pid, cid))
        trials[trial] = row
        participants[pid].append(row)
        cells[(background, cid, condition)] += 1
    groups = defaultdict(set)
    for pid, rows in participants.items():
        groups[rows[0]['background_stratum']].add(pid)
        if (len(rows) != len(usable) or
                {r['concept_id'] for r in rows} != set(usable) or
                {r['background_stratum'] for r in rows} != {rows[0]['background_stratum']} or
                Counter(r['condition'] for r in rows) !=
                {'core': len(usable) // 2, 'candidate': len(usable) // 2}):
            raise VekaError('incomplete or inconsistent researcher assignment')
    for background, people in groups.items():
        if len(people) < 2 or len(people) % 2:
            raise VekaError('root study background stratum is not balanced')
        for cid in usable:
            if cells[(background, cid, 'core')] != cells[(background, cid, 'candidate')]:
                raise VekaError('root study assignment is not balanced by concept and background')
    return trials


def _observations(keys: list[dict], responses_dir: str | Path,
                  candidates: list[dict], lex: Lexicon) -> dict:
    trials = _validated_keys(keys, candidates, lex)
    directory = Path(responses_dir)
    if not directory.is_dir() or directory.is_symlink():
        raise VekaError('responses directory must exist and not be a symbolic link')
    participant_ids = {row['participant_id'] for row in keys}
    if {p.name for p in directory.glob('*.csv')} != {pid + '.csv' for pid in participant_ids}:
        raise VekaError('response files must match precisely the researcher roster')
    observed = {}
    for pid in sorted(participant_ids):
        path = directory / f'{pid}.csv'
        if path.is_symlink() or not path.is_file():
            raise VekaError('participant response file is missing or is a symbolic link')
        rows = read_global_csv(path, PARTICIPANT_FIELDS)
        expected = {r['trial_id']: r for r in keys if r['participant_id'] == pid}
        if len(rows) != len(expected):
            raise VekaError('missing or extra participant response trial')
        for row in rows:
            trial = row['trial_id']
            if (row['participant_id'] != pid or trial not in expected
                    or trial in observed
                    or row['presented_form'] != expected[trial]['presented_form']
                    or row['presentation_modality'] != 'written'):
                raise VekaError('participant packet contradicts blinded researcher assignment')
            response = row['response_gloss']
            if (not response.strip() or len(response) > 1000
                    or response.lstrip()[0] in '=+-@'
                    or any(ord(ch) < 32 for ch in response)):
                raise VekaError('unsafe, empty or excessive first-sight response')
            duration = row['response_ms']
            if (not duration.isascii() or not duration.isdecimal()
                    or len(duration) > 12 or int(duration) == 0):
                raise VekaError('response duration must be positive ASCII milliseconds')
            if row['prior_exposure'] not in ('yes', 'no', 'unknown'):
                raise VekaError('prior exposure requires yes, no, or unknown')
            observed[trial] = row
    if set(observed) != set(trials):
        raise VekaError('missing root study observations')
    return observed


def build_root_review(keys: list[dict], responses_dir: str | Path,
                      candidates: list[dict], lex: Lexicon) -> list[dict[str, str]]:
    """Create manual reviewer input with target/response, never the form/condition."""
    observations = _observations(keys, responses_dir, candidates, lex)
    return [{
        'participant_id': key['participant_id'],
        'trial_id': key['trial_id'],
        'target_gloss': key['target_gloss'],
        'response_gloss': observations[key['trial_id']]['response_gloss'],
        'correct': '', 'critical_error': '', 'reviewer_id': '', 'review_note': '',
    } for key in sorted(keys, key=lambda k: (k['participant_id'], k['trial_id']))]


def write_root_review(rows: list[dict], path: str | Path) -> None:
    """Create a private, no-overwrite, manually scored review CSV."""
    target = Path(path)
    if not rows or any(tuple(row) != REVIEW_FIELDS for row in rows):
        raise VekaError('invalid root review export')
    if target.is_symlink():
        raise VekaError('refusing review-sheet symbolic link')
    try:
        _private_csv(target, rows)
    except OSError as exc:
        raise VekaError('cannot create private root review file; refusing overwrite') from exc


def _stats(rows: list[dict]) -> dict:
    n = len(rows)
    total = sum(r['elapsed_ms'] for r in rows)
    return {
        'trials': n,
        'correct': sum(r['correct'] for r in rows),
        'critical_errors': sum(r['critical_error'] for r in rows),
        'prior_exposure_yes': sum(r['prior_exposure'] == 'yes' for r in rows),
        'prior_exposure_unknown': sum(r['prior_exposure'] == 'unknown' for r in rows),
        'accuracy': sum(r['correct'] for r in rows) / n if n else None,
        'mean_written_response_ms': round(total / n, 2) if n else None,
    }


def score_root_review(keys: list[dict], responses_dir: str | Path,
                      reviews: list[dict], candidates: list[dict], lex: Lexicon) -> dict:
    """Descriptive, fully linked claims, not an inference or approval engine."""
    expected = {tuple(row[k] for k in ('participant_id', 'trial_id')): row
                for row in build_root_review(keys, responses_dir, candidates, lex)}
    observations = _observations(keys, responses_dir, candidates, lex)
    by_trial = {row['trial_id']: row for row in keys}
    if len(reviews) != len(expected):
        raise VekaError('all planned trials require one independent manual judgment')
    seen, normalized = set(), []
    for row in reviews:
        if (not isinstance(row, dict) or tuple(row) != REVIEW_FIELDS
                or any(not isinstance(row[k], str) for k in REVIEW_FIELDS)):
            raise VekaError('invalid manual judgment columns')
        identity = (row['participant_id'], row['trial_id'])
        if identity not in expected or identity in seen:
            raise VekaError('unknown or repeated root judgment')
        seen.add(identity)
        if any(row[k] != expected[identity][k] for k in
               ('participant_id', 'trial_id', 'target_gloss', 'response_gloss')):
            raise VekaError('manual judgment does not match the original response')
        if (row['correct'] not in ('0', '1') or row['critical_error'] not in ('0', '1')
                or (row['correct'], row['critical_error']) == ('1', '1')
                or not PSEUDONYM.fullmatch(row['reviewer_id'])
                or not row['review_note'].strip()):
            raise VekaError('manual judgment needs a reviewer, note and coherent binary scores')
        key = by_trial[row['trial_id']]
        observed = observations[row['trial_id']]
        normalized.append({
            'concept_id': key['concept_id'],
            'background': key['background_stratum'],
            'condition': key['condition'],
            'correct': int(row['correct']),
            'critical_error': int(row['critical_error']),
            'elapsed_ms': int(observed['response_ms']),
            'prior_exposure': observed['prior_exposure'],
        })
    if seen != set(expected):
        raise VekaError('incomplete judged study responses')
    conditions = ('core', 'candidate')
    backgrounds = sorted({r['background'] for r in normalized})
    concepts = sorted({r['concept_id'] for r in normalized})
    report = {
        'schema_version': 'veka.root-study-adjudication.v13',
        'participants': len({r['participant_id'] for r in keys}),
        'total_trials': len(normalized),
        'by_condition': {c: _stats([r for r in normalized if r['condition'] == c])
                         for c in conditions},
        'by_background': {
            b: {c: _stats([r for r in normalized if r['background'] == b and r['condition'] == c])
                for c in conditions} for b in backgrounds},
        'by_concept': {
            cid: {c: _stats([r for r in normalized if r['concept_id'] == cid and r['condition'] == c])
                  for c in conditions} for cid in concepts},
        'by_concept_and_background': {
            cid: {b: {c: _stats([r for r in normalized if r['concept_id'] == cid
                                  and r['background'] == b and r['condition'] == c])
                      for c in conditions} for b in backgrounds} for cid in concepts},
        'manual_judgments_claimed': len(normalized),
        'independent_human_data_verified': False,
        'comparative_benefit_established': False,
        'acoustic_comprehension_measured': False,
        'delayed_retention_measured': False,
        'adoption_authorized': False,
        'canonical_changes': 0,
        'warning': (
            'Scores are unverified manual verdicts on written first-sight responses, '
            'not independently authenticated observations. This tool verifies exact '
            'trial joins and descriptive coverage, not semantic correctness, blinding, '
            'consent, recruitment, statistical power or reviewer independence. '
            'A positive descriptive difference is not evidence of causal superiority. '
            'No canonical Veka root is replaced or authorized for adoption.'
        ),
    }
    return report
