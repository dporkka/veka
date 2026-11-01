"""Opt-in six-language research cohorts for Veka loanword recognition.

This generates reproducible blind packets, never proposed canonical forms.
Language labels are sampling strata, NOT inferred linguistic competence.
No new translations, etymologies, human outcomes, or audio are generated.
"""
from __future__ import annotations

from collections import Counter
from .core import Lexicon, VekaError
from .international import generate_recognition_manifest, summarize_recognition_scores

# Explicit language codes; shared macrofamily labels MUST NOT be counted as
# independent evidence for English, Hindi, Spanish, and Portuguese.
LANGUAGE_GROUPS = {
    'en': {'name': 'English', 'family': 'Indo-European'},
    'cmn': {'name': 'Mandarin Chinese', 'family': 'Sino-Tibetan'},
    'es': {'name': 'Spanish', 'family': 'Indo-European'},
    'hi': {'name': 'Hindi', 'family': 'Indo-European'},
    'pt': {'name': 'Portuguese', 'family': 'Indo-European'},
    'id': {'name': 'Indonesian', 'family': 'Austronesian'},
}


def make_cohort(rows: list[dict], lexicon: Lexicon,
                participants_per_language: int = 2, seed: int = 20261101
                ) -> tuple[list[dict], list[dict]]:
    """Balanced written core-vs-draft pilot, with one version/concept/person.

    Pseudonyms are synthetic pair IDs, NOT identifying participant records.
    Allocate IDs independently of recruitment order to avoid systematic
    differences between assigned conditions and participant backgrounds.
    """
    if (type(participants_per_language) is not int
            or not 2 <= participants_per_language <= 200
            or participants_per_language % 2):
        raise VekaError('participants per language must be an even integer from 2 to 200')
    if type(seed) is not int:
        raise VekaError('seed must be an integer')
    participant_sheets: list[dict] = []
    researcher_key: list[dict] = []
    for code, details in LANGUAGE_GROUPS.items():
        for pair in range(1, participants_per_language // 2 + 1):
            for arm in ('A', 'B'):
                pid = f'V07-{code}-{pair:03d}-{arm}'
                visible, key = generate_recognition_manifest(rows, lexicon, pid, seed)
                # A/B differ by exactly one code point: invert per-concept
                # assignment across adjacent participants, not within person.
                participant_sheets.extend(dict(row, language=code) for row in visible)
                researcher_key.extend(dict(row, language=code,
                                           family=details['family']) for row in key)
    # Check design, not human recognition. Fail closed if upstream logic changes.
    per_participant: dict[str, Counter] = {}
    per_concept: dict[tuple[str, str], Counter] = {}
    for row in researcher_key:
        per_participant.setdefault(row['participant_id'], Counter())[row['condition']] += 1
        per_concept.setdefault((row['language'], row['concept_id']), Counter())[row['condition']] += 1
    if not per_participant or any(c['core'] != c['international'] for c in per_participant.values()):
        raise VekaError('unbalanced per-participant assignment')
    if any(c['core'] != c['international'] for c in per_concept.values()):
        raise VekaError('unbalanced per-language concept assignment')
    if len({row['trial_id'] for row in researcher_key}) != len(researcher_key):
        raise VekaError('duplicate trial IDs')
    return participant_sheets, researcher_key


def score_cohort(key: list[dict], annotated: list[dict]) -> dict:
    """Descriptive per-language stats from independently adjudicated outcomes.

    Do not present differences as treatment effects, language abilities or
    representative population estimates. The caller must verify provenance.
    """
    if not key:
        raise VekaError('multilingual answer key is empty')
    required_key = ('trial_id', 'participant_id', 'concept_id', 'language',
                    'family', 'condition', 'status')
    for row in key:
        if (not all(isinstance(row.get(field), str) and row[field].strip()
                    for field in required_key)
                or row['condition'] not in ('core', 'international')
                or row['status'] != 'unverified_draft'):
            raise VekaError('incomplete or invalid multilingual answer key')
    if len({row['trial_id'] for row in key}) != len(key):
        raise VekaError('duplicate multilingual trial ID')
    for row in annotated:
        if not isinstance(row.get('trial_id'), str) or not row['trial_id'].strip():
            raise VekaError('annotation missing trial ID')
    participants: dict[str, str] = {}
    by_participant: dict[str, Counter] = {}
    by_concept: dict[tuple[str, str], Counter] = {}
    seen_participant_concept = set()
    for row in key:
        code = row.get('language')
        if code not in LANGUAGE_GROUPS or row.get('family') != LANGUAGE_GROUPS[code]['family']:
            raise VekaError('invalid language or family in answer key')
        pid = row.get('participant_id', '')
        if not isinstance(pid, str) or not pid.startswith(f'V07-{code}-'):
            raise VekaError('participant ID does not match language stratum')
        if pid in participants and participants[pid] != code:
            raise VekaError('participant assigned multiple language strata')
        participants[pid] = code
        pair = (pid, row['concept_id'])
        if pair in seen_participant_concept:
            raise VekaError('participant saw a repeated concept')
        seen_participant_concept.add(pair)
        by_participant.setdefault(pid, Counter())[row['condition']] += 1
        by_concept.setdefault((code, row['concept_id']), Counter())[row['condition']] += 1
    if (any(count['core'] != count['international'] for count in by_participant.values())
            or any(count['core'] != count['international'] for count in by_concept.values())):
        raise VekaError('answer key has unbalanced experimental assignments')

    # The existing scorer strictly validates matching trial IDs, complete
    # human-judged binary correctness, timing and repair_count.
    overall = summarize_recognition_scores(key, annotated)
    by_id = {row['trial_id']: row for row in annotated}
    strata = {}
    for code, details in LANGUAGE_GROUPS.items():
        subkey = [row for row in key if row['language'] == code]
        if not subkey:
            raise VekaError(f'missing language stratum: {code}')
        subscored = [by_id[row['trial_id']] for row in subkey]
        stat = summarize_recognition_scores(subkey, subscored)
        if set(stat['conditions']) != {'core', 'international'}:
            raise VekaError(f'missing pilot condition in {code}')
        strata[code] = {
            'language': details['name'],
            'family': details['family'],
            'participants': len({row['participant_id'] for row in subkey}),
            'n': stat['trials'],
            'conditions': stat['conditions'],
        }
    return {
        'schema_version': 'veka.international-cohort.v07',
        'trials': overall['trials'],
        'participants': len(participants),
        'languages': strata,
        'overall': overall['conditions'],
        'causal_effect_established': False,
        'human_observations_independently_verified': False,
        'warning': ('Descriptive scores only. Validate real consent, language history, '
                    'judge blinding, trial completeness, prior exposure, sampling '
                    'and uncertainty before interpreting differences. '
                    'Languages sharing a family are not independent attestations.'),
    }
