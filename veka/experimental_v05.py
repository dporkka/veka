"""Noncanonical Veka 0.5 semantics and opt-in productive verb derivation.

The approved 0.3 lexicon and default parser remain unchanged. Markers and
meanings are *engineering proposals*, not empirically validated vocabulary.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .core import Entry, Lexicon, VekaError, validate_word


@dataclass(frozen=True)
class DerivationRule:
    name: str
    marker: str
    source_pos: str
    result_pos: str
    semantic_role: str
    requires_transitive: bool = False


# Every marker is a provisional, otherwise unused legal syllable. The visible
# hyphen is an existing Veka syllable boundary; no segment is silently dropped.
DERIVATIONS = {
    'agent': DerivationRule('agent', 'rik', 'verb', 'noun', 'subject participant'),
    'patient': DerivationRule('patient', 'mol', 'verb', 'noun', 'direct-object participant', True),
    'instrument': DerivationRule('instrument', 'zas', 'verb', 'noun', 'potential instrument'),
    'place': DerivationRule('place', 'dai', 'verb', 'noun', 'place where action occurs'),
    'repeat': DerivationRule('repeat', 'koin', 'verb', 'verb', 'repeat event'),
    'passive_able': DerivationRule('passive_able', 'vau', 'verb', 'adjective',
                                   'patient has potential to undergo action', True),
}


@dataclass(frozen=True)
class DerivedWord:
    form: str
    base: str
    operation: str
    marker: str
    pos: str
    role: str
    valency: str
    source_valency: str
    meaning: str
    canonical: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def _check_rules(lex: Lexicon) -> None:
    markers = set()
    for op, rule in DERIVATIONS.items():
        if rule.name != op or not validate_word(rule.marker) or '-' in rule.marker:
            raise VekaError(f'invalid experimental derivational operator {op}')
        if rule.marker in markers or rule.marker in lex:
            raise VekaError(f'operator marker collision: {rule.marker}')
        markers.add(rule.marker)


def derive(base: str, operation: str, lex: Lexicon) -> DerivedWord:
    """Derive from a canonical verb root, never from arbitrary compounds.

    The role is a typed interpretation; the existence of an instrument,
    patient, etc. is NOT entailed by morphology alone.
    """
    _check_rules(lex)
    if operation not in DERIVATIONS:
        raise VekaError(f'unknown experimental operation: {operation}')
    rule = DERIVATIONS[operation]
    source = lex.get(base)
    if not source or source.kind != 'root' or source.pos != rule.source_pos:
        raise VekaError('derivation requires a canonical verb root')
    if source.valency not in ('transitive', 'intransitive'):
        raise VekaError('source valency must be explicit')
    if rule.requires_transitive and source.valency != 'transitive':
        raise VekaError(f'{operation} requires a transitive root with a direct object')
    form = f'{base}-{rule.marker}'
    if not validate_word(form) or form in lex:
        raise VekaError(f'proposed derivative collides or violates phonology: {form}')
    result_valency = source.valency if rule.result_pos == 'verb' else ''
    meanings = {
        'agent': f'subject participant in action: {source.gloss}',
        'patient': f'direct-object participant of action: {source.gloss}',
        'instrument': f'possible instrument for action: {source.gloss}',
        'place': f'place in which action occurs: {source.gloss}',
        'repeat': f'perform action again with same valency: {source.gloss}',
        'passive_able': f'able to undergo action as object: {source.gloss}',
    }
    return DerivedWord(form, base, operation, rule.marker, rule.result_pos,
                       rule.name, result_valency, source.valency,
                       meanings[operation])


def parse_derivative(form: str, lex: Lexicon) -> DerivedWord:
    """Exact, reversible two-part decoding; no guesswork or recursive stacking."""
    if not isinstance(form, str) or form.count('-') != 1:
        raise VekaError('derivative must have exactly one root and one operator')
    base, marker = form.split('-')
    ops = [name for name, rule in DERIVATIONS.items() if rule.marker == marker]
    if len(ops) != 1:
        raise VekaError('unregistered experimental operator marker')
    return derive(base, ops[0], lex)


def experimental_lexicon(canonical: Lexicon) -> Lexicon:
    """Copy, then extend. Never mutate or promote the caller's lexicon."""
    _check_rules(canonical)
    generated = Lexicon(canonical)
    for entry in tuple(canonical.values()):
        if entry.kind == 'root' and entry.pos == 'verb':
            for operator in DERIVATIONS:
                if DERIVATIONS[operator].requires_transitive and entry.valency != 'transitive':
                    continue
                word = derive(entry.form, operator, canonical)
                if word.form in generated:
                    raise VekaError('candidate derivative shadowed by existing form')
                generated[word.form] = Entry(word.form, word.meaning, word.pos,
                    'experimental_derived', 'experimental', entry.form,
                    word.marker, word.valency)
    return generated


# Values are typed semantic slots, not newly admitted lexical roots.
CORRELATIVE_SERIES = ('question', 'this', 'that', 'some', 'every', 'none')
CORRELATIVE_DIMENSIONS = ('person', 'thing', 'place', 'time')


def correlative(series: str, dimension: str, lex: Lexicon) -> dict:
    """A proposed 6x4 semantic grid with conservative spoken realization.

    Only two existing canonical quantifiers with existing canonical noun heads
    are spoken. Others have no Veka surface form, and are not accepted by the
    parser. In particular, 'none' cannot be silently equated to clause 'ne'.
    """
    if series not in CORRELATIVE_SERIES or dimension not in CORRELATIVE_DIMENSIONS:
        raise VekaError('unknown correlative series or dimension')
    base = {'person': 'ren', 'time': 'nus'}.get(dimension)
    quant = {'some': 'kis', 'every': 'al'}.get(series)
    if base and lex.get(base) and lex[base].pos == 'noun' and quant in lex:
        surface = f'{quant} {base}'
        status = 'existing_quantified_noun_phrase'
    else:
        surface = None
        status = 'semantic_design_only'
    return {
        'semantic_id': f'{series}:{dimension}', 'series': series,
        'dimension': dimension, 'surface': surface, 'status': status,
        'canonical_adopted': False,  # does not introduce any new canonical word
    }


def audit_experimental_v05(lex: Lexicon) -> dict:
    expanded = experimental_lexicon(lex)
    new_forms = set(expanded).difference(lex)
    for form in new_forms:
        if parse_derivative(form, lex).form != form:
            raise VekaError('non-reversible generated derivative')
    return {
        'canonical_entries': len(lex),
        'experimental_derivatives': len(new_forms),
        'derivational_collisions': len(new_forms.intersection(lex)),
        'distinct_derivational_operators': len(DERIVATIONS),
        'correlative_semantic_cells': len(CORRELATIVE_SERIES) * len(CORRELATIVE_DIMENSIONS),
        'correlative_cells_with_existing_surface': sum(
            correlative(s, d, lex)['surface'] is not None
            for s in CORRELATIVE_SERIES for d in CORRELATIVE_DIMENSIONS
        ),
        'human_validated': False, 'canonical_adopted': False,
        'warning': 'Structural checks only. Candidate markers and word meanings require human validation.'
    }
