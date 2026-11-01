"""Isolated experimental lexical variants; NEVER silently change canonical Veka.

The tone-free candidate substitutes four root WORDS, not just strips acute marks.
This is a contrastive lexicon for testing, not evidence of acoustic superiority.
"""
from __future__ import annotations

import csv
import re
from dataclasses import replace
from pathlib import Path

from .core import Lexicon, VekaError, validate_word

DATA = Path(__file__).resolve().parents[1] / 'data'
TONAL_MARKS = 'áéíóú'
PROFILES = ('tonal', 'toneless')
WORD = re.compile(r'[A-Za-zÁÉÍÓÚáéíóú]+')


def _substitutions(lex: Lexicon, data_dir: Path) -> dict[str, str]:
    mapping = {}
    with (data_dir / 'tone_free_ablation.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            old = row['tonal_form']
            new = row['toneless_candidate']
            if old in mapping or old not in lex:
                raise VekaError(f'unknown or duplicate tonal root: {old}')
            if not any(c in old for c in TONAL_MARKS) or lex[old].kind != 'root':
                raise VekaError(f'only existing tonal roots may be replaced: {old}')
            if any(c in new for c in TONAL_MARKS) or not validate_word(new):
                raise VekaError(f'invalid toneless substitute: {new}')
            if row['gloss'] != lex[old].gloss:
                raise VekaError(f'mismatched gloss for: {old}')
            mapping[old] = new
    existing_tonal = {word for word in lex if any(c in word for c in TONAL_MARKS)}
    if set(mapping) != existing_tonal:
        raise VekaError('tone-free mapping must cover every tonal headword')
    if len(set(mapping.values())) != len(mapping):
        raise VekaError('duplicate toneless replacement')
    if set(mapping.values()).intersection(lex.keys()):
        raise VekaError('toneless substitution collides with existing headword')
    return mapping


def load_profile(profile: str = 'tonal', *, data_dir: Path | None = None) -> Lexicon:
    """Load canonical lexicon or a bijective, collision-checked alternate lexicon."""
    if profile not in PROFILES:
        raise VekaError(f'unsupported profile {profile!r}; choose from {PROFILES}')
    root = Path(data_dir) if data_dir is not None else DATA
    lex = Lexicon.from_csv(root / 'lexicon.csv')
    if profile == 'tonal':
        return lex
    mapping = _substitutions(lex, root)
    changed = Lexicon()
    for word, entry in lex.items():
        new_form = mapping.get(word, word)
        changed[new_form] = replace(entry, form=new_form)
    return changed


def profile_summary(profile: str, *, data_dir: Path | None = None) -> dict:
    root = Path(data_dir) if data_dir is not None else DATA
    lex = load_profile(profile, data_dir=root)
    from .phonology import analyze_root_confusions
    structural = analyze_root_confusions(lex)
    return {
        'profile': profile,
        'headwords': len(lex),
        'rising_headwords': sum(any(c in word for c in TONAL_MARKS) for word in lex),
        'substitutions': 0 if profile == 'tonal' else len(_substitutions(Lexicon.from_csv(root / 'lexicon.csv'), root)),
        'structural_minimal_pair_count': structural['minimal_pair_count'],
        'structural_count_is_acoustic_evidence': False,
        'acoustically_validated': False,
        'status': 'experimental hypothesis; no human listening evidence',
    }


def convert_utterance(text: str, target_profile: str, *, data_dir: Path | None = None) -> str:
    """Convert only complete root tokens; leave unknown/nonlexical text unchanged.

    Example: 'pái-pál' -> 'fok-lek', but 'páile' must not be changed.
    This tool does not parse or approve grammatical validity.
    """
    if not isinstance(text, str):
        raise VekaError('utterance must be text')
    if target_profile not in PROFILES:
        raise VekaError(f'unsupported profile: {target_profile}')
    root = Path(data_dir) if data_dir is not None else DATA
    tonal = Lexicon.from_csv(root / 'lexicon.csv')
    forward = _substitutions(tonal, root)
    mapping = forward if target_profile == 'toneless' else {v:k for k,v in forward.items()}
    def replace_word(match):
        word = match.group(0)
        replacement = mapping.get(word.lower())
        if replacement is None: return word
        if word.isupper():return replacement.upper()
        if word[0].isupper():return replacement.capitalize()
        return replacement
    return WORD.sub(replace_word, text)
