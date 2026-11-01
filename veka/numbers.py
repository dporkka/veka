"""Veka 0.3 canonical spoken decimal numerals (never floating point)."""
from __future__ import annotations
import re
from .core import VekaError

DIGITS = ('nul', 'ran', 'kuk', 'zun', 'sok', 'gel', 'tak', 'pil', 'bos', 'mus')
DIGIT_VALUES = {word:str(i) for i,word in enumerate(DIGITS)}
NUMBER_REGEX = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z', re.ASCII)
MAX_DIGITS = 64


def spell_number(value: str) -> str:
    """Spell an ASCII canonical base-10 numeral, preserving decimal precision.

    No separators, exponent syntax, -0 or redundant leading zeros.
    """
    if not isinstance(value,str) or not NUMBER_REGEX.fullmatch(value):
        raise VekaError('number must use canonical decimal notation')
    digits = [c for c in value if c.isdigit()]
    if len(digits) > MAX_DIGITS:
        raise VekaError('number exceeds safety length limit')
    if value.startswith('-') and all(d == '0' for d in digits):
        raise VekaError('negative zero is forbidden')
    spoken = ['wen']
    if value.startswith('-'): spoken.append('sin')
    for ch in value.lstrip('-'):
        spoken.append('dis' if ch=='.' else DIGITS[int(ch)])
    return ' '.join(spoken)


def read_number(spoken: str) -> str:
    if not isinstance(spoken,str) or not spoken:
        raise VekaError('empty number')
    tokens=spoken.split()
    if not tokens or tokens[0]!='wen': raise VekaError('number must begin with wen')
    value,ending = parse_number_tokens(tokens,0)
    if ending != len(tokens):raise VekaError('trailing tokens after number')
    return value


def parse_number_tokens(tokens: list[str], start: int) -> tuple[str,int]:
    """Read marker + digits until first nonnumeric token, returns (value, index)."""
    if start >= len(tokens) or tokens[start]!='wen':
        raise VekaError('number must begin with wen')
    pos=start+1; negative=False
    if pos<len(tokens) and tokens[pos]=='sin':
        negative=True;pos+=1
    integer=[]; fraction=[]; seen_dot=False
    while pos<len(tokens) and (tokens[pos] in DIGIT_VALUES or tokens[pos]=='dis'):
        t=tokens[pos];pos+=1
        if t=='dis':
            if seen_dot or not integer:raise VekaError('invalid decimal separator')
            seen_dot=True
        else:
            (fraction if seen_dot else integer).append(DIGIT_VALUES[t])
        if len(integer)+len(fraction)>MAX_DIGITS:raise VekaError('number exceeds safety length limit')
    if not integer or (seen_dot and not fraction):raise VekaError('incomplete numerical expression')
    if len(integer)>1 and integer[0]=='0':raise VekaError('leading zeros forbidden')
    if negative and not any(d!='0' for d in integer+fraction):
        raise VekaError('negative zero is forbidden')
    value=('-' if negative else '')+''.join(integer)
    if seen_dot:value+='.'+''.join(fraction)
    return value,pos
