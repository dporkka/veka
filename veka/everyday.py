"""Everyday communication requirements and a canonical beginner curriculum.

The dialogues are English requirements, not claimed Veka translations. The
beginner examples are editorial English glosses of parser-accepted Veka.
Neither audit measures human comprehension, speed or learnability.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .core import VekaError
from .registers import inspect_register

DATA = Path(__file__).resolve().parents[1] / 'data'
DIALOGUES = DATA / 'everyday_dialogues_v09.json'
LESSONS = DATA / 'beginner_lessons_v09.json'
EXPECTED_DOMAINS = frozenset({
    'introductions', 'essentials', 'navigation', 'commerce', 'scheduling',
    'social', 'clarification', 'planning', 'teamwork', 'numeracy',
})


def _document(path: str | Path) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding='utf-8'))
    except (ValueError, OSError, TypeError) as exc:
        raise VekaError(f'cannot read everyday resource: {exc}') from exc
    if not isinstance(doc, dict):
        raise VekaError('everyday resource must be a JSON object')
    return doc


def _validate_dialogues(rows: list) -> None:
    if not isinstance(rows, list):
        raise VekaError('dialogue items must be an array')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise VekaError('dialogue item must be an object')
        identifier = row.get('id')
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise VekaError('missing or duplicate dialogue id')
        seen.add(identifier)
        if row.get('domain') not in EXPECTED_DOMAINS:
            raise VekaError(f'invalid dialogue domain: {identifier}')
        if not isinstance(row.get('scenario'), str) or not row['scenario'].strip():
            raise VekaError(f'missing scenario: {identifier}')
        if row.get('translation_status') != 'not_attempted' or 'veka' in row:
            raise VekaError(f'unreviewed dialogue cannot claim a Veka translation: {identifier}')
        turns = row.get('turns')
        if not isinstance(turns, list) or len(turns) != 2 or any(
            not isinstance(turn, dict) or turn.get('speaker') != speaker
            or not isinstance(turn.get('text'), str) or not turn['text'].strip()
            for turn, speaker in zip(turns, ('A', 'B'))
        ):
            raise VekaError(f'expected A/B English turns: {identifier}')
        features = row.get('required_features')
        if not isinstance(features, list) or not features or any(
            not isinstance(feature, str) or not feature or not feature.replace('_', '').isalpha()
            for feature in features
        ):
            raise VekaError(f'invalid required_features: {identifier}')


def load_dialogues(path: str | Path = DIALOGUES) -> list[dict]:
    doc = _document(path)
    if doc.get('schema_version') != 'veka.everyday-requirements.v09' or doc.get('language') != 'en':
        raise VekaError('unknown everyday dialogue schema or language')
    rows = doc.get('items')
    _validate_dialogues(rows)
    if len(rows) != 100 or any(sum(r['domain'] == name for r in rows) != 10
                               for name in EXPECTED_DOMAINS):
        raise VekaError('the frozen v0.9 evaluation set needs 10 items in each of 10 domains')
    if len({r['scenario'] for r in rows}) != len(rows):
        raise VekaError('duplicate scenario identifiers')
    return rows


def audit_dialogues(*, rows: list[dict] | None = None,
                    domain: str | None = None, include_items: bool = False) -> dict:
    """Inventory human-authored requirements; do not claim parser coverage."""
    items = load_dialogues() if rows is None else rows
    _validate_dialogues(items)
    if domain is not None and domain not in EXPECTED_DOMAINS:
        raise VekaError(f'unknown everyday domain: {domain}')
    filtered = [r for r in items if domain is None or r['domain'] == domain]
    by_domain = Counter(row['domain'] for row in filtered)
    feature_counts = Counter(feature for row in filtered for feature in row['required_features'])
    result = {
        'schema_version': 'veka.everyday-audit.v09',
        'scope': domain or 'all',
        'total_scenarios': len(filtered),
        'domains': dict(sorted(by_domain.items())),
        'required_feature_counts': dict(sorted(feature_counts.items())),
        'not_attempted': len(filtered),
        'machine_translations_verified': 0,
        'human_comprehension_validated': False,
        'language_coverage_established': False,
        'interpretation': 'English-only requirements; feature tags identify needs, not gaps verified against full Veka semantics.',
    }
    if include_items:
        result['items'] = filtered
    return result


def load_lessons(path: str | Path = LESSONS) -> list[dict]:
    doc = _document(path)
    if doc.get('schema_version') != 'veka.beginner-lessons.v09':
        raise VekaError('unknown beginner lesson schema')
    rows = doc.get('lessons')
    if not isinstance(rows, list) or [r.get('level') for r in rows if isinstance(r, dict)] != [1, 2, 3, 4]:
        raise VekaError('expected four ordered beginner levels')
    for level in rows:
        if not isinstance(level.get('title'), str) or not level['title'].strip():
            raise VekaError('beginner lesson missing title')
        examples = level.get('examples')
        if not isinstance(examples, list) or len(examples) < 3:
            raise VekaError('beginner lesson requires at least three examples')
        for example in examples:
            if not isinstance(example, dict) or not isinstance(example.get('english'), str) or not example['english'].strip():
                raise VekaError('beginner example requires an editorial English gloss')
            try:
                parsed = inspect_register(example.get('veka'), max_register='core')
            except VekaError as exc:
                raise VekaError(f'beginner example is not canonical: {exc}') from exc
            if parsed['register'] != 'core' or not parsed['canonical_lexicon']:
                raise VekaError('beginner examples must be canonical tonal Veka')
    return rows


def get_lesson(level: int) -> dict:
    if level not in (1, 2, 3, 4):
        raise VekaError(f'unknown beginner level: {level}')
    lesson = load_lessons()[level-1]
    return {
        'schema_version': 'veka.learn.v09',
        **lesson,
        'profile': 'tonal',
        'grammar_register': 'core',
        'editorial_translation': True,
        'machine_syntax_verified': True,
        'human_learning_validated': False,
        'warning': 'Parser approval is not comprehension, fluency, or translation-quality validation.',
    }
