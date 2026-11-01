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
from .compound_semantics import audit_compound_semantics, load_compound_reviews
from .study import write_manifest
from .meaning_v06 import make_meaning_packet, write_meaning_packet
from .communication_v07 import generate_cases, audit_communication
from .listening_v06 import (DEFAULT_CONTRASTS, load_contrasts, make_packet,
                             write_packet, read_csv, score_packet)
from .audio_preflight import audit_recordings
from .profiles import load_profile, profile_summary, convert_utterance, PROFILES
from .aesthetics import rank_candidates, prosody_guidance
from .spoken_study import write_spoken_manifest
from .extended import parse_extended, derive, correlative, SERIES, DOMAINS
from .discourse import parse_discourse
from .registers import inspect_register, REGISTERS
from .beginner import guide_sentence, format_beginner_guide
from .semantic_families import describe_family, format_semantic_family
from .global_comprehension import (read_global_csv, audit_global_candidates,
                                   summarize_global_trials, EVIDENCE_FIELDS, TRIAL_FIELDS)
from .international import (read_candidates, read_evidence, audit_candidates,
                            compound_family_report, derive_noun_modifier,
                            generate_recognition_manifest, summarize_recognition_scores,
                            write_csv)
from .cognates import read_pilot, audit_pilot, make_pilot_manifest, score_pilot
from .cognate_session import read_blind_manifest, write_blind_session, prepare_judge_sheet
from .cognate_review import read_cognate_leads, audit_cognate_leads

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
    t=sub.add_parser('beginner',help='first-sight word-by-word English guide; international draft cues are NOT Veka')
    t.add_argument('sentence');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--no-cues',action='store_true',help='hide unverified international associations')
    t.add_argument('--families',action='store_true',help='add structural families without registering new words')
    t.add_argument('--readings',action='store_true',help='show exact-match unverified English/Portuguese editorial readings')
    t.add_argument('--format',choices=('text','json'),default='text')
    t=sub.add_parser('family',help='inspect canonical compounds and opt-in derived word families')
    t.add_argument('word');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--limit',type=int,default=12)
    t.add_argument('--no-cues',action='store_true')
    t.add_argument('--format',choices=('text','json'),default='text')
    t=sub.add_parser('lookup',help='search headwords by Veka form or English gloss')
    t.add_argument('query');t.add_argument('--limit',type=int,default=20)
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('render',help='export native syllable blocks as SVG')
    t.add_argument('sentence');t.add_argument('--output',required=True)
    t=sub.add_parser('read-script',help='recover romanization from rendered SVG metadata, not OCR')
    t.add_argument('--input',required=True)
    sub.add_parser('benchmark',help='deterministic parse-equivalence and syllable-count evaluation')
    t=sub.add_parser('communication-audit',help='synthetic meaning reversals and context-safety checks (not human data)')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--domains',default=str(DATA/'communication_domains_v07.json'))
    t=sub.add_parser('score',help='score actual listener trials CSV');t.add_argument('csv_file')
    t=sub.add_parser('audit',help='lexical structural confusion audit (not speech testing)')
    t.add_argument('--top',type=int,default=20);t.add_argument('--output')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('meaning-plan',help='blinded meaning-recovery participant/key/recording packet')
    t.add_argument('--participant',required=True)
    t.add_argument('--arm',required=True,type=int,choices=(0,1))
    t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--participant-csv',required=True)
    t.add_argument('--key-csv',required=True)
    t.add_argument('--recording-csv',required=True)
    t=sub.add_parser('study-assign',help='legacy RESEARCHER-ONLY manifest exposing meanings and conditions (no audio)')
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
    t=sub.add_parser('listening-plan',help='create blinded ABX participant/key/recording study packet')
    t.add_argument('--participant',required=True)
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--talker',action='append',default=[])
    t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--arm',type=int,choices=(0,1),required=True)
    t.add_argument('--contrasts',default=str(DEFAULT_CONTRASTS))
    t.add_argument('--participant-csv',required=True)
    t.add_argument('--key-csv',required=True)
    t.add_argument('--recording-csv',required=True)
    t=sub.add_parser('listening-preflight',help='audit real ABX WAV PCM before manual speech review')
    t.add_argument('--recording-csv',required=True)
    t.add_argument('--audio-root',required=True)
    t=sub.add_parser('listening-score',help='score complete responses with recorded WAV verification')
    t.add_argument('--key-csv',required=True)
    t.add_argument('--responses-csv',required=True)
    t.add_argument('--recording-csv',required=True)
    t.add_argument('--audio-root',required=True)
    t=sub.add_parser('compound-semantics',help='editorial surface/meaning review; no listener evidence')
    t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--review-file',help='optional CSV of explicit editorial classifications')
    t.add_argument('--top',type=int,default=10)
    t.add_argument('--output',help='write the complete JSON report to file')
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
    t=sub.add_parser('cognate-audit',help='audit 0.7 noncanonical cognate pilot and evidence')
    t.add_argument('--candidates',default=str(DATA/'cognate_candidates_v07.csv'))
    t.add_argument('--evidence',default=str(DATA/'cognate_evidence_v07.csv'))
    t.add_argument('--output')
    t=sub.add_parser('cognate-leads',help='review sourced but unverified cognate attestations')
    t.add_argument('--candidates',default=str(DATA/'cognate_candidates_v07.csv'))
    t.add_argument('--leads',default=str(DATA/'cognate_source_leads_v07.csv'))
    t.add_argument('--output')
    t=sub.add_parser('cognate-manifest',help='blinded 0.7 cognate study packet')
    t.add_argument('--participant',required=True);t.add_argument('--arm',required=True,type=int,choices=(0,1))
    t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--candidates',default=str(DATA/'cognate_candidates_v07.csv'))
    t.add_argument('--output',required=True);t.add_argument('--answer-key',required=True)
    t=sub.add_parser('cognate-session',help='export an answer-key-free JSON session from a blinded participant CSV')
    t.add_argument('--manifest',required=True);t.add_argument('--output',required=True)
    t=sub.add_parser('cognate-judge-sheet',help='create private, blank manual adjudication sheet from participant responses')
    t.add_argument('--answer-key',required=True);t.add_argument('--responses',required=True);t.add_argument('--output',required=True)
    t=sub.add_parser('cognate-score',help='score manually judged 0.7 cognate trials')
    t.add_argument('--answer-key',required=True);t.add_argument('--annotated',required=True)
    t=sub.add_parser('extend',help='experimental Veka 0.5 typed morphology and bounded embedding')
    t.add_argument('sentence');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('derive',help='inspect compositional event-derived vocabulary')
    t.add_argument('word');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('correlative',help='inspect one generated reference form')
    t.add_argument('word');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('discourse',help='experimental Veka 0.6 topic/focus, domain and temporal scope')
    t.add_argument('sentence');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('register-check',help='check canonical Core/Precise versus opt-in Research syntax')
    t.add_argument('sentence');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t.add_argument('--max-register',choices=REGISTERS,default='core')
    t=sub.add_parser('aesthetics',help='screen proposed word forms using text-only sound-shape heuristics')
    t.add_argument('forms',nargs='+');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('prosody',help='guidance for delivery of strictly parsed Veka without audio')
    t.add_argument('sentence');t.add_argument('--profile',choices=PROFILES,default='tonal')
    t=sub.add_parser('spoken-study-assign',help='generate condition-blinded listening packet (no audio)')
    t.add_argument('--participant',required=True)
    t.add_argument('--profile',choices=PROFILES,required=True)
    t.add_argument('--arm',type=int,choices=(0,1),required=True)
    t.add_argument('--seed',type=int,default=20261101)
    t.add_argument('--output',required=True)
    t.add_argument('--researcher-key',required=True)
    t=sub.add_parser('global-audit',help='review sourced multilingual evidence without promoting any vocabulary')
    t.add_argument('--candidates',default=str(DATA/'international_candidates_v04.csv'))
    t.add_argument('--evidence',default=str(DATA/'global_evidence_v07.csv'))
    t.add_argument('--output')
    t=sub.add_parser('global-score',help='describe real first-sight comprehension trials by language family')
    t.add_argument('--candidates',default=str(DATA/'international_candidates_v04.csv'))
    t.add_argument('--trials',default=str(DATA/'global_trials_v07.csv'))
    t.add_argument('--output')
    args=ap.parse_args(argv)
    try:
        if args.command=='communication-audit':
            seeds=json.loads(Path(args.domains).read_text(encoding='utf-8'))
            lex=load_profile(args.profile)
            result=audit_communication(generate_cases(seeds,lex),lex,profile=args.profile)
        elif args.command=='register-check':
            result=inspect_register(args.sentence,profile=args.profile,max_register=args.max_register)
        elif args.command=='meaning-plan':
            items=json.loads((DATA/'study_items_v03.json').read_text(encoding='utf-8'))
            packet=make_meaning_packet(items,args.participant,arm=args.arm,seed=args.seed)
            result=write_meaning_packet(packet,args.participant_csv,
                                        args.key_csv,args.recording_csv)
        elif args.command=='cognate-audit':
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            result=audit_pilot(read_pilot(args.candidates),lex,read_evidence(args.evidence))
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='cognate-leads':
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            result=audit_cognate_leads(read_pilot(args.candidates),
                                      read_cognate_leads(args.leads),lex)
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='cognate-manifest':
            if Path(args.output).resolve()==Path(args.answer_key).resolve():
                raise VekaError('participant sheet and researcher key must be separate files')
            if Path(args.output).exists() or Path(args.answer_key).exists():
                raise VekaError('refusing to overwrite existing study files')
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            participants,key=make_pilot_manifest(read_pilot(args.candidates),lex,
                                                  args.participant,seed=args.seed,arm=args.arm)
            write_csv(args.output,participants)
            write_csv(args.answer_key,key)
            result={'schema_version':'veka.cognate-manifest.v07',
                    'trials':len(participants),'participant_sheet':args.output,
                    'researcher_key':args.answer_key,
                    'human_data_collected':False,'audio_recorded':False}
        elif args.command=='cognate-session':
            if Path(args.manifest).resolve() == Path(args.output).resolve():
                raise VekaError('input and output must be separate files')
            result=write_blind_session(read_blind_manifest(args.manifest),args.output)
        elif args.command=='cognate-judge-sheet':
            result=prepare_judge_sheet(args.answer_key,args.responses,args.output)
        elif args.command=='cognate-score':
            with open(args.answer_key,encoding='utf8',newline='') as f:
                key=list(csv.DictReader(f))
            with open(args.annotated,encoding='utf8',newline='') as f:
                observed=list(csv.DictReader(f))
            result=score_pilot(key,observed)
        elif args.command=='beginner':
            result=guide_sentence(args.sentence,load_profile(args.profile),
                                  read_candidates(DATA/'international_candidates_v04.csv'),
                                  profile=args.profile,include_cues=not args.no_cues,
                                  include_families=args.families,include_readings=args.readings)
            if args.format=='text':
                print(format_beginner_guide(result))
                return 0
        elif args.command=='family':
            result=describe_family(args.word,load_profile(args.profile),
                                   read_candidates(DATA/'international_candidates_v04.csv'),
                                   limit=args.limit,include_cues=not args.no_cues)
            if args.format=='text':
                print(format_semantic_family(result))
                return 0
        elif args.command=='global-audit':
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            result=audit_global_candidates(read_candidates(args.candidates),lex,
                                           read_global_csv(args.evidence,EVIDENCE_FIELDS))
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='global-score':
            lex=Lexicon.from_csv(DATA/'lexicon.csv')
            rows=read_candidates(args.candidates)
            structural=audit_candidates(rows,lex)
            mapping={r['concept_id']:r['candidate_form'] for r in structural['candidates']
                     if r['status']=='structurally_testable'}
            result=summarize_global_trials(read_global_csv(args.trials,TRIAL_FIELDS),mapping)
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='listening-plan':
            lex=load_profile(args.profile)
            pairs=load_contrasts(args.contrasts,lex,args.profile)
            packet=make_packet(pairs,args.participant,tuple(args.talker or ('S01','S02')),
                               args.profile,seed=args.seed,arm=args.arm)
            write_packet(packet,args.participant_csv,args.key_csv,args.recording_csv)
            result={'schema_version':'veka.abx-plan.v06',
                    'participant':args.participant,'profile':args.profile,
                    'trials':len(packet[0]),'recording_jobs':len(packet[2]),
                    'participant_csv':args.participant_csv,'key_csv':args.key_csv,
                    'recording_csv':args.recording_csv,
                    'human_results_collected':False,'audio_recorded':False,
                    'warning':'Restricted answer key and recording manifest must not be shared with participants.'}
        elif args.command=='listening-preflight':
            result=audit_recordings(read_csv(args.recording_csv),args.audio_root)
        elif args.command=='listening-score':
            result=score_packet(read_csv(args.key_csv),read_csv(args.responses_csv),
                                read_csv(args.recording_csv),args.audio_root)
        elif args.command=='aesthetics':
            result={'profile':args.profile,
                    'ranked_candidates':rank_candidates(args.forms,load_profile(args.profile)),
                    'audio_generated':False,'empirically_validated':False}
        elif args.command=='prosody':
            result=prosody_guidance(args.sentence,load_profile(args.profile),profile=args.profile)
        elif args.command=='spoken-study-assign':
            items=json.loads((DATA/'spoken_aesthetics_items_v05.json').read_text(encoding='utf8'))['items']
            result=write_spoken_manifest(
                items,args.participant,args.profile,args.arm,
                args.output,args.researcher_key,args.seed)
        elif args.command=='lexical-risk':
            lex=load_profile(args.profile)
            priorities=load_priorities(args.priorities,lex)
            result=audit_lexical_risk(lex,priorities,targets=args.target,top=args.top,
                                      candidates=args.candidates,profile=args.profile)
            if args.output:
                Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        elif args.command=='compound-semantics':
            lex=load_profile(args.profile)
            reviews=(load_compound_reviews(args.review_file,lex) if args.review_file else {})
            result=audit_compound_semantics(lex,reviews,top=args.top)
            if args.output:
                full=audit_compound_semantics(lex,reviews)
                Path(args.output).write_text(json.dumps(full,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        elif args.command=='discourse':
            result=parse_discourse(args.sentence,load_profile(args.profile))
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
