"""Audit taught canonical roots without inventing human frequency evidence.

Curated lessons are not representative spoken-language frequency corpora.
Transparent compounds contribute their existing noun and adjective roots.
"""
from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path

from .core import Lexicon, VekaError, parse
from .everyday import load_lessons
from .lessons import LESSONS
from .profiles import load_profile

SCHEMA = 'veka.learner-core.v01'
CRITICAL_CONTRASTS = (('mi', 'ti'), ('ne', 'na'), ('ran', 'ren'))


def load_learner_examples_csv(path: str | Path) -> list[str]:
    """Read a bounded, unscored one-column list of researcher-authored examples.

    No correctness label, scenario meaning, speaker demographic or purported
    participant score is accepted; parsing happens in audit_learner_core.
    """
    try:
        source = Path(path)
        if source.stat().st_size > 1048576:
            raise VekaError('learner corpus exceeds 1 MiB')
        with source.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames != ['sentence']:
                raise VekaError('learner corpus requires exactly the sentence column')
            sentences = []
            for row in reader:
                if (list(row) != ['sentence'] or not isinstance(row['sentence'], str)
                        or not row['sentence'] or len(row['sentence']) > 1024):
                    raise VekaError('malformed learner corpus sentence')
                sentences.append(row['sentence'])
                if len(sentences) > 500:
                    raise VekaError('learner corpus exceeds 500 sentences')
    except (UnicodeError, csv.Error) as exc:
        raise VekaError('invalid UTF-8 learner corpus CSV') from exc
    if not sentences:
        raise VekaError('learner corpus must contain examples')
    return sentences


def _examples(sentences: list[str] | None) -> tuple[list[tuple[str, str, int]], str]:
    if sentences is not None:
        if (not isinstance(sentences, list) or not sentences or len(sentences) > 500
                or any(not isinstance(s, str) or not s or len(s) > 1024 for s in sentences)):
            raise VekaError('supplied lesson corpus must contain 1..500 short sentences')
        return [(s, 'supplied_canonical_examples', 1) for s in sentences], 'supplied_canonical_examples_not_usage_sample'
    examples = [(example['veka'], f'beginner_level_{level["level"]}', level['level'])
                for level in load_lessons() for example in level['examples']]
    examples.extend((lesson[0], 'trilingual_lessons', 5) for lesson in LESSONS)
    return examples, 'curated_editorial_lessons_not_usage_sample'


def _roots_in_sentence(sentence: str, lex: Lexicon) -> tuple[list[str], list[str]]:
    if (not isinstance(sentence, str) or not sentence or sentence != sentence.strip()
            or len(sentence) > 1024):
        raise VekaError('lesson sentence must be bounded and trimmed')
    parse(sentence, lex, strict=True)
    words = sentence[:-1] if sentence.endswith(('.', '!', '?')) else sentence
    roots, compounds = [], []
    for token in words.split():
        entry = lex.get(token.lower())
        if entry is None:
            raise VekaError(f'learner inventory requires known canonical words: {token}')
        if entry.kind == 'root':
            roots.append(entry.form)
        elif entry.kind == 'compound':
            head, modifier = lex.get(entry.head), lex.get(entry.modifier)
            if (entry.form != f'{entry.head}-{entry.modifier}'
                    or entry.pos != 'noun' or head is None or modifier is None
                    or head.kind != 'root' or head.pos != 'noun'
                    or modifier.kind != 'root' or modifier.pos != 'adjective'):
                raise VekaError(f'cannot decompose nontransparent compound: {entry.form}')
            roots.extend((head.form, modifier.form))
            compounds.append(entry.form)
        else:
            raise VekaError(f'unsupported lexical classification: {token}')
    return roots, compounds


def audit_learner_core(*, budget: int = 20, sentences: list[str] | None = None,
                       lex: Lexicon | None = None) -> dict:
    """Deterministic curricular exposure and lexical-coverage report, not fluency."""
    lex = load_profile('tonal') if lex is None else lex
    root_entries = {e.form: e for e in lex.values() if e.kind == 'root'}
    compounds = [e for e in lex.values() if e.kind == 'compound']
    if type(budget) is not int or not 1 <= budget <= len(root_entries):
        raise VekaError(f'budget must be between 1 and {len(root_entries)} roots')
    examples, corpus_type = _examples(sentences)
    seen_sentences: set[str] = set()
    unique = []
    occurrences: Counter[str] = Counter()
    sentence_exposure: Counter[str] = Counter()
    compound_occurrences: Counter[str] = Counter()
    first_stage: dict[str, int] = {}
    first_source: dict[str, str] = {}
    for sentence, source, stage in examples:
        roots, used_compounds = _roots_in_sentence(sentence, lex)
        key = sentence.casefold().rstrip('.?!')
        if key in seen_sentences:
            if sentences is not None:
                raise VekaError('supplied corpus contains duplicate canonical examples')
            continue
        seen_sentences.add(key)
        unique.append((sentence, set(roots)))
        occurrences.update(roots)
        sentence_exposure.update(set(roots))
        compound_occurrences.update(used_compounds)
        for root in roots:
            if root not in first_stage:
                first_stage[root] = stage
                first_source[root] = source

    inventory = [dict(form=form, gloss=root_entries[form].gloss,
                      part_of_speech=root_entries[form].pos, kind='root',
                      token_occurrences=occurrences[form],
                      sentence_occurrences=sentence_exposure[form],
                      first_taught_in=first_source[form])
                 for form in sorted(occurrences,
                                    key=lambda f: (first_stage[f], -sentence_exposure[f],
                                                   -occurrences[f], f))]
    selected = inventory[:budget]
    selected_forms = {item['form'] for item in selected}
    uncovered = [dict(sentence=s, missing_roots=sorted(roots - selected_forms))
                 for s, roots in unique if not roots.issubset(selected_forms)]
    for forms in CRITICAL_CONTRASTS:
        if any(form not in root_entries for form in forms):
            raise VekaError('critical contrast has missing canonical root')
    return {
        'schema_version': SCHEMA,
        'corpus': {
            'type': corpus_type,
            'sources': ['beginner_lessons_v09', 'trilingual_lessons'] if sentences is None
                       else ['supplied_canonical_examples'],
            'source_examples': len(examples),
            'unique_sentences': len(unique),
            'deduped_examples': len(examples) - len(unique),
        },
        'lexicon': {
            'root_count': len(root_entries),
            'transparent_compound_count': len(compounds),
            'total_headwords': len(lex),
            'compound_memorization_policy': 'transparent_composition_not_additional_atomic_roots',
        },
        'root_inventory': inventory,
        'selected_roots': selected,
        'root_types_observed': len(inventory),
        'root_tokens_observed': sum(occurrences.values()),
        'roots_not_yet_in_sample': len(root_entries) - len(inventory),
        'compounds_observed': [dict(form=form, noun=lex[form].head,
                                    adjective=lex[form].modifier, uses=count)
                               for form, count in sorted(compound_occurrences.items())],
        'coverage': {
            'budget': budget,
            'selected_root_count': len(selected),
            'fully_lexically_covered_sentences': len(unique) - len(uncovered),
            'total_sentences': len(unique),
            'uncovered_examples': uncovered,
            'meaning_comprehension_established': False,
        },
        'critical_contrasts': [dict(
            forms=list(pair),
            curriculum_token_occurrences={form: occurrences[form] for form in pair},
            not_seen_in_curriculum=[form for form in pair if not occurrences[form]],
            acoustic_confusion_measured=False,
        ) for pair in CRITICAL_CONTRASTS],
        'ranking_basis': 'earliest_taught_stage_then_distinct_example_occurrences; not natural usage frequency',
        'natural_language_frequency_measured': False,
        'human_comprehension_validated': False,
        'canonical_lexicon_modified': False,
        'warning': ('Curated, partly duplicated lesson examples are not a representative frequency corpus. '
                    'Lexical coverage and compound decomposition cannot establish comprehension, '
                    'spoken distinctness, frequency, retention or any learner-group advantage. '
                    'The 100 English-only everyday scenarios have no approved Veka translations '
                    'and are therefore excluded.'),
    }
