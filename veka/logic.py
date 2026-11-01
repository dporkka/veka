"""Fully bracketed, compositional Veka 0.3 propositional logic.

zi A ve B yu = A AND B
 oi A ve B yu = A OR B (inclusive)
 fi A ve B yu = A -> B (material conditional)
 na A yu      = NOT A

Deliberate trade-off: no precedence shortcuts. Every scope is overt.
"""
from __future__ import annotations
from .core import VekaError, Discourse, Lexicon, _normalize_sentence, parse

OPERATORS={'zi':'and','oi':'or_inclusive','fi':'if','na':'not'}
BOUNDARIES={'ve','yu'}
MAX_DEPTH=16
MAX_TOKENS=256


def parse_logic(sentence: str, lex: Lexicon, context: Discourse|None=None, strict: bool=True) -> dict:
    words = [w.lower() if w.lower() in lex else w for w in _normalize_sentence(sentence)]
    if len(words)>MAX_TOKENS:raise VekaError('logic expression too long')

    def parse_expr(pos: int, depth: int) -> tuple[dict,int]:
        if depth>MAX_DEPTH:raise VekaError('logic nesting limit exceeded')
        if pos>=len(words):raise VekaError('expected logical expression')
        marker=words[pos]
        if marker in OPERATORS:
            op=OPERATORS[marker]
            left,pos=parse_expr(pos+1,depth+1)
            if op=='not':
                if pos>=len(words) or words[pos]!='yu':raise VekaError('NOT must close with yu')
                return {'op':'not','argument':left},pos+1
            if pos>=len(words) or words[pos]!='ve':raise VekaError('binary connective requires ve')
            right,pos=parse_expr(pos+1,depth+1)
            if pos>=len(words) or words[pos]!='yu':raise VekaError('binary connective must close with yu')
            return {'op':op,'left':left,'right':right},pos+1
        end=pos
        while end<len(words) and words[end] not in BOUNDARIES:
            if words[end] in OPERATORS:
                raise VekaError('logical operator requires expression boundary')
            end+=1
        if pos==end:raise VekaError('empty logical clause')
        clause=parse(' '.join(words[pos:end]),lex,context=context,strict=strict)
        if clause['mood'] != 'statement' or clause['question']:
            raise VekaError('truth-functional logic cannot operate on questions or commands')
        return {'op':'atom','source':' '.join(words[pos:end]),'clause':clause},end

    ast,end=parse_expr(0,0)
    if end!=len(words):raise VekaError('unexpected trailing expression tokens')
    return ast


def evaluate_logic(ast: dict, valuations: dict[str,bool]) -> bool:
    """Check propositional truth tables against externally supplied atom truth.

    This is NOT a model of noun quantifiers or real-world conditions.
    An IF expression is material implication, not a causal prediction.
    """
    op=ast.get('op')
    if op=='atom':
        key=ast['source']
        if key not in valuations or type(valuations[key]) is not bool:
            raise VekaError(f'missing Boolean truth assignment: {key}')
        return valuations[key]
    if op=='not':return not evaluate_logic(ast['argument'],valuations)
    if op not in ('and','or_inclusive','if'):raise VekaError('unknown logical expression')
    a=evaluate_logic(ast['left'],valuations)
    b=evaluate_logic(ast['right'],valuations)
    if op=='and':return a and b
    if op=='or_inclusive':return a or b
    return (not a) or b
