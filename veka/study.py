"""Reproducible counterbalanced listening-study assignment builder.

Outputs a recording/presentation MANIFEST, not synthetic speech and not participant data.
"""
from __future__ import annotations
import csv
import hashlib
import json
import random
from pathlib import Path
from .core import VekaError

REQUIRED = {'item_id', 'category', 'meaning', 'context', 'critical', 'explicit', 'compact'}
CONDITIONS = ('explicit', 'compact')


def validate_items(items: list[dict]):
    if not isinstance(items,list) or not items:
        raise VekaError('study requires nonempty item list')
    seen=set()
    for item in items:
        if not isinstance(item,dict) or not REQUIRED.issubset(item):
            raise VekaError('study item missing required fields')
        if item['item_id'] in seen or not item['item_id']:
            raise VekaError('duplicate or empty study item id')
        seen.add(item['item_id'])
        if not all(isinstance(item[k],str) and item[k].strip() for k in ('meaning','explicit','compact','category')):
            raise VekaError('empty study target')
        if not isinstance(item['context'],dict) or item['critical'] not in (0,1):
            raise VekaError('invalid study context or critical flag')


def generate_assignments(items: list[dict], participant_id: str, seed: int = 20261101) -> list[dict]:
    validate_items(items)
    if not isinstance(participant_id,str) or not participant_id.strip():
        raise VekaError('participant_id is required')
    # Participant assignment is deterministic. Adjacent participant IDs switch arm.
    # Balanced order, while shuffled positions prevent fixed-order practice effects.
    parity = (sum(participant_id.encode('utf-8')) + seed) % 2
    rows=[]
    for index,item in enumerate(items):
        condition=CONDITIONS[(index+parity)%2]
        rows.append({
            'participant_id':participant_id,
            'item_id':item['item_id'],
            'condition':condition,
            'category':item['category'],
            'meaning':item['meaning'],
            'utterance':item[condition],
            'context_json':json.dumps(item['context'],ensure_ascii=False,sort_keys=True),
            'critical':item['critical'],
            'recording_id':item['item_id']+'_'+condition+'.wav',
        })
    random.Random(f'{seed}:{participant_id}').shuffle(rows)
    validate_assignments(rows)
    return rows


def validate_assignments(rows: list[dict]):
    ids=[r['item_id'] for r in rows]
    if len(ids)!=len(set(ids)):
        raise VekaError('same reference meaning presented more than once per participant')
    arms=[r['condition'] for r in rows]
    if set(arms)-set(CONDITIONS):raise VekaError('unexpected condition name')
    if abs(arms.count('explicit')-arms.count('compact'))>1:
        raise VekaError('study conditions are not balanced')
    if len({r['participant_id'] for r in rows})!=1:
        raise VekaError('assignment mixed participant identifiers')
    return True


def write_manifest(items: list[dict], participant_id: str, output: str | Path, seed: int = 20261101):
    rows=generate_assignments(items,participant_id,seed)
    with open(output,'w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    return {'participant_id':participant_id,'trials':len(rows),
            'explicit':sum(r['condition']=='explicit' for r in rows),
            'compact':sum(r['condition']=='compact' for r in rows),
            'output':str(output),'audio_generated':False,'human_data_collected':False}


def generate_abx_assignments(pairs: list[dict], participant_id: str, seed: int = 20261101) -> list[dict]:
    """ABX sound-discrimination manifest, with both possible X targets balanced.

    Humans must record audio. Each pair has 4 trials, two with X=A and two X=B.
    The talker should record distinct natural productions, never duplicate the
    exact same waveform for A and X; otherwise it tests audio matching.
    """
    from .core import _syllable_info
    if not isinstance(participant_id,str) or not participant_id.strip():
        raise VekaError('participant ID required')
    if not pairs:raise VekaError('at least one ABX pair required')
    rows=[]
    for pair in pairs:
        a,b=pair['a'],pair['b']
        if a==b or not all(isinstance(q,str) for q in (a,b)):
            raise VekaError('ABX targets must be distinct words')
        for sound in (a,b):_syllable_info(sound)
        for repeat in range(4):
            target='A' if repeat%2==0 else 'B'
            rows.append({'participant_id':participant_id,
                         'trial_id':f"{pair['id']}-{repeat+1}",
                         'contrast':pair['contrast'],
                         'a':a,'b':b,
                         'x':a if target=='A' else b,
                         'correct_option':target,
                         'audio_recorded':False})
    random.Random(f'abx:{seed}:{participant_id}').shuffle(rows)
    return rows
