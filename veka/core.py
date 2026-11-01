"""Conservative reference parser and script renderer for Veka 0.3.

No probabilistic reference resolution: reject missing/ambiguous mandatory roles.
Grammar covers a deliberately limited single-clause subset only.
"""
from __future__ import annotations

import csv
import html
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

CONSONANTS = 'pbtdkgmnfvszhlryw'
VOWELS = 'aeiou'
DIPHTHONGS = ('ai','au','oi')
CODAS = ('','n','l','s','k')
ACCENT = str.maketrans('áéíóú', 'aeiou')
SONORANT_CODAS = {'','n','l'}
RESERVED = {'ha','ke','lu','pa','fu','du','ne','to','en','de','es'}
TIME_WORDS = {'sun','nal'}
PATTERN = re.compile(r'^(?P<onset>[pbtdkgmnfvszhlryw]?)(?P<nucleus>ai|au|oi|[aeiou])(?P<coda>[nlsk]?)$')


class VekaError(ValueError):
    pass


def _syllable_info(text: str):
    form = unicodedata.normalize('NFC', text)
    rise = [ch for ch in form if ch in 'áéíóú']
    if len(rise) > 1: raise VekaError('a syllable may have only one tone accent')
    plain = form.translate(ACCENT)
    match = PATTERN.fullmatch(plain)
    if not match: raise VekaError(f'illegal syllable: {text}')
    o, n, c = match.group('onset','nucleus','coda')
    if plain in ('yi','wu'): raise VekaError('phonologically restricted collision-prone syllable')
    if n in DIPHTHONGS and c not in ('','n'): raise VekaError('diphthong forbids this coda')
    if rise:
        if c not in SONORANT_CODAS: raise VekaError('rising tone forbidden on obstruent coda')
        # Roman accent must occur on the FIRST vowel of a diphthong.
        vowel_start = len(o)
        if form[vowel_start] not in 'áéíóú': raise VekaError('accent must mark nucleus first vowel')
    return o,n,c,bool(rise)


def syllabify(form: str) -> list[str]:
    if not form or form != form.strip() or '--' in form:
        raise VekaError('invalid empty form or compound delimiter')
    parts = form.split('-')
    for p in parts: _syllable_info(p)
    return parts


def validate_word(form: str) -> bool:
    try:
        syllabify(form)
        return True
    except (ValueError,TypeError):
        return False


@dataclass(frozen=True)
class Entry:
    form: str
    gloss: str
    pos: str
    kind: str
    domain: str
    head: str
    modifier: str
    valency: str


class Lexicon(dict[str, Entry]):
    @classmethod
    def from_csv(cls, filename: str | Path) -> 'Lexicon':
        result = cls()
        with open(filename, encoding='utf-8', newline='') as f:
            for row in csv.DictReader(f):
                e = Entry(**row)
                if e.form in result or not validate_word(e.form):
                    raise VekaError(f'duplicate or invalid word {e.form}')
                result[e.form] = e
        return result


@dataclass(frozen=True)
class Discourse:
    """Speaker-supplied candidate referents; no inferred conversational state.

    Every omitted mandatory role requires exactly one candidate. The lists
    describe candidates mutually established in the preceding discourse, NOT
    confidence scores assigned by a model.
    """
    subjects: tuple[str,...] = ()
    objects: tuple[str,...] = ()
    recipients: tuple[str,...] = ()
    locations: tuple[str,...] = ()
    referents: tuple[str,...] = ()


def _unique(items: tuple[str,...], role: str) -> str:
    if len(set(items)) != 1 or not items:
        raise VekaError(f'{role} is not uniquely recoverable from shared context')
    return items[0]


def _normalize_sentence(text: str) -> list[str]:
    if not text or not isinstance(text,str): raise VekaError('empty sentence')
    text = unicodedata.normalize('NFC',text.strip())
    # Exactly zero or one terminating punctuation mark; never silently discard
    # punctuation sequences that could hide a multi-utterance input.
    if text and text[-1] in '.?!': text = text[:-1]
    if not text or re.search(r'[.!?]',text): raise VekaError('only single clauses supported')
    tokens = text.split()
    if not tokens: raise VekaError('empty sentence')
    return tokens


def _is_proper_name(token: str) -> bool:
    """Recognize capitalized, single-token Unicode names without guessing words.

    Unlike Veka syllables, foreign names retain their original spelling. A
    name must begin with an uppercase/titlecase letter; optional internal
    apostrophes and hyphens separate nonempty letter sequences. No digits,
    whitespace, controls, format characters, or arbitrary punctuation.
    """
    if not token or len(token) > 128 or unicodedata.category(token[0]) not in ('Lu', 'Lt'):
        return False
    parts = re.split(r"[-'’]", token)
    return all(
        part and unicodedata.category(part[0]).startswith('L')
        and all(unicodedata.category(ch)[0] in ('L', 'M') for ch in part)
        for part in parts
    )


def _token_info(token: str, lex: Lexicon) -> tuple[str,str]:
    form = token.lower()
    if form in lex: return form, lex[form].pos
    if _is_proper_name(token):
        # At sentence start, capitalized research morphology otherwise looks
        # like a foreign proper name. Reserve only *complete*, valid extension
        # forms so Core cannot silently reinterpret content questions as names.
        if form.count('-') == 1:
            from .extended import DERIVATIONS, DOMAINS, SERIES
            left, right = form.split('-')
            if ((left in SERIES and right in DOMAINS)
                    or (left in lex and lex[left].pos == 'verb'
                        and lex[left].kind == 'root' and right in DERIVATIONS)):
                raise VekaError(f'experimental form requires research grammar: {token}')
        return token,'proper'
    raise VekaError(f'unknown Veka word: {token}')


def _np(tokens: list[str], pos: int, lex: Lexicon, context: Discourse, strict: bool, depth: int = 0) -> tuple[str,int]:
    """Noun phrase with one optional quantifier OR exact decimal quantity.

    Grammar: [quantifier] noun [plural] {adjective} [count [unit]] [possession].
    A quantifier and exact quantity cannot coexist in v0.3.
    """
    if depth > 16: raise VekaError('noun phrase possession nesting exceeds 16 levels')
    if pos >= len(tokens): raise VekaError('expected noun phrase')
    items = []
    quantified = False
    if tokens[pos] in ('al','kis'):
        items.append(tokens[pos]); pos += 1; quantified = True
        if pos>=len(tokens):raise VekaError('quantifier without noun')
    word, p = _token_info(tokens[pos],lex)
    if p not in ('noun','pronoun','proper'): raise VekaError(f'expected noun phrase, got {tokens[pos]}')
    if word == 'sa':
        if strict: raise VekaError('sa forbidden in critical mode; name entity')
        possible = context.referents or (context.subjects + context.objects + context.recipients + context.locations)
        word = _unique(possible,'sa antecedent')
    items.append(word); pos += 1
    plural = False
    if pos < len(tokens) and tokens[pos] == 'lu':
        items.append('lu'); pos += 1; plural = True
    while pos < len(tokens) and _token_info(tokens[pos],lex)[1] == 'adjective':
        items.append(_token_info(tokens[pos],lex)[0]); pos += 1
    if pos<len(tokens) and tokens[pos]=='wen':
        if quantified or plural:raise VekaError('exact quantity cannot combine with plural or quantifier')
        from .numbers import parse_number_tokens
        _,next_pos=parse_number_tokens(tokens,pos)
        items.extend(tokens[pos:next_pos]);pos=next_pos
        if pos<len(tokens) and tokens[pos]=='su':
            pos+=1
            if pos>=len(tokens) or _token_info(tokens[pos],lex)[1]!='unit':
                raise VekaError('su requires a standardized unit')
            items.extend(['su',tokens[pos]]);pos+=1
    if pos < len(tokens) and tokens[pos]=='de':
        items.append('de'); pos += 1
        possessor,pos = _np(tokens,pos,lex,context,strict,depth + 1)
        items.append(possessor)
    return ' '.join(items),pos


def _np_semantics(phrase: str | None) -> tuple[str|None,str|None,str|None]:
    """Return (quantifier, exact quantity, unit); data is already grammar-checked."""
    if phrase is None: return None,None,None
    tokens=phrase.split()
    # Possessor can have its own numeral; never attribute it to the head.
    tokens = tokens[:tokens.index('de')] if 'de' in tokens else tokens
    quantifier = {'al':'every','kis':'some'}.get(tokens[0])
    quantity=unit=None
    # 'wen' also exists as a NOUN. The numeric marker is only legal after
    # the head and its modifiers, never in the head's position.
    head_index = 1 if quantifier is not None else 0
    numeral_index = next((i for i in range(head_index + 1, len(tokens))
                          if tokens[i] == 'wen'), None)
    if numeral_index is not None:
        from .numbers import parse_number_tokens
        quantity,pos=parse_number_tokens(tokens,numeral_index)
        if pos<len(tokens) and tokens[pos]=='su': unit=tokens[pos+1]
    return quantifier,quantity,unit


def parse(sentence: str, lex: Lexicon, context: Discourse | None = None, strict: bool = False) -> dict:
    """Parse a simple single clause. Rejects structurally unsafe omissions.

    This is a syntactic parser, NOT full translation or a proof that any
    actual listener will recover a referent.
    """
    ctx = context or Discourse()
    tokens = _normalize_sentence(sentence)
    # Reject unsupported punctuation, token placement and unknown words.
    tokens = [_token_info(t,lex)[0] for t in tokens]
    pos=0; mood='statement'; compressed=False
    if tokens[pos]=='ha':
        mood='imperative'; subject='ti'; pos+=1
    elif tokens[pos] in ('pa','fu','du','ne') or (tokens[pos] in lex and lex[tokens[pos]].pos == 'verb'):
        if strict: raise VekaError('omitted subject forbidden in critical mode')
        subject = _unique(ctx.subjects, 'subject'); compressed=True
    else:
        subject,pos = _np(tokens,pos,lex,ctx,strict)
    tense='unspecified'; progressive=False; negative=False
    if pos < len(tokens) and tokens[pos] in ('pa','fu'):
        tense={'pa':'past','fu':'future'}[tokens[pos]]; pos+=1
    if pos < len(tokens) and tokens[pos]=='du': progressive=True; pos+=1
    if pos < len(tokens) and tokens[pos]=='ne': negative=True; pos+=1
    if pos>=len(tokens): raise VekaError('missing predicate')
    copula = tokens[pos]=='es'
    if copula:
        pos+=1
        if pos>=len(tokens):raise VekaError('copula missing adjective')
        pred=tokens[pos]; pos+=1
        if lex[pred].pos != 'adjective': raise VekaError('copula requires an adjective')
        valency='intransitive'
    else:
        pred=tokens[pos]; pos+=1
        if lex[pred].pos != 'verb': raise VekaError('predicate must be a verb')
        valency=lex[pred].valency
        if valency not in ('transitive','intransitive'):
            raise VekaError(f'unknown verb valency: {pred}')
    obj=None; recipient=None; location=None; time=None
    # Lexical NP cannot begin with a grammatical marker or time adverb.
    if pos < len(tokens) and (tokens[pos] in ('al','kis') or tokens[pos] not in lex or lex[tokens[pos]].pos in ('noun','pronoun')):
        if valency=='intransitive':raise VekaError('this predicate does not accept a direct object')
        obj,pos=_np(tokens,pos,lex,ctx,strict)
    if pos<len(tokens) and tokens[pos]=='to':
        pos+=1;recipient,pos=_np(tokens,pos,lex,ctx,strict)
    if pos<len(tokens) and tokens[pos]=='en':
        pos+=1;location,pos=_np(tokens,pos,lex,ctx,strict)
    if pos<len(tokens) and tokens[pos] in lex and lex[tokens[pos]].pos=='time':
        time=tokens[pos]; pos+=1
    question=False
    if pos < len(tokens) and tokens[pos]=='ke':
        question=True;pos+=1
    if pos != len(tokens):raise VekaError('unrecognized word order or duplicate role marker: '+' '.join(tokens[pos:]))
    if mood == 'imperative' and (tense == 'past' or question):
        raise VekaError('imperative cannot have past tense or polar-question marking')
    if obj is None and valency=='transitive':
        if strict: raise VekaError('omitted direct object forbidden in critical mode')
        obj=_unique(ctx.objects,'direct object');compressed=True
    if compressed and recipient is None and len(set(ctx.recipients))==1 and ctx.recipients:
        recipient=ctx.recipients[0]
    sq,sn,su = _np_semantics(subject)
    oq,on,ou = _np_semantics(obj)
    rq,rn,ru = _np_semantics(recipient)
    lq,ln,lu = _np_semantics(location)
    # Generalized quantifier scope across two noun phrases has not yet been
    # defined. Reject rather than guessing a reading (every > some, etc.).
    if sum(q is not None for q in (sq,oq,rq,lq))>1:
        raise VekaError('multiple quantifiers in a clause require explicit scope grammar')
    return dict(mood=mood,subject=subject,tense=tense,progressive=progressive,
                negative=negative,copula=copula,predicate=pred,object=obj,
                recipient=recipient,location=location,time=time,question=question,
                compressed=compressed,
                subject_quantifier=sq, subject_quantity=sn, subject_unit=su,
                object_quantifier=oq, object_quantity=on, object_unit=ou,
                recipient_quantifier=rq, recipient_quantity=rn, recipient_unit=ru,
                location_quantifier=lq, location_quantity=ln, location_unit=lu)


def _strokes(letter: str, x: float, y:float, size: float, color: str):
    """Featural shapes, based on v0.1 specimen. Returned SVG fragments."""
    dbase = {
        'lip': 'M7 25 V6 H25 V25', 'cor':'M8 6 V25 H26',
        'vel':'M5 25 L16 6 L27 25','glo':'M16 6 V25',
        'gli':'M4 16 Q10 7 16 16 Q22 25 28 16',
    }
    category = ('lip' if letter in 'pbmfv' else 'cor' if letter in 'tdnslrz'
                else 'vel' if letter in 'kg' else 'glo' if letter=='h' else 'gli')
    paths=[dbase[category]]
    if letter in ('m','n'):paths.append('M11 16 H23')
    if letter in ('f','v','s','z'):paths.append('M12 23 L23 9')
    if letter=='l':paths.append('M17 7 H27')
    if letter=='r':paths.extend(('M17 7 H27','M17 13 H27'))
    if letter=='w':paths.append('M4 24 Q10 15 16 24 Q22 33 28 24')
    contents=''.join(f'<path d="{d}"/>' for d in paths)
    if letter in 'bdgvz':contents+='<circle cx="29.5" cy="3.5" r="2.8" fill="currentColor" stroke="none"/>'
    return f'<g transform="translate({x} {y}) scale({size})" color="{color}">{contents}</g>'


def _vowel(v: str, x:float,y:float,scale:float):
    pattern={'a':'M17 5 V27 M17 15 H29','e':'M17 5 V27 M5 15 H17','i':'M17 5 V27',
             'o':'M5 17 H29 M17 5 V17','u':'M5 12 H29 M17 12 V27'}
    return f'<g transform="translate({x} {y}) scale({scale})"><path d="{pattern[v]}"/></g>'


def render_svg(sentence: str) -> str:
    """Render a line of canonical romanized Veka words as featural SVG blocks.

    Native Veka glyphs currently lack Unicode assignments. This SVG is a
    graphic representation, not reversible font text or TTS. No external assets.
    """
    words = _normalize_sentence(sentence)
    for word in words: syllabify(word.lower())
    blocks=[]; x=10
    for word_index, word in enumerate(words):
        for syllable_index, syll in enumerate(syllabify(word.lower())):
            onset,nucleus,coda,rising=_syllable_info(syll)
            contents=['<rect x="0" y="0" width="88" height="92" rx="9" fill="#fafcff" stroke="#c4ced8" stroke-width="1.5"/>']
            if onset:contents.append(_strokes(onset,7,10,.9,'#18324e'))
            if len(nucleus)==1:
                contents.append(_vowel(nucleus,45,9,.85))
            else:
                contents.extend([_vowel(nucleus[0],43,6,.6), _vowel(nucleus[1],60,16,.54)])
            if coda: contents.append(_strokes(coda,32,53,.62,'#18324e'))
            if rising:contents.append('<path d="M69 11 L79 3" stroke="#a54136" stroke-width="3.7"/>')
            tone = 'rising' if rising else 'level'
            blocks.append(f'<g transform="translate({x} 6)" data-veka="{html.escape(syll,quote=True)}" data-tone="{tone}" data-word-index="{word_index}" data-syllable-index="{syllable_index}">'+''.join(contents)+'</g>')
            x+=92
        x+=14
    width=max(125,x+10)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="118" viewBox="0 0 {width} 118" role="img" aria-label="Veka block script for {html.escape(sentence,quote=True)}">'
            '<rect width="100%" height="100%" fill="#f4f8fc"/>'
            '<g fill="none" stroke="#18324e" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">'+''.join(blocks)+'</g></svg>')


def read_svg(svg_text: str) -> str:
    """Recover normalized romanization from Veka SVG *metadata*, not glyphs.

    This is a reversible export format, NOT OCR or verification that the drawn
    strokes match their labels. Only render_svg's word/segment index format is
    accepted, so dropped or reordered blocks cannot be silently repaired.
    """
    from xml.etree import ElementTree as ET

    if (not isinstance(svg_text, str) or not svg_text or len(svg_text) > 2_000_000
            or "<!DOCTYPE" in svg_text.upper() or "<!ENTITY" in svg_text.upper()):
        raise VekaError("invalid Veka SVG metadata input")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise VekaError("malformed Veka SVG") from exc
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise VekaError("expected an SVG document")
    words: list[list[str]] = []
    block_count = 0
    for element in root.iter():
        syll = element.get("data-veka")
        if syll is None:
            continue
        block_count += 1
        if block_count > 4096:
            raise VekaError("Veka script exceeds block limit")
        raw_word = element.get("data-word-index")
        raw_syllable = element.get("data-syllable-index")
        if (raw_word is None or raw_syllable is None or not raw_word.isascii()
                or not raw_word.isdecimal() or not raw_syllable.isascii()
                or not raw_syllable.isdecimal()):
            raise VekaError("missing or invalid Veka script position")
        word_index, syll_index = int(raw_word), int(raw_syllable)
        if (str(word_index) != raw_word or str(syll_index) != raw_syllable
                or word_index > len(words) or word_index < len(words) - 1):
            raise VekaError("nonconsecutive Veka word indexes")
        if not validate_word(syll) or "-" in syll or syll != syll.lower():
            raise VekaError("invalid Veka script syllable")
        expected_tone = "rising" if any(c in syll for c in "áéíóú") else "level"
        if element.get("data-tone") != expected_tone:
            raise VekaError("Veka script tone metadata mismatch")
        if word_index == len(words):
            if syll_index != 0:
                raise VekaError("word must start with syllable zero")
            words.append([])
        if syll_index != len(words[word_index]):
            raise VekaError("missing or reordered Veka syllable")
        words[word_index].append(syll)
    if not words:
        raise VekaError("SVG has no Veka script blocks")
    return " ".join("-".join(parts) for parts in words)


def count_syllables(sentence: str) -> int:
    return sum(len(syllabify(word.lower())) for word in _normalize_sentence(sentence))


def evaluate_stimuli(stimuli: list[dict], lex: Lexicon) -> dict:
    if not isinstance(stimuli,list):raise VekaError('stimuli must be a list')
    passes=0; explicit=0; compact=0; failures=[]
    for i,item in enumerate(stimuli):
        ctx=Discourse(**{k:tuple(v) for k,v in item['context'].items()})
        try:
            full=parse(item['explicit'],lex,context=ctx)
            short=parse(item['compact'],lex,context=ctx)
            if full != dict(short,compressed=False):
                raise VekaError('full and compact forms yield different semantics')
            if not short['compressed']:
                raise VekaError('compact version did not actually omit a role')
            if not count_syllables(item['compact']) < count_syllables(item['explicit']):
                raise VekaError('compact version does not shorten utterance')
            passes+=1
            explicit+=count_syllables(item['explicit'])
            compact+=count_syllables(item['compact'])
        except (ValueError,KeyError,TypeError) as exc:
            failures.append({'case':i+1,'error':str(exc)})
    return {'n_cases':len(stimuli),'parse_passes':passes,'failures':failures,
            'explicit_syllables':explicit,'compact_syllables':compact,
            'syllable_reduction_fraction':round(1-compact/explicit,4) if explicit else 0,
            'measures_spoken_throughput':False,'measures_comprehension':False}


def score_human_trials(rows: list[dict]) -> dict:
    """Summarize actual listener observations; never invent performance data.

    Correct/minute counts successful messages over ALL elapsed time, including
    unsuccessful attempts and any repairs already included in elapsed_ms.
    """
    from collections import defaultdict
    import math
    import statistics
    groups = defaultdict(list)
    seen = set()
    required={'participant_id','trial_id','condition','elapsed_ms','repairs','correct','confidence','critical'}
    for row in rows:
        if not required.issubset(row):
            raise VekaError(f'missing fields: {sorted(required - row.keys())}')
        pid,tid,condition=(str(row[k]).strip() for k in ('participant_id','trial_id','condition'))
        if not (pid and tid and condition):raise VekaError('participant, trial and condition required')
        if condition not in ('explicit', 'compact'):
            raise VekaError('unsupported trial condition; expected explicit or compact')
        # Each participant receives exactly one rendition of a given meaning.
        key=(pid,tid)
        if key in seen:raise VekaError('duplicate participant/trial observation across conditions')
        seen.add(key)
        try:
            elapsed=float(row['elapsed_ms']);repairs=int(row['repairs'])
            correct=int(row['correct']);confidence=float(row['confidence']);critical=int(row['critical'])
        except (ValueError,TypeError) as e:
            raise VekaError('invalid numeric trial value') from e
        if (not math.isfinite(elapsed) or elapsed<=0 or repairs<0 or correct not in (0,1)
                or not math.isfinite(confidence) or not 0<=confidence<=1 or critical not in (0,1)):
            raise VekaError('trial out of range')
        groups[condition].append((elapsed,repairs,correct,confidence,critical))
    report={}
    for cond, trials in sorted(groups.items()):
        n=len(trials);good=sum(x[2] for x in trials)
        total_ms=sum(x[0] for x in trials)
        report[cond]={
          'n_trials':n,
          'success_rate':round(good/n,4),
          'correct_per_minute':round(good*60000/total_ms,3),
          'median_attempt_ms':round(statistics.median(x[0] for x in trials),2),
          'mean_repairs':round(sum(x[1] for x in trials)/n,3),
          'critical_errors':sum(x[4] and not x[2] for x in trials),
          'mean_confidence':round(sum(x[3] for x in trials)/n,3),
          'brier_score':round(sum((x[3]-x[2])**2 for x in trials)/n,4),
        }
    return report
