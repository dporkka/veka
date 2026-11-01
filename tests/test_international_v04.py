"""Tests for Veka 0.4 noncanonical international-lexicon research tools."""
import csv
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError, parse
from veka.international import (audit_candidates, generate_recognition_manifest,
                                summarize_recognition_scores, derive_noun_modifier,
                                compound_family_report, read_candidates, audit_evidence)

ROOT = Path(__file__).resolve().parents[1]

class InternationalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT/'data/lexicon.csv')
        cls.candidates = read_candidates(ROOT/'data/international_candidates_v04.csv')

    def test_exactly_100_canonical_concepts_and_no_canonical_reassignment(self):
        self.assertEqual(len(self.candidates), 100)
        self.assertEqual(len(set(r['concept_id'] for r in self.candidates)),100)
        for r in self.candidates:
            entry = self.lex[r['core_form']]
            self.assertEqual((entry.gloss,entry.pos,entry.kind),
                             (r['gloss'],r['pos'],'root'))
        self.assertEqual(len(self.lex),1025)

    def test_draft_candidates_are_phonotactically_valid_and_noncanonical(self):
        result=audit_candidates(self.candidates,self.lex)
        self.assertEqual(result['concept_count'],100)
        self.assertGreaterEqual(result['experimental_forms'],6)
        self.assertEqual(result['rejected_forms'],0)
        self.assertEqual(result['adopted_forms'],0)
        self.assertFalse(result['recognition_measured'])
        self.assertTrue(all(r['status']=='structurally_testable' for r in result['candidates']))

    def test_collision_and_operator_segmentation_fail_closed(self):
        sample=dict(self.candidates[0])
        sample['candidate_form']=sample['core_form']
        result=audit_candidates([sample],self.lex)
        self.assertEqual(result['rejected_forms'],1)
        sample['candidate_form']='fu-ka'  # 'fu' is a grammatical particle
        result=audit_candidates([sample],self.lex)
        self.assertEqual(result['rejected_forms'],1)
        sample['candidate_form']='kri-za'  # illegal consonant cluster
        result=audit_candidates([sample],self.lex)
        self.assertEqual(result['rejected_forms'],1)

    def test_duplicate_draft_lexeme_rejected_and_wrong_core_mapping_is_error(self):
        seed=next(r for r in self.candidates if r['candidate_form'])
        other=dict(seed,concept_id='another',gloss='another',candidate_form=seed['candidate_form'])
        with self.assertRaises(VekaError):
            audit_candidates([seed,other],self.lex)
        with self.assertRaises(VekaError):
            audit_candidates([dict(seed,gloss='fictional')],self.lex)

    def test_correlated_romance_languages_count_as_one_family(self):
        records=[dict(concept_id='C001',language='Spanish',language_family='Indo-European',
                      attested_form='dato',citation='example://a',reviewer='a',verified='yes'),
                 dict(concept_id='C001',language='Portuguese',language_family='Indo-European',
                      attested_form='dado',citation='example://b',reviewer='b',verified='yes'),
                 dict(concept_id='C001',language='Indonesian',language_family='Austronesian',
                      attested_form='data',citation='example://c',reviewer='c',verified='yes')]
        result=audit_evidence(records,self.candidates)
        self.assertEqual(result['by_concept']['C001']['attested_languages'],3)
        self.assertEqual(result['by_concept']['C001']['independent_families'],2)
        self.assertFalse(result['recognition_measured'])
        with self.assertRaises(VekaError):
            audit_evidence([dict(records[0],citation='')],self.candidates)

    def test_no_donor_evidence_is_not_interpreted_as_recognition_proof(self):
        report=audit_candidates(self.candidates,self.lex)
        self.assertEqual(report['attested_forms'],0)
        self.assertEqual(report['adopted_forms'],0)
        self.assertEqual(report['human_participants'],0)

class MorphologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex=Lexicon.from_csv(ROOT/'data/lexicon.csv')

    def test_existing_compound_preserved_and_unlisted_pair_noncanonical(self):
        entry=derive_noun_modifier('ren','sak',self.lex)
        self.assertEqual(entry['form'],'ren-sak')
        self.assertTrue(entry['canonical'])
        other=derive_noun_modifier('sil','bon',self.lex)
        self.assertEqual(other['form'],'sil-bon')
        self.assertFalse(other['canonical'])
        self.assertNotIn('sil-bon',self.lex)
        with self.assertRaises(VekaError):
            derive_noun_modifier('pa','ren',self.lex)

    def test_compound_family_report_does_not_promote_hypothetical_derivations(self):
        report=compound_family_report(self.lex)
        self.assertEqual(report['existing_compounds'],708)
        self.assertEqual(report['invalid_compounds'],0)
        self.assertEqual(report['new_entries'],0)

class RecognitionStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex=Lexicon.from_csv(ROOT/'data/lexicon.csv')
        cls.rows=read_candidates(ROOT/'data/international_candidates_v04.csv')

    def test_reproducible_balanced_single_exposure_assignments(self):
        a=generate_recognition_manifest(self.rows,self.lex,'p001',seed=4)
        b=generate_recognition_manifest(self.rows,self.lex,'p001',seed=4)
        c=generate_recognition_manifest(self.rows,self.lex,'p002',seed=4)
        self.assertEqual(a,b)
        self.assertNotEqual(a,c)
        visible,key=a
        self.assertEqual(len(visible),len(key))
        self.assertEqual(len(set(t['trial_id'] for t in visible)),len(visible))
        self.assertTrue(all('gloss' not in t and 'condition' not in t for t in visible))
        self.assertEqual(abs(sum(x['condition']=='international' for x in key)-sum(x['condition']=='core' for x in key)),0)
        self.assertTrue(all(x['status']=='unverified_draft' for x in key))

    def test_scoring_requires_real_annotated_results_not_guesses(self):
        visible,key=generate_recognition_manifest(self.rows,self.lex,'p001',seed=4)
        with self.assertRaises(VekaError):
            summarize_recognition_scores(key,[])
        scored=[{'trial_id':r['trial_id'],'correct':str(i%2),'response_ms':'1200',
                 'repair_count':'0'} for i,r in enumerate(key)]
        result=summarize_recognition_scores(key,scored)
        self.assertEqual(result['trials'],len(key))
        self.assertIn('core',result['conditions'])
        self.assertIn('international',result['conditions'])
        self.assertFalse(result['causal_effect_established'])
        with self.assertRaises(VekaError):
            summarize_recognition_scores(key,scored[:-1])
        with self.assertRaises(VekaError):
            summarize_recognition_scores(key,scored+[scored[0]])
        scored[0]['correct']='yes'
        with self.assertRaises(VekaError):
            summarize_recognition_scores(key,scored)

    def test_candidate_rejected_when_canonical_parser_would_confuse_meaning(self):
        # Experimentation cannot sneak novel words into the parser or alter canonical meanings.
        with self.assertRaises(VekaError):
            parse('Mi lin da-ta.', self.lex)

class InternationalCLIRegressionTests(unittest.TestCase):
    def test_audit_output_file_is_valid_json(self):
        import json
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'audit.json'
            result=subprocess.run([sys.executable,'-m','veka','international-audit','--output',str(output)],
                                  cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            audit=json.loads(output.read_text(encoding='utf8'))
            self.assertEqual(audit['concept_count'],100)

if __name__=='__main__': unittest.main()
