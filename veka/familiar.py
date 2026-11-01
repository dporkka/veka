"""A versioned, reversible familiar-vocabulary pilot for the Core grammar.

Run ``python -m veka.familiar parse 'Mi sen mu-si-ka.'`` or ``convert``.
The mapping is an editorial hypothesis, not evidence of global recognition.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import replace

from .core import Lexicon, VekaError, parse, validate_word
from .profiles import load_profile

# Deliberately small: meanings and grammatical classes remain those of v0.4.
REPLACEMENTS = {
    'woi': 'mu-si-ka',  # music
    'vik': 'se-ko-la',  # school
    'sau': 'bu-ku',     # book
    'noi': 'os-pi-tal', # hospital
    'dik': 'ka-me-ra',  # camera
    'hek': 'dok-ta',     # doctor (sense requires review)
    'ru': 'me-tal',      # metal
}
TOKEN = re.compile(r"[^\s.,!?;:]+")


def familiar_lexicon() -> tuple[Lexicon, dict[str, str]]:
    """Build the profile and a complete map including compositional entries."""
    original = load_profile('tonal')
    mapping = {}
    for old, new in REPLACEMENTS.items():
        if old not in original or original[old].kind != 'root' or original[old].pos != 'noun':
            raise VekaError(f'invalid replacement root: {old}')
        if not validate_word(new) or new in original:
            raise VekaError(f'invalid or occupied replacement: {new}')
    result = Lexicon()
    for form, entry in original.items():
        if entry.kind == 'compound':
            head = REPLACEMENTS.get(entry.head, entry.head)
            modifier = REPLACEMENTS.get(entry.modifier, entry.modifier)
            new_form = head + '-' + modifier if (head, modifier) != (entry.head, entry.modifier) else form
        else:
            head, modifier = entry.head, entry.modifier
            new_form = REPLACEMENTS.get(form, form)
        if not validate_word(new_form) or new_form in result:
            raise VekaError(f'profile collision or illegal form: {new_form}')
        result[new_form] = replace(entry, form=new_form, head=head, modifier=modifier)
        if new_form != form:
            mapping[form] = new_form
    if set(mapping.values()) & (set(original) - set(mapping)):
        raise VekaError('replacement shadows unchanged word')
    surfaces = {}
    for form in result:
        surfaces.setdefault(form.replace('-', ''), []).append(form)
    for form in mapping.values():
        if len(surfaces[form.replace('-', '')]) != 1:
            raise VekaError(f'undelimited surface collision: {form}')
    return result, mapping


def convert(text: str, direction: str) -> str:
    """Convert complete known lexemes; unknown text and punctuation are untouched.

    Conversion is lexical, not translation. Proper names sharing a lexeme are
    ambiguous; do not apply it to text where such names must be preserved.
    """
    _, mapping = familiar_lexicon()
    if direction == 'to-core':
        mapping = {v: k for k, v in mapping.items()}
    elif direction != 'to-familiar':
        raise VekaError('direction must be to-core or to-familiar')
    def substitute(match):
        word = match.group()
        new = mapping.get(word.lower())
        if new is None:
            return word
        if word.isupper(): return new.upper()
        if word[0].isupper(): return new.capitalize()
        return new
    return TOKEN.sub(substitute, text)


def parse_familiar(sentence: str) -> dict:
    lex, mapping = familiar_lexicon()
    # Capitalized old forms otherwise pass as proper names in the Core parser.
    for match in TOKEN.finditer(sentence):
        if match.group().lower() in mapping:
            raise VekaError(f'old vocabulary requires conversion: {match.group()}')
    return parse(sentence, lex, strict=True)


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest='command', required=True)
    p = commands.add_parser('parse'); p.add_argument('sentence')
    c = commands.add_parser('convert'); c.add_argument('direction', choices=('to-core', 'to-familiar')); c.add_argument('text')
    args = cli.parse_args()
    try:
        result = parse_familiar(args.sentence) if args.command == 'parse' else convert(args.text, args.direction)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except VekaError as exc:
        cli.exit(2, f'error: {exc}\n')


if __name__ == '__main__':
    main()
