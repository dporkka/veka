"""Pre-registrable, condition-blinded spoken-aesthetics assignment generator.

Outputs placeholder stimuli, NOT speech recordings, ratings, or comprehension data.
The researcher key must not be shared with participants during the experiment.
"""
from __future__ import annotations

import csv
import hashlib
import os
import random
import re
from pathlib import Path

from .core import VekaError, parse
from .logic import parse_logic
from .profiles import load_profile, PROFILES

DELIVERIES = ('baseline', 'guided')
REQUIRED = frozenset(('id', 'meaning', 'tonal', 'toneless', 'category', 'critical'))


def _strict_sentence(text: str, lexicon) -> bool:
    try:
        parse(text, lexicon, strict=True)
        return True
    except VekaError:
        try:
            parse_logic(text, lexicon, strict=True)
            return True
        except VekaError as exc:
            raise VekaError(f'invalid study stimulus {text!r}: {exc}') from exc


def generate_spoken_manifest(
    items: list[dict], participant_id: str, profile: str, arm: int,
    seed: int = 20261101,
) -> tuple[list[dict], list[dict]]:
    """Assign each meaning once, counterbalancing delivery across two arms.

    Profiles are separated between participants to avoid cross-profile exposure.
    This only generates assignments; recordings must be obtained independently.
    """
    if not isinstance(participant_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', participant_id):
        raise VekaError('participant_id must be 1..64 letters, digits, underscores or hyphens')
    if profile not in PROFILES:
        raise VekaError(f'unsupported study profile: {profile}')
    if type(arm) is not int or arm not in (0, 1):
        raise VekaError('arm must be explicitly assigned as 0 or 1')
    if type(seed) is not int:
        raise VekaError('seed must be an integer')
    if not isinstance(items, list) or len(items) < 2 or len(items) % 2:
        raise VekaError('study requires an even number of at least two items')
    if len(items) > 128:
        raise VekaError('study item limit is 128')
    forms = {name: load_profile(name) for name in PROFILES}
    seen = set()
    trials = []
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not REQUIRED.issubset(item):
            raise VekaError('study item missing required fields')
        identity = item['id']
        if not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', identity) or identity in seen:
            raise VekaError('duplicate or malformed item identifier')
        seen.add(identity)
        if item['critical'] not in (0, 1) or type(item['critical']) is not int:
            raise VekaError('critical must be 0 or 1')
        if not all(isinstance(item[k], str) and item[k].strip() for k in
                   ('meaning','tonal','toneless','category')):
            raise VekaError('empty or malformed study stimulus')
        for name in PROFILES:
            _strict_sentence(item[name], forms[name])
        delivery = DELIVERIES[(index + arm) % 2]
        token = hashlib.sha256(
            f'{seed}:{participant_id}:{identity}'.encode('utf-8')
        ).hexdigest()[:20]
        trials.append({
            'stimulus_id': f'S{token}',
            'item_id': identity,
            'meaning': item['meaning'],
            'category': item['category'],
            'utterance': item[profile],
            'profile': profile,
            'delivery': delivery,
            'critical': item['critical'],
            'recording_filename': f'S{token}.wav',
            'audio_recorded': 'false',
        })
    random.Random(f'spoken:{seed}:{participant_id}').shuffle(trials)
    # Researcher data contains condition labels and text; participant sheet does not.
    participant, researcher = [], []
    for number, item in enumerate(trials, 1):
        trial_id = f'T{number:03d}'
        participant.append({
            'participant_id': participant_id, 'trial_id': trial_id,
            'stimulus_id': item['stimulus_id'],
            'pleasantness_1_7': '', 'naturalness_1_7': '',
            'comprehension_response': '', 'elapsed_ms': '',
            'repairs': '',
        })
        researcher.append({
            'participant_id': participant_id, 'trial_id': trial_id, **item,
        })
    return participant, researcher


def write_spoken_manifest(
    items: list[dict], participant_id: str, profile: str, arm: int,
    output: str | Path, researcher_key: str | Path, seed: int = 20261101,
) -> dict:
    participant, researcher = generate_spoken_manifest(
        items, participant_id, profile, arm, seed
    )
    visible = Path(output)
    secret = Path(researcher_key)
    if visible.resolve() == secret.resolve():
        raise VekaError('participant sheet and researcher key must have separate paths')
    if visible.exists() or secret.exists():
        raise VekaError('refusing to overwrite participant sheet or researcher key')
    created = []
    try:
        for path, rows in ((visible, participant), (secret, researcher)):
            # Create private by default, including on shared research machines.
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            created.append(path)
            with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    except (OSError, ValueError):
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return {
        'participant_id': participant_id, 'profile': profile, 'arm': arm,
        'trial_count': len(participant),
        'baseline_trials': sum(r['delivery']=='baseline' for r in researcher),
        'guided_trials': sum(r['delivery']=='guided' for r in researcher),
        'participant_sheet': str(visible), 'researcher_key': str(secret),
        'audio_recorded': False, 'human_data_collected': False,
    }
