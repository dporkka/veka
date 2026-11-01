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
from .profiles import load_profile, profile_summary, convert_utterance, PROFILES

DATA=Path(__file__).resolve().parents[1]/'data'


def main(argv=None):
    ap=argparse.ArgumentParser(prog='python -m veka',description='Veka 0.3 experimental language toolkit')
    sub=ap.add_subparsers(dest='command',required=True)
    t=sub.add_parser('check',help='check phonotactics');t.add_argument('word')
    t=sub.add_parser('parse',help='parse a single clause, with exact quantities and quantifiers');t.add_argument('sentence')
    t.add_argument('--subject',action='append',default=[]);t.add_argument('--object',action='append',default=[])
    t.add_argument('--recipient',action='append',default=[]);t.add_argument('--strict',action='store_true')
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
    t=sub.add_parser('profile',help='inspect a separately versioned experimental vocabulary')
    t.add_argument('name',choices=PROFILES)
    t=sub.add_parser('convert',help='convert tonal root tokens in text without grammatical inference')
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
        elif args.command=='study-assign':
            items=json.loads((DATA/'study_items_v03.json').read_text(encoding='utf8'))
            result=write_manifest(items,args.participant,args.output,args.seed)
        else:
            lex=load_profile(getattr(args,'profile','tonal'))
            if args.command=='parse':
                result=parse(args.sentence,lex,
                    Discourse(subjects=tuple(args.subject),objects=tuple(args.object),
                              recipients=tuple(args.recipient)),strict=args.strict)
            elif args.command=='logic':
                result=parse_logic(args.expression,lex,strict=args.strict)
            elif args.command=='audit':
                audit=analyze_root_confusions(lex)
                if args.output:Path(args.output).write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
                result={k:v for k,v in audit.items() if k!='minimal_pairs'}
                result['profile'] = args.profile
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
