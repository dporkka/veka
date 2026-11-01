"""Veka 0.4 experimental-profile and fail-closed regression contract."""
import csv
import tempfile
import unittest
import contextlib
import io
import json
from pathlib import Path
from unittest.mock import patch

from veka.core import Discourse, Lexicon, VekaError, parse, score_human_trials
from veka.profiles import load_profile, profile_summary, convert_utterance

ROOT = Path(__file__).resolve().parents[1]


class ToneFreeVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tonal = load_profile('tonal')
        cls.toneless = load_profile('toneless')

    def test_variant_is_tone_free_and_has_no_lexical_collision(self):
        self.assertEqual(len(self.toneless), len(self.tonal))
        self.assertEqual(len(self.toneless), len(set(self.toneless)))
        self.assertFalse(any(any(mark in form for mark in 'áéíóú') for form in self.toneless))
        self.assertEqual(set(self.toneless)-set(self.tonal), {'fok', 'lek', 'hok', 'gon'})
        self.assertEqual(set(self.tonal)-set(self.toneless), {'pái','pál','lé','vén'})

    def test_substitutions_preserve_part_of_speech_and_english_gloss(self):
        for old,new in [('pái','fok'),('pál','lek'),('lé','hok'),('vén','gon')]:
            before,after = self.tonal[old], self.toneless[new]
            self.assertEqual((before.gloss,before.pos,before.valency,before.kind),
                             (after.gloss,after.pos,after.valency,after.kind))
            self.assertNotIn(old,self.toneless)
            self.assertNotIn(new,self.tonal)

    def test_profile_parser_rejects_words_from_opposite_profile(self):
        a=parse('Mi pái mel.', self.tonal)
        b=parse('Mi fok mel.', self.toneless)
        self.assertEqual(a['predicate'],'pái')
        self.assertEqual(b['predicate'],'fok')
        with self.assertRaises(VekaError):parse('Mi pái mel.',self.toneless)
        with self.assertRaises(VekaError):parse('Mi fok mel.',self.tonal)

    def test_form_conversion_is_token_aware_and_reversible(self):
        sentence='Mi pái mel to ti. Pál lé vén.'
        converted=convert_utterance(sentence,'toneless')
        self.assertEqual(converted,'Mi fok mel to ti. Lek hok gon.')
        self.assertEqual(convert_utterance(converted,'tonal'),sentence)
        self.assertEqual(convert_utterance('páile', 'toneless'), 'páile')
        self.assertEqual(convert_utterance('pái-pál', 'toneless'), 'fok-lek')

    def test_audit_reports_current_profile_without_claiming_perceptual_success(self):
        r=profile_summary('toneless')
        self.assertEqual(r['headwords'], 1025)
        self.assertEqual(r['rising_headwords'], 0)
        self.assertEqual(r['substitutions'], 4)
        self.assertEqual(r['structural_minimal_pair_count'],2320)
        self.assertFalse(r['acoustically_validated'])

    def test_profile_matched_corpus_parses_as_same_semantics(self):
        data=json.loads((ROOT/'data/profile_pairs_v04.json').read_text())
        self.assertEqual(len(data['items']),8)
        mapping={'pái':'fok','pál':'lek','lé':'hok','vén':'gon'}
        for item in data['items']:
            with self.subTest(item=item['id']):
                self.assertEqual(convert_utterance(item['tonal'],'toneless'),item['toneless'])
                tonal=parse(item['tonal'],self.tonal,strict=True)
                toneless=parse(item['toneless'],self.toneless,strict=True)
                renamed={k:(' '.join(mapping.get(x,x) for x in v.split()) if isinstance(v,str) else v)
                         for k,v in tonal.items()}
                self.assertEqual(renamed,toneless)

    def test_original_compounds_not_partially_rewritten(self):
        tonal_roots={'pái','pál','lé','vén'}
        compounds=[e for e in self.tonal.values() if e.kind=='compound']
        self.assertGreater(len(compounds),500)
        self.assertFalse(any(set(e.form.split('-')) & tonal_roots for e in compounds))

    def test_invalid_profile_or_collision_rejected(self):
        with self.assertRaises(VekaError):load_profile('tonelesss')
        with tempfile.TemporaryDirectory() as d:
            dir=Path(d)
            (dir/'lexicon.csv').write_bytes((ROOT/'data/lexicon.csv').read_bytes())
            (dir/'tone_free_ablation.csv').write_text('tonal_form,toneless_candidate,gloss,status\n'
                'pái,mi,remember,invalid\npál,lek,hill,invalid\nlé,hok,idea,invalid\nvén,gon,trust,invalid\n')
            with self.assertRaises(VekaError):load_profile('toneless',data_dir=dir)


class ParserIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lex=Lexicon.from_csv(ROOT/'data/lexicon.csv')

    def test_rejects_multiple_trailing_terminators(self):
        for utterance in ['Mi gos??', 'Mi gos.!', 'Mi gos!!!', 'Mi gos...', 'Mi gos!?']:
            with self.subTest(utterance=utterance),self.assertRaises(VekaError):
                parse(utterance,self.lex)

    def test_nested_possession_has_a_bounded_parse_depth(self):
        # Compact grammar must reject pathological recursive possessions, not crash.
        sentence='Ren ' + 'de ren '*40 + 'pa gos.'
        with self.assertRaises(VekaError):
            parse(sentence,self.lex)

    def test_listener_cannot_receive_same_meaning_in_both_conditions(self):
        row={'participant_id':'P1','trial_id':'1','condition':'explicit','elapsed_ms':'1000',
             'repairs':'0','correct':'1','confidence':'1','critical':'0'}
        with self.assertRaises(VekaError):
            score_human_trials([row,dict(row,condition='compact')])

    def test_score_rejects_unknown_conditions(self):
        row={'participant_id':'P1','trial_id':'1','condition':'invented','elapsed_ms':'1000',
             'repairs':'0','correct':'1','confidence':'1','critical':'0'}
        with self.assertRaises(VekaError):score_human_trials([row])

class CLIProfileTests(unittest.TestCase):
    def call_cli(self, argv):
        from veka.__main__ import main
        out=io.StringIO(); err=io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status=main(argv)
        return status, out.getvalue(), err.getvalue()

    def test_explicit_tone_free_parse_and_fail_closed_lexicon(self):
        code,out,_=self.call_cli(['parse','Mi fok mel.','--profile','toneless'])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out)['predicate'],'fok')
        code,_,err=self.call_cli(['parse','Mi pái mel.','--profile','toneless'])
        self.assertEqual(code,2)
        self.assertIn('unknown',err)

    def test_profile_summary_and_conversion(self):
        code,out,_=self.call_cli(['profile','toneless'])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out)['rising_headwords'],0)
        code,out,_=self.call_cli(['convert','Mi pái mel.','--target','toneless'])
        self.assertEqual(code,0)
        self.assertEqual(json.loads(out)['converted'],'Mi fok mel.')

    def test_lookup_uses_selected_profile(self):
        code,out,_=self.call_cli(['lookup','remember','--profile','toneless'])
        self.assertEqual(code,0)
        self.assertTrue(any(e['form']=='fok' for e in json.loads(out)['results']))


if __name__=='__main__':unittest.main()
