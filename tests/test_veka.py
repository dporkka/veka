import json
import unittest
from pathlib import Path

from veka.core import (Lexicon, Discourse, VekaError, validate_word,
                       syllabify, parse, render_svg, evaluate_stimuli)

ROOT = Path(__file__).resolve().parents[1]


class VekaSoundTests(unittest.TestCase):
    def test_legal_contrasts_and_accents(self):
        for word in ('pal', 'pál', 'pái', 'dak', 'mel', 'mi', 'sun', 'lé', 'vén', 'ton', 'ai', 'au'):
            self.assertTrue(validate_word(word), word)

    def test_rejects_illegal_phonotactics(self):
        for word in ('pat', 'glo', 'pák', 'yi', 'wu', 'aiak', 'páiń', 'páuk', 'dakk', ''):
            self.assertFalse(validate_word(word), word)

    def test_compounds_are_segmented_at_morpheme_boundaries(self):
        self.assertEqual(syllabify('ren-sak'), ['ren', 'sak'])
        self.assertEqual(syllabify('pál'), ['pál'])
        with self.assertRaises(VekaError):
            syllabify('rensak')  # no implied boundaries for multiroot words


class VekaGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data' / 'lexicon.csv')

    def test_full_future_transitive(self):
        ast = parse('Mi fu dak mel to ti sun.', self.lex)
        self.assertEqual(ast['subject'], 'mi')
        self.assertEqual(ast['tense'], 'future')
        self.assertEqual(ast['predicate'], 'dak')
        self.assertEqual(ast['object'], 'mel')
        self.assertEqual(ast['recipient'], 'ti')
        self.assertEqual(ast['time'], 'sun')
        self.assertFalse(ast['compressed'])

    def test_negative_past_question_and_command(self):
        ast = parse('Ti pa ne ton mel ke?', self.lex)
        self.assertEqual((ast['tense'], ast['negative'], ast['question']), ('past', True, True))
        cmd = parse('Ha dak mel to mi.', self.lex)
        self.assertEqual((cmd['mood'], cmd['subject']), ('imperative', 'ti'))

    def test_predicative_modifier_not_confused_with_noun_phrase(self):
        ast = parse('Mel es kal.', self.lex)
        self.assertEqual((ast['subject'], ast['predicate'], ast['copula']), ('mel', 'kal', True))
        ast = parse('Mi lin mel kal de ti.', self.lex)
        self.assertEqual(ast['object'], 'mel kal de ti')

    def test_compression_requires_context_and_preserves_roles(self):
        with self.assertRaises(VekaError):
            parse('Fu dak sun.', self.lex)
        ctx = Discourse(subjects=('mi',), objects=('mel',), recipients=('ti',))
        ast = parse('Fu dak sun.', self.lex, context=ctx)
        self.assertEqual((ast['subject'], ast['object'], ast['recipient']), ('mi', 'mel', 'ti'))
        self.assertTrue(ast['compressed'])
        with self.assertRaises(VekaError):
            parse('Fu dak sun.', self.lex, context=Discourse(subjects=('mi','ti'), objects=('mel',), recipients=('ti',)))
        with self.assertRaises(VekaError):
            parse('Fu dak sun.', self.lex, context=ctx, strict=True)

    def test_ambiguity_and_unsafe_ellipsis(self):
        with self.assertRaises(VekaError):
            parse('Sa pa gos.', self.lex, context=Discourse(subjects=('Ana', 'Beni')))
        self.assertEqual(parse('Ana pa gos.', self.lex)['subject'], 'Ana')
        with self.assertRaises(VekaError):
            parse('Mi dak.', self.lex)  # missing obligatory object
        with self.assertRaises(VekaError):
            parse('Mi fu dak mel to ti to Ana.', self.lex)  # duplicate recipient
        with self.assertRaises(VekaError):
            parse('Mi ke dak mel.', self.lex)  # question placement

    def test_pronoun_requires_unique_active_referent_across_roles(self):
        context = Discourse(subjects=('Ana',), objects=('Beni',))
        with self.assertRaises(VekaError):
            parse('Sa pa gos.', self.lex, context=context)
        context = Discourse(subjects=('Ana',))
        self.assertEqual(parse('Sa pa gos.', self.lex, context=context)['subject'], 'Ana')

    def test_imperatives_are_not_past_commands_or_questions(self):
        with self.assertRaises(VekaError):
            parse('Ha pa dak mel.', self.lex)
        with self.assertRaises(VekaError):
            parse('Ha dak mel ke?', self.lex)

    def test_lexicon_has_one_thousand_unique_entries(self):
        self.assertEqual(len(self.lex), 1025)
        self.assertEqual(len({e.form for e in self.lex.values()}), 1025)
        self.assertGreaterEqual(sum('-' in e.form for e in self.lex.values()), 500)
        self.assertTrue(all(validate_word(e.form) for e in self.lex.values()))
        self.assertEqual(self.lex['pál'].gloss, 'hill')
        self.assertEqual(self.lex['pal'].gloss, 'garden')


class VekaWritingAndBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data' / 'lexicon.csv')

    def test_svg_renders_tonal_minimal_pair_and_escapes_text(self):
        level = render_svg('pal')
        rising = render_svg('pál')
        self.assertIn('<svg', level)
        self.assertIn('data-veka="pal"', level)
        self.assertNotEqual(level, rising)
        self.assertIn('data-tone="rising"', rising)
        self.assertIn('data-tone="level"', level)
        with self.assertRaises(VekaError):
            render_svg('<script>')

    def test_benchmark_reports_structural_not_empirical_metrics(self):
        stimuli = json.loads((ROOT / 'data' / 'stimuli.json').read_text())
        result = evaluate_stimuli(stimuli, self.lex)
        self.assertGreaterEqual(result['n_cases'], 20)
        self.assertEqual(result['parse_passes'], result['n_cases'])
        self.assertGreater(result['explicit_syllables'], result['compact_syllables'])
        self.assertFalse(result['measures_spoken_throughput'])
        self.assertFalse(result['measures_comprehension'])


if __name__ == '__main__':
    unittest.main()

class VekaHumanStudyScoringTests(unittest.TestCase):
    def test_scores_conditions_using_observed_results_only(self):
        from veka.core import score_human_trials
        trials = [
            {'participant_id':'p1','trial_id':'1','condition':'explicit','elapsed_ms':'4000','repairs':'0','correct':'1','confidence':'0.9','critical':'0'},
            {'participant_id':'p1','trial_id':'2','condition':'explicit','elapsed_ms':'5000','repairs':'1','correct':'1','confidence':'0.8','critical':'1'},
            {'participant_id':'p2','trial_id':'1','condition':'compact','elapsed_ms':'2000','repairs':'0','correct':'0','confidence':'0.9','critical':'1'},
            {'participant_id':'p2','trial_id':'2','condition':'compact','elapsed_ms':'3000','repairs':'1','correct':'1','confidence':'0.7','critical':'0'},
        ]
        r = score_human_trials(trials)
        self.assertEqual(r['explicit']['success_rate'],1.0)
        self.assertEqual(r['compact']['success_rate'],0.5)
        self.assertEqual(r['compact']['critical_errors'],1)
        self.assertEqual(r['compact']['correct_per_minute'],12.0)

    def test_rejects_bad_or_duplicate_trials(self):
        from veka.core import score_human_trials
        row={'participant_id':'p1','trial_id':'1','condition':'compact','elapsed_ms':'-1',
             'repairs':'0','correct':'1','confidence':'0.9','critical':'0'}
        with self.assertRaises(VekaError): score_human_trials([row])
        row['elapsed_ms']='2000'
        with self.assertRaises(VekaError): score_human_trials([row,row])
