"""Tests for opt-in, structurally scored spoken aesthetics (not listener evidence)."""
import contextlib
import io
import json
import unittest

from veka.aesthetics import score_form, rank_candidates, prosody_guidance
from veka.core import VekaError
from veka.profiles import load_profile


class SpokenAestheticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tonal = load_profile('tonal')
        cls.toneless = load_profile('toneless')

    def test_open_syllable_preferred_over_obstruent_final_with_same_onset(self):
        self.assertGreater(score_form('da')['score'], score_form('dak')['score'])

    def test_compatible_compound_is_scored_deterministically(self):
        a = score_form('ma-li')
        self.assertEqual(a, score_form('ma-li'))
        self.assertEqual(a['syllables'], 2)
        self.assertEqual(a['open_syllable_fraction'], 1.0)
        self.assertFalse(a['empirically_validated'])

    def test_preserves_accents_and_rejects_illegal_forms(self):
        self.assertEqual(score_form('pái')['form'], 'pái')
        for word in ['laa', 'bad!', 'mali', 'da--li', 'káks']:
            with self.subTest(word=word), self.assertRaises(VekaError):
                score_form(word)

    def test_ranking_marks_existing_forms_and_close_operators_as_unsafe(self):
        ranked = rank_candidates(['mi', 'ni', 'ma-li', 'pa'], self.tonal)
        by_form = {item['form']: item for item in ranked}
        self.assertEqual(set(by_form), {'mi', 'ni', 'ma-li', 'pa'})
        self.assertTrue(by_form['mi']['existing_headword'])
        self.assertFalse(by_form['mi']['eligible_new_word'])
        self.assertTrue(by_form['pa']['existing_headword'])
        self.assertFalse(by_form['pa']['eligible_new_word'])
        self.assertIn('critical_marker_distance', by_form['ma-li'])
        self.assertFalse(by_form['ma-li']['empirically_validated'])

    def test_hyphenated_candidates_require_spoken_segmentation_review(self):
        compound = rank_candidates(['ma-li'], self.tonal)[0]
        self.assertTrue(compound['requires_spoken_segmentation_review'])
        self.assertFalse(compound['eligible_new_word'])
        self.assertTrue(any('hyphen' in w for w in compound['screening_warnings']))

    def test_input_ranking_is_stable_and_does_not_change_lexicon(self):
        before = tuple(self.tonal)
        a = rank_candidates(['ma-li', 'ma', 'ma-li'], self.tonal)
        b = rank_candidates(['ma-li', 'ma'], self.tonal)
        self.assertEqual(a, b)
        self.assertEqual(tuple(self.tonal), before)

    def test_unparseable_clause_rejected_for_prosody(self):
        with self.assertRaises(VekaError):
            prosody_guidance('Mi pa ne.', self.tonal, profile='tonal')
        with self.assertRaises(VekaError):
            prosody_guidance('Mi fok mel.', self.tonal, profile='tonal')

    def test_tonal_prosody_protects_lexical_tone(self):
        result = prosody_guidance('Mi pái mel.', self.tonal, profile='tonal')
        self.assertTrue(result['preserve_lexical_tone'])
        self.assertEqual(result['cadence'], 'phrase-final soft fall subordinate to lexical tones')
        self.assertEqual(result['spoken_text'], 'Mi pái mel.')
        self.assertFalse(result['audio_generated'])
        self.assertFalse(result['empirically_validated'])

    def test_toneless_prosody_allows_phrasal_rise_and_fall(self):
        result = prosody_guidance('Mi fok mel.', self.toneless, profile='toneless')
        self.assertFalse(result['preserve_lexical_tone'])
        self.assertEqual(result['cadence'], 'gentle phrase-final fall')
        self.assertEqual(result['spoken_text'], 'Mi fok mel.')

    def test_command_line_score_and_prosody(self):
        from veka.__main__ import main
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(['aesthetics', 'ma-li', 'ma', '--profile', 'tonal'])
        self.assertEqual(code, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data['profile'], 'tonal')
        self.assertEqual(len(data['ranked_candidates']), 2)
        self.assertFalse(data['audio_generated'])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(['prosody', 'Mi pa dak mel.', '--profile', 'tonal'])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())['preserve_lexical_tone'])


if __name__ == '__main__':
    unittest.main()
