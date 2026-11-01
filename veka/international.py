"""Veka 0.4 INTERNATIONAL-LEXICON EXPERIMENT (never canonical by default).

Provides structural audits, transparent *existing* compound-family checks, and
blind randomized pilot manifests. No cross-linguistic or human-study result is
estimated or invented. This module never mutates the Veka lexicon or parser.
"""
from __future__ import annotations

import csv
import hashlib
import random
from collections import Counter, defaultdict
from pathlib import Path

from .core import Lexicon, VekaError, syllabify, validate_word
from .phonology import CRITICAL_OPERATORS

COLUMNS = ('concept_id','gloss','pos','core_form','domain', 'candidate_form',
           'reference_spelling','status','evidence_note')
CANONICAL_POS = {'noun','verb','adjective'}
FORBIDDEN_SEGMENTS = set(CRITICAL_OPERATORS) | {'mi','ti','ni','sa','ya','no'}


def read_candidates(path: str | Path) -> list[dict]:
    with open(path,encoding='utf-8',newline='') as file:
        reader=csv.DictReader(file)
        if not reader.fieldnames or tuple(reader.fieldnames)!=COLUMNS:
            raise VekaError('experimental candidate CSV has incorrect headers')
        return list(reader)


EVIDENCE_COLUMNS=('concept_id','language','language_family','attested_form',
                  'citation','reviewer','verified')


def read_evidence(path:str | Path) -> list[dict]:
    with open(path,encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ())!=EVIDENCE_COLUMNS:
            raise VekaError('invalid multilingual evidence CSV headers')
        return list(reader)


def audit_evidence(records:list[dict],candidates:list[dict])->dict:
    """Count independently sourced FAMILY coverage; never infer recognition.

    A citation is required even for unverified evidence. Family tags are
    analyst-supplied and require external review; they are not universal
    orthography or inherent comprehension estimates.
    """
    concepts={r['concept_id'] for r in candidates}
    seen=set();by_concept=defaultdict(list)
    for r in records:
        if not set(EVIDENCE_COLUMNS).issubset(r):raise VekaError('missing multilingual evidence field')
        if (any(not isinstance(r.get(k),str) for k in EVIDENCE_COLUMNS)
            or r['concept_id'] not in concepts or any(not r[k].strip() for k in
            ('concept_id','language','language_family','attested_form','citation','reviewer'))
            or r['verified'] not in ('yes','no')):
            raise VekaError('evidence record missing provenance or unknown concept')
        identifier=(r['concept_id'],r['language'].casefold())
        if identifier in seen:raise VekaError('duplicate concept-language evidence')
        seen.add(identifier)
        if r['verified']=='yes':by_concept[r['concept_id']].append(r)
    out={}
    for cid,entries in sorted(by_concept.items()):
        out[cid]={'attested_languages':len(entries),
                  'independent_families':len({x['language_family'].casefold() for x in entries}),
                  'family_labels':sorted({x['language_family'] for x in entries}),
                  'recognition_rate':None}
    return {'evidence_records':len(records),'verified_records':sum(len(v) for v in by_concept.values()),
            'by_concept':out,'recognition_measured':False,
            'warning':'Verification flags and family assignments are human supplied; attestation does not measure recognition.'}


def audit_candidates(rows: list[dict], lex: Lexicon, evidence: list[dict] | None = None) -> dict:
    """Mechanical audit, not a word recognition model or an adoption process.

    Fail closed on corrupt concept mapping and duplicate proposed lexemes.
    Individual phonetically invalid draft proposals get marked rejected so
    that analysts can repair them without losing the whole 100-concept queue.
    """
    if not rows:raise VekaError('candidate queue is empty')
    seen_concepts=set(); seen_forms=set(); results=[]
    for row in rows:
        if not set(COLUMNS).issubset(row):
            raise VekaError('missing candidate CSV field')
        concept=row['concept_id']
        if not concept or concept in seen_concepts:
            raise VekaError('duplicate or empty concept id')
        seen_concepts.add(concept)
        core=row['core_form']
        if core not in lex or lex[core].kind!='root' or lex[core].pos not in CANONICAL_POS:
            raise VekaError(f'noncanonical concept mapping: {concept}')
        e=lex[core]
        if (e.gloss,e.pos)!=(row['gloss'],row['pos']):
            raise VekaError(f'canonical mapping changed: {concept}')
        if any(not isinstance(row.get(k),str) for k in COLUMNS):
            raise VekaError(f'incomplete candidate CSV row: {concept}')
        proposed=row['candidate_form'].strip()
        if not proposed:
            if row['status']!='not_proposed':
                raise VekaError(f'empty candidate must be not_proposed: {concept}')
            continue
        if proposed in seen_forms:
            raise VekaError(f'duplicate international candidate form: {proposed}')
        seen_forms.add(proposed)
        if row['status']!='unverified_draft':
            raise VekaError(f'unrecognized experimental status: {concept}')
        problems=[]
        if not validate_word(proposed):
            problems.append('invalid Veka phonotactics')
            parts=[]
        else:
            parts=syllabify(proposed)
            if len(parts)<2:problems.append('single syllable would consume a core root slot')
            if len(parts)>8:problems.append('too many syllables for pilot word')
            if any(any(ch in 'áéíóú' for ch in part) for part in parts):
                problems.append('pilot loans must be toneless')
            if any(part in FORBIDDEN_SEGMENTS for part in parts):
                problems.append('contains grammatical/pronoun syllable')
        if proposed in lex:problems.append('collides with canonical dictionary form')
        results.append({'concept_id':concept,'gloss':e.gloss,'core_form':core,
                        'candidate_form':proposed,'syllable_count':len(parts),'added_syllables_vs_core':len(parts)-1,
                        'status':'rejected' if problems else 'structurally_testable',
                        'reasons':problems,
                        'recognition_measured':False,
                        'meaning_validated':False})
    vetted=audit_evidence(evidence or [],rows)
    return {'concept_count':len(rows),'experimental_forms':len(results),
            'rejected_forms':sum(x['status']=='rejected' for x in results),
            'structurally_testable':sum(x['status']=='structurally_testable' for x in results),
            'attested_forms':len(vetted['by_concept']),'evidence':vetted,
            'adopted_forms':0,'human_participants':0,
            'recognition_measured':False,'candidates':results,
            'warning':'No multilingual donor evidence or human recognition data supplied; structural suitability is not empirical acceptance.'}


def derive_noun_modifier(noun: str, adjective: str, lex: Lexicon) -> dict:
    """Express the existing noun–adjective template, no new suffix/semantics."""
    if noun not in lex or lex[noun].pos!='noun' or lex[noun].kind!='root':
        raise VekaError('head must be a canonical noun root')
    if adjective not in lex or lex[adjective].pos!='adjective' or lex[adjective].kind!='root':
        raise VekaError('modifier must be a canonical adjective root')
    form=f'{noun}-{adjective}'
    matching=lex.get(form)
    canonical=bool(matching and matching.pos=='noun' and matching.kind=='compound'
                   and matching.head==noun and matching.modifier==adjective)
    return {'form':form,'gloss':f'{lex[adjective].gloss} {lex[noun].gloss}',
            'canonical':canonical,
            'status':'existing_dictionary_compound' if canonical else 'hypothetical_unregistered_expression',
            'new_entries':0}


def compound_family_report(lex: Lexicon) -> dict:
    families=defaultdict(list);bad=[]
    for e in lex.values():
        if e.kind!='compound':continue
        if not (e.head in lex and e.modifier in lex and
                lex[e.head].kind=='root' and lex[e.head].pos=='noun' and
                lex[e.modifier].kind=='root' and lex[e.modifier].pos=='adjective' and
                e.form==f'{e.head}-{e.modifier}' and e.pos=='noun'):
            bad.append(e.form)
        else: families[e.head].append(e.form)
    return {'existing_compounds':sum(e.kind=='compound' for e in lex.values()),
            'valid_compounds':sum(map(len,families.values())),
            'invalid_compounds':len(bad),'invalid_forms':bad,
            'noun_root_families':len(families),
            'largest_families':[{ 'head':k,'count':len(v), 'examples':v[:3]} for k,v in
                                  sorted(families.items(),key=lambda kv:(-len(kv[1]),kv[0]))[:10]],
            'new_entries':0,'invented_agent_or_tool_suffixes':False}


def generate_recognition_manifest(rows:list[dict],lex:Lexicon,participant_id:str,seed:int=20261101):
    """Produce participant-blind stimuli and a separate researcher answer key.

    One version of each meaning per participant. Complementary participant
    identifiers with opposite parity permit cross-person condition assignment.
    Comparison requires randomized enrollment and controlling prior exposure.
    """
    if not isinstance(participant_id,str) or not participant_id.strip():
        raise VekaError('participant_id required')
    audit=audit_candidates(rows,lex)
    if audit['rejected_forms']:
        raise VekaError('candidate list includes structurally rejected forms')
    proposals=[r for r in audit['candidates'] if r['status']=='structurally_testable']
    if len(proposals)<2 or len(proposals)%2:
        raise VekaError('pilot requires an even number of at least two valid candidate forms')
    # Deterministic cohort alternation; allocate participant pseudonyms randomly
    # to avoid demographic/learning biases from participant name assignment.
    arm=(sum(participant_id.encode('utf-8'))+seed)%2
    index_order=list(range(len(proposals)))
    random.Random(f'concepts:{seed}').shuffle(index_order)
    assigned={idx:('core' if (slot+arm)%2==0 else 'international')
              for slot,idx in enumerate(index_order)}
    key=[];visible=[]
    for idx,proposal in enumerate(proposals):
        condition=assigned[idx]
        token=(proposal['core_form'] if condition=='core' else proposal['candidate_form'])
        opaque_id=hashlib.sha256(f'{seed}:{participant_id}:{proposal["concept_id"]}'.encode()).hexdigest()[:12]
        trial_id=f'V04-{opaque_id}'
        visible.append({'participant_id':participant_id,'trial_id':trial_id,
                        'presented_form':token,'response_gloss':'',
                        'response_ms':'','prior_exposure':'',
                        'presentation_modality':'written'})
        key.append({'participant_id':participant_id,'trial_id':trial_id,
                    'concept_id':proposal['concept_id'],'target_gloss':proposal['gloss'],
                    'condition':condition,'presented_form':token,
                    'status':'unverified_draft','judge_correct':'',
                    'repair_count':''})
    order=list(range(len(visible)))
    random.Random(f'order:{seed}:{participant_id}').shuffle(order)
    return [visible[i] for i in order],[key[i] for i in order]


def summarize_recognition_scores(key:list[dict],scored:list[dict]):
    """Aggregate *manually judged* correctness, never NLP string guesses.

    Scored rows must be complete; latency is optional only if genuinely absent,
    not silently represented as zero. A paired causal effect is not established.
    """
    if not key or not scored: raise VekaError('actual annotated trials required')
    k={r['trial_id']:r for r in key}
    if len(k)!=len(key):raise VekaError('duplicate answer-key trial')
    s={r['trial_id']:r for r in scored}
    if len(s)!=len(scored) or set(s)!=set(k):raise VekaError('duplicate or incomplete trial outcomes')
    groups=defaultdict(list)
    for tid, row in s.items():
        if row.get('correct') not in ('0','1'):
            raise VekaError(f'correct must be a manually annotated 0 or 1: {tid}')
        if row.get('repair_count','')=='':
            raise VekaError(f'repair count must be annotated (zero is 0): {tid}')
        try:
            duration=float(row['response_ms']) if row.get('response_ms') else None
            repairs=int(row['repair_count'])
        except (ValueError,TypeError):raise VekaError(f'invalid timing or repairs: {tid}')
        if (duration is not None and (duration<=0 or duration==float('inf') or duration!=duration)) or repairs<0:
            raise VekaError(f'invalid timing or repairs: {tid}')
        groups[k[tid]['condition']].append((int(row['correct']),duration,repairs))
    stats={}
    for condition,items in sorted(groups.items()):
        times=[x[1] for x in items if x[1] is not None]
        stats[condition]={'n':len(items),'correct':sum(x[0] for x in items),
                          'accuracy':sum(x[0] for x in items)/len(items),
                          'mean_response_ms':sum(times)/len(times) if times else None,
                          'timed_trials':len(times),'total_repairs':sum(x[2] for x in items)}
    return {'trials':len(scored),'conditions':stats,'human_data_required':True,
            'causal_effect_established':False,
            'warning':'Descriptive pilot only: independent judges, cohort randomization, prior exposure, and uncertainty estimation are required.'}


def write_csv(path:str | Path,rows:list[dict]):
    if not rows:raise VekaError('cannot write empty manifest')
    out=Path(path)
    if out.exists():raise VekaError(f'refusing to overwrite existing artifact: {out}')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
