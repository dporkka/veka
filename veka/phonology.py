"""Static, hypothesis-generating confusion audit. Not acoustic evidence."""
from __future__ import annotations
from .numbers import DIGITS
from .core import Lexicon, _syllable_info

CRITICAL_OPERATORS=('zi','oi','fi','na','ve','yu','al','kis','sin','dis','su',
                    'ha','ke','lu','pa','fu','du','ne','to','en','de','es')


def edit_distance(a: str, b: str) -> int:
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        next_row=[i]
        for j,y in enumerate(b,1):
            next_row.append(min(next_row[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=next_row
    return previous[-1]


def evaluate_numeric_distances(lex: Lexicon) -> dict:
    operator_names = set(CRITICAL_OPERATORS)
    assert all(t in lex and lex[t].pos=='digit' for t in DIGITS)
    digits=[edit_distance(a,b) for i,a in enumerate(DIGITS) for b in DIGITS[i+1:]]
    operators=[edit_distance(a,b) for a in DIGITS for b in operator_names]
    return {'count':len(DIGITS), 'minimum_digit_distance':min(digits),
            'minimum_operator_distance':min(operators),
            'method':'orthographic Levenshtein distance; NOT psychoacoustic distance',
            'acoustically_validated':False}


def analyze_root_confusions(lex: Lexicon) -> dict:
    entries=[e for e in lex.values() if e.kind=='root' and e.pos not in ('digit','unit')]
    minimal_pairs=[]
    for i,a in enumerate(entries):
        for b in entries[i+1:]:
            try:
                oa,na,ca,ta=_syllable_info(a.form)
                ob,nb,cb,tb=_syllable_info(b.form)
            except ValueError:continue
            variants=sum(x!=y for x,y in zip((oa,na,ca,ta),(ob,nb,cb,tb)))
            if variants!=1:continue
            mode=('tone' if ta!=tb else 'coda' if ca!=cb
                  else 'vowel' if na!=nb else 'onset')
            minimal_pairs.append({'forms':sorted([a.form,b.form]),'contrast':mode})
    minimal_pairs.sort(key=lambda p: (p['contrast']!='tone',p['contrast']!='coda',p['forms']))
    return {'root_count':len(entries),'minimal_pair_count':len(minimal_pairs),
            'minimal_pairs':minimal_pairs, 'numeric':evaluate_numeric_distances(lex),
            'empirically_validated':False,
            'warning':'Surface contrast count only; does not predict speech error rates.'}
