"""Run: python -m veka --help"""
import argparse
import csv
import json
from pathlib import Path
import sys

from .core import (Lexicon,Discourse,VekaError,validate_word,syllabify,parse,
                   render_svg,read_svg,evaluate_stimuli,score_human_trials)
from .numbers import spell_number,read_number
from .logic import parse_logic
from .phonology import analyze_root_confusions
from .lexical_risk import load_priorities, audit_lexical_risk, DEFAULT_PRIORITIES
from .study import write_manifest
from .profiles import load_profile, profile_summary, convert_utterance, PROFILES
from .extended import parse_extended, derive, correlative, SERIES, DOMAINS
from .international import (read_candidates, read_evidence, audit_candidates,
                            compound_family_report, derive_noun_modifier,
                            generate_recognition_manifest, summarize_recognition_scores,
                            write_csv)

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
    t=sub.add_parser('read-script',help='recover romanization from rendered SVG metadata, not OCR')
    t.add_argument('--input',required=True)
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
    t=sub.add_parser('lexical-risk',help='rank symbolic phonological risks and experimental replacement candidates')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--priorities',default=str(DEFAULT_PRIORITIES))
    t.add_argument('--target',action='append',default=None)
    t.add_argument('--top',type=int,default=10)
    t.add_argument('--candidates',type=int,default=5)
    t.add_argument('--output')
    t=sub.add_parser('international-audit',help='audit noncanonical loanword candidates and donor evidence')
    t.add_argument('--candidates',default=str(DATA/'international_candidates_v04.csv'))
    t.add_argument('--evidence',default=str(DATA/'international_evidence_v04.csv'))
    t.add_argument('--output')
    t=sub.add_parser('international-family',help='inspect existing noun-modifier compounds')
    t.add_argument('--noun');t.add_argument('--adjective')
    t=sub.add_parser('international-manifest',help='blind recognition manifest and researcher key')
    t.add_argument('--participant',required=True);t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--output',required=True);t.add_argument('--answer-key',required=True)
    t.add_argument('--candidates',default=str(DATA/'international_candidates_v04.csv'))
    t=sub.add_parser('international-score',help='score manually annotated recognition trials')
    t.add_argument('--answer-key',required=True);t.add_argument('--annotated',required=True)
    t=sub.add_parser('extend',help='experimental Veka 0.5 typed morphology and bounded embedding')
    t.add_argument('sentence');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('derive',help='inspect compositional event-derived vocabulary')
    t.add_argument('word');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('correlative',help='inspect one generated reference form')
    t.add_argument('word');t.add_argument('--profile',choices=PROFILES,default='tonal')
    args=ap.parse_args(argv)
    try:
        if args.command=='lexical-risk':
            lex=load_profile(args.profile)
            priorities=load_priorities(args.priorities,lex)
            result=audit_lexical_risk(lex,priorities,targets=args.target,top=args.top,
                                      candidates=args.candidates,profile=args.profile)
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='extend':
            result=parse_extended(args.sentence,load_profile(args.profile),strict=True)
        elif args.command=='derive':
            result=derive(args.word,load_profile(args.profile))
        elif args.command=='correlative':
            result=correlative(args.word,load_profile(args.profile))
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
        elif args.command=='international-manifest':
            if Path(args.output).resolve()==Path(args.answer_key).resolve():
                raise VekaError('participant sheet and researcher key MUST use different files')
            if Path(args.output).exists() or Path(args.answer_key).exists():
                raise VekaError('refusing to overwrite an existing manifest or answer key')
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            rows=read_candidates(args.candidates)
            participant,key=generate_recognition_manifest(rows,lex,args.participant,args.seed)
            write_csv(args.output,participant);write_csv(args.answer_key,key)
            result={'participant_id':args.participant,'trials':len(participant),
                    'participant_sheet':args.output,'researcher_key':args.answer_key,
                    'human_data_collected':False,'audio_recorded':False}
        elif args.command=='international-score':
            with open(args.answer_key,encoding='utf8',newline='') as f:
                key=list(csv.DictReader(f))
            with open(args.annotated,encoding='utf8',newline='') as f:
                actual=list(csv.DictReader(f))
            result=summarize_recognition_scores(key,actual)
        elif args.command=='profile':
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
        elif args.command=='read-script':
            result={'romanized':read_svg(Path(args.input).read_text(encoding='utf-8')),
                    'source':'SVG syllable metadata', 'optical_recognition':False}
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
