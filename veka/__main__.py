"""Run: python -m veka --help"""
import argparse
import csv
import json
from pathlib import Path
import sys

from .core import (Lexicon,Discourse,VekaError,validate_word,syllabify,parse,
                   render_svg,evaluate_stimuli,score_human_trials)
from .numbers import spell_number,read_number
from .logic import parse_logic
from .phonology import analyze_root_confusions
from .study import write_manifest
from .international import (read_candidates, read_evidence, audit_candidates,
                            compound_family_report, derive_noun_modifier,
                            generate_recognition_manifest, summarize_recognition_scores,
                            write_csv)

from .profiles import load_profile, profile_summary, convert_utterance, PROFILES
from .experimental_v05 import (DERIVATIONS, derive, experimental_lexicon,
                                correlative, audit_experimental_v05)

DATA=Path(__file__).resolve().parents[1]/'data'


def main(argv=None):
    ap=argparse.ArgumentParser(prog='python -m veka',description='Veka 0.3 language + noncanonical Veka 0.4 research tools')
    sub=ap.add_subparsers(dest='command',required=True)
    t=sub.add_parser('check',help='check phonotactics');t.add_argument('word')
    t=sub.add_parser('parse',help='parse a single clause, with exact quantities and quantifiers');t.add_argument('sentence')
    t.add_argument('--subject',action='append',default=[]);t.add_argument('--object',action='append',default=[])
    t.add_argument('--recipient',action='append',default=[]);t.add_argument('--strict',action='store_true')
    t.add_argument('--experimental-v05',action='store_true',help='opt into unapproved derivative forms')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('logic',help='parse fully scoped AND/OR/IF/NOT expressions');t.add_argument('expression')
    t.add_argument('--strict',action=argparse.BooleanOptionalAction,default=True)
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('number',help='convert between decimal numbers and canonical spoken Veka')
    t.add_argument('mode',choices=['spell','read']);t.add_argument('value')
    t=sub.add_parser('lookup',help='search headwords by Veka form or English gloss')
    t.add_argument('query');t.add_argument('--limit',type=int,default=20)
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('render',help='export native syllable blocks as SVG')
    t.add_argument('sentence');t.add_argument('--output',required=True)
    sub.add_parser('benchmark',help='deterministic parse-equivalence and syllable-count evaluation')
    t=sub.add_parser('score',help='score actual listener trials CSV');t.add_argument('csv_file')
    t=sub.add_parser('audit',help='lexical structural confusion audit (not speech testing)')
    t.add_argument('--top',type=int,default=20);t.add_argument('--output')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('study-assign',help='create a balanced study manifest without audio/data')
    t.add_argument('--participant',required=True);t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--output',required=True)
    t=sub.add_parser('international-audit',help='audit proposed noncanonical international forms and donor citations')
    t.add_argument('--candidates',default=str(DATA/'international_candidates_v04.csv'))
    t.add_argument('--evidence',default=str(DATA/'international_evidence_v04.csv'))
    t.add_argument('--output',help='write full JSON audit (never canonicalize proposals)')
    t=sub.add_parser('international-family',help='audit existing noun-modifier compounds or inspect an unregistered pair')
    t.add_argument('--noun');t.add_argument('--adjective')
    t=sub.add_parser('international-manifest',help='blind recognition manifest and separate researcher key; no participant data')
    t.add_argument('--participant',required=True);t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--output',required=True);t.add_argument('--answer-key',required=True)
    t.add_argument('--candidates',default=str(DATA/'international_candidates_v04.csv'))
    t=sub.add_parser('international-score',help='aggregate real manually annotated lexical recognition trials')
    t.add_argument('--answer-key',required=True);t.add_argument('--annotated',required=True)
    t=sub.add_parser('experimental-derive',help='inspect noncanonical typed verb derivative')
    t.add_argument('root');t.add_argument('operator',choices=sorted(DERIVATIONS))
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('experimental-correlative',help='inspect semantic grid without inventing spoken forms')
    t.add_argument('series');t.add_argument('dimension')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('experimental-audit',help='validate candidate derivations without adopting them')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('profile',help='inspect independently versioned vocabulary profile')
    t.add_argument('name',choices=PROFILES)
    t=sub.add_parser('convert',help='token-aware conversion between experiment profiles, not grammar validation')
    t.add_argument('utterance');t.add_argument('--target',choices=PROFILES,required=True)
    args=ap.parse_args(argv)
    try:
        if args.command=='profile':
            result=profile_summary(args.name)
        elif args.command=='convert':
            result={'source':args.utterance,'target_profile':args.target,
                    'converted':convert_utterance(args.utterance,args.target),
                    'grammatically_validated':False}
        elif args.command=='check':
            if not validate_word(args.word):raise VekaError('illegal form')
            result={'form':args.word,'syllables':syllabify(args.word)}
        elif args.command=='render':
            data=render_svg(args.sentence)
            Path(args.output).write_text(data,encoding='utf-8')
            result={'output':str(args.output),'bytes':len(data.encode())}
        elif args.command=='number':
            result={'value':args.value,'result':spell_number(args.value) if args.mode=='spell' else read_number(args.value)}
        elif args.command=='score':
            with open(args.csv_file, newline='', encoding='utf-8') as f:
                result=score_human_trials(list(csv.DictReader(f)))
        elif args.command in ('experimental-derive','experimental-correlative','experimental-audit'):
            lex=load_profile(args.profile)
            if args.command=='experimental-derive':
                result=derive(args.root,args.operator,lex).as_dict()
            elif args.command=='experimental-correlative':
                result=correlative(args.series,args.dimension,lex)
            else:result=audit_experimental_v05(lex)
        elif args.command=='international-manifest':
            if Path(args.output).resolve()==Path(args.answer_key).resolve():
                raise VekaError('participant sheet and researcher key MUST use different files')
            if Path(args.output).exists() or Path(args.answer_key).exists():
                raise VekaError('refusing to overwrite an existing manifest or answer key')
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            rows=read_candidates(args.candidates)
            participant,key=generate_recognition_manifest(rows,lex,args.participant,args.seed)
            write_csv(args.output,participant)
            write_csv(args.answer_key,key)
            result={'participant_id':args.participant,'trials':len(participant),
                    'core':sum(r['condition']=='core' for r in key),
                    'international':sum(r['condition']=='international' for r in key),
                    'participant_sheet':args.output,'researcher_key':args.answer_key,
                    'human_data_collected':False,'audio_recorded':False}
        elif args.command=='international-score':
            with open(args.answer_key,encoding='utf8',newline='') as f:
                key=list(csv.DictReader(f))
            with open(args.annotated,encoding='utf8',newline='') as f:
                actual=list(csv.DictReader(f))
            result=summarize_recognition_scores(key,actual)
        elif args.command=='international-audit':
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            result=audit_candidates(read_candidates(args.candidates),lex,read_evidence(args.evidence))
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='international-family':
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            if bool(args.noun)!=bool(args.adjective):
                raise VekaError('--noun and --adjective are required together')
            result=(derive_noun_modifier(args.noun,args.adjective,lex)
                    if args.noun else compound_family_report(lex))
        elif args.command=='study-assign':
            items=json.loads((DATA/'study_items_v03.json').read_text(encoding='utf8'))
            result=write_manifest(items,args.participant,args.output,args.seed)
        else:
            lex=load_profile(getattr(args,'profile','tonal'))
            if args.command=='parse':
                if args.experimental_v05: lex=experimental_lexicon(lex)
                result=parse(args.sentence,lex,
                    Discourse(subjects=tuple(args.subject),objects=tuple(args.object),
                              recipients=tuple(args.recipient)),strict=args.strict)
            elif args.command=='logic':
                result=parse_logic(args.expression,lex,strict=args.strict)
            elif args.command=='audit':
                audit=analyze_root_confusions(lex)
                if args.output:Path(args.output).write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
                result={k:v for k,v in audit.items() if k!='minimal_pairs'}
                result['profile']=args.profile
                result['high_risk_pairs_sample']=audit['minimal_pairs'][:max(0,args.top)]
                if args.output:result['full_output']=args.output
            elif args.command=='lookup':
                results=[dict(form=e.form,gloss=e.gloss,pos=e.pos,kind=e.kind)
                         for e in lex.values() if args.query.casefold() in (e.form+' '+e.gloss).casefold()]
                result={'total_matches':len(results),'results':results[:max(1,args.limit)]}
            else:
                result=evaluate_stimuli(json.loads((DATA/'stimuli.json').read_text(encoding='utf-8')),lex)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (VekaError,OSError,UnicodeError) as exc:
        print('VEKA ERROR: '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
