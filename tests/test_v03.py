"""Veka 0.3 feature specifications. Run these first (RED)."""
import csv
import json
import unittest
import itertools
from pathlib import Path

from veka.core import Lexicon, Discourse, VekaError, parse, validate_word, CONSONANTS, VOWELS, DIPHTHONGS
from veka.numbers import spell_number, read_number
from veka.logic import parse_logic, evaluate_logic
from veka.phonology import analyze_root_confusions, evaluate_numeric_distances
from veka.study import generate_assignments, validate_assignments, generate_abx_assignments

ROOT = Path(__file__).resolve().parents[1]


class BackwardsCompatibilityAndCapacity(unittest.TestCase):
    def test_all_v02_entries_remain_byte_level_semantically_identical(self):
        with (ROOT/'data/legacy_lexicon_v02.csv').open(encoding='utf8') as stream:
            old=list(csv.DictReader(stream))
        with (ROOT/'data/lexicon.csv').open(encoding='utf8') as stream:
            new=list(csv.DictReader(stream))
        self.assertEqual(len(old),1000)
        self.assertEqual(new[:len(old)],old)
        self.assertEqual(len(new),1025)

    def test_theoretical_syllable_inventory_exactly_932(self):
        accents=dict(zip('aeiou','áéíóú'))
        forms=set()
        for onset,nucleus,coda,tone in itertools.product(['']+list(CONSONANTS),
                list(VOWELS)+list(DIPHTHONGS),('','n','l','s','k'),(0,1)):
            center=(accents[nucleus[0]]+nucleus[1:] if tone else nucleus)
            form=onset+center+coda
            if validate_word(form):forms.add(form)
        self.assertEqual(len(forms),932)
        self.assertEqual(sum(not any(ch in x for ch in 'áéíóú') for x in forms),556)


class NumberTests(unittest.TestCase):
    def test_decimal_roundtrips_and_scale_is_retained(self):
        for value in ('0', '1', '120', '101', '120.05', '0.001', '-14.50', '999999'):
            self.assertEqual(read_number(spell_number(value)), value)

    def test_incorrect_or_ambiguous_numbers_fail_closed(self):
        for value in ('00', '01', '-0', '-0.00', '1.', '.5', '1e3', 'NaN', 'Infinity', '2,500'):
            with self.subTest(value=value), self.assertRaises(VekaError):
                spell_number(value)
        for encoded in ('wen', 'wen dis', 'wen nul ran', 'wen sin nul', 'wen ran dis',
                        'wen ran dis nul sin', 'wen ran ran ran xxx'):
            with self.subTest(encoded=encoded), self.assertRaises(VekaError):
                read_number(encoded)

    def test_each_numeric_digit_is_distinct_from_grammar_particles(self):
        lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        evaluation = evaluate_numeric_distances(lex)
        self.assertEqual(evaluation['count'], 10)
        self.assertGreaterEqual(evaluation['minimum_digit_distance'], 2)
        self.assertGreaterEqual(evaluation['minimum_operator_distance'], 2)


class LogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')

    def test_exact_count_in_noun_phrase(self):
        ast = parse('Mi lin ren wen kuk.', self.lex)
        self.assertEqual(ast['object_quantity'], '2')
        self.assertEqual(ast['object'], 'ren wen kuk')
        ast = parse('Ren wen nul pa gos.', self.lex)
        self.assertEqual(ast['subject_quantity'], '0')

    def test_unit_bearing_exact_decimal_measurement(self):
        ast = parse('Mi rin sil wen ran dis gel su wok.', self.lex)
        self.assertEqual(ast['object_quantity'], '1.5')
        self.assertEqual(ast['object_unit'], 'wok')
        with self.assertRaises(VekaError):
            parse('Mi rin sil wen ran su ti.', self.lex)

    def test_possessors_do_not_steal_head_quantity_and_invalid_unit_fails_gracefully(self):
        ast = parse('Ren de ren wen kuk pa gos.', self.lex)
        self.assertIsNone(ast['subject_quantity'])
        with self.assertRaises(VekaError):
            parse('Mi rin sil wen ran su Blorp.', self.lex)

    def test_logic_has_correct_truth_tables(self):
        ast = parse_logic('Fi mi gos ve ti gos yu.', self.lex)
        self.assertFalse(evaluate_logic(ast, {'mi gos':True, 'ti gos':False}))
        self.assertTrue(evaluate_logic(ast, {'mi gos':False, 'ti gos':False}))
        disjunction = parse_logic('Oi mi gos ve ti gos yu.', self.lex)
        self.assertTrue(evaluate_logic(disjunction, {'mi gos':True, 'ti gos':True}))
        with self.assertRaises(VekaError):
            evaluate_logic(ast, {'mi gos':True})

    def test_quantifiers_have_local_scope_and_unsupported_double_scope_fails(self):
        ast = parse('Al ren pa gos.', self.lex)
        self.assertEqual(ast['subject_quantifier'], 'every')
        ast = parse('Kis ren pa gos.', self.lex)
        self.assertEqual(ast['subject_quantifier'], 'some')
        with self.assertRaises(VekaError):
            parse('Al ren lin kis ren.', self.lex)
        with self.assertRaises(VekaError):
            parse('Al ren wen kuk gos.', self.lex)

    def test_explicit_bracketing_makes_negation_scope_visible(self):
        outer = parse_logic('Na zi mi gos ve ti gos yu yu.', self.lex)
        inner = parse_logic('Zi na mi gos yu ve ti gos yu.', self.lex)
        self.assertEqual(outer['op'], 'not')
        self.assertEqual(outer['argument']['op'], 'and')
        self.assertEqual(inner['op'], 'and')
        self.assertEqual(inner['left']['op'], 'not')
        self.assertNotEqual(outer, inner)

    def test_conditional_is_one_way_and_or_is_inclusive(self):
        ast = parse_logic('Fi mi dak mel ve ti ton mel yu.', self.lex)
        self.assertEqual(ast['op'], 'if')
        self.assertEqual(ast['left']['clause']['predicate'], 'dak')
        self.assertEqual(ast['right']['clause']['predicate'], 'ton')
        ast = parse_logic('Oi mi gos ve ti gos yu.', self.lex)
        self.assertEqual(ast['op'], 'or_inclusive')

    def test_truth_operators_reject_questions_and_commands(self):
        with self.assertRaises(VekaError):
            parse_logic('Zi mi gos ke ve ti gos yu.', self.lex)
        with self.assertRaises(VekaError):
            parse_logic('Fi ha gos ve mi gos yu.', self.lex)

    def test_unbalanced_or_unmarked_logic_is_rejected(self):
        for sentence in ('Zi mi gos ti gos yu.', 'Zi mi gos ve ti gos.',
                         'Na mi gos.', 'Mi gos oi ti gos.', 'Zi mi gos ve ti gos yu yu.',
                         'Zi mi gos ve yu', 'Fi mi gos ve ti gos yu ve mi gos'):
            with self.subTest(sentence=sentence), self.assertRaises(VekaError):
                parse_logic(sentence, self.lex)

    def test_nested_expressions_cannot_recursively_exhaust_parser(self):
        with self.assertRaises(VekaError):
            parse_logic('Na ' * 25 + 'mi gos ' + 'yu ' * 25, self.lex)


class StudyTests(unittest.TestCase):
    def test_assignments_are_reproducible_and_counterbalanced(self):
        trials = json.loads((ROOT / 'data/study_items_v03.json').read_text())
        a = generate_assignments(trials, participant_id='p1', seed=7)
        b = generate_assignments(trials, participant_id='p1', seed=7)
        c = generate_assignments(trials, participant_id='p2', seed=7)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        validate_assignments(a)
        validate_assignments(c)
        self.assertGreaterEqual(len(a), 12)
        self.assertEqual(len({r['item_id'] for r in a}), len(a))

    def test_abx_manifests_balance_targets_with_no_fake_audio(self):
        pairs = json.loads((ROOT / 'data/phonology_abx_pairs.json').read_text())
        trials=generate_abx_assignments(pairs,'p012',seed=42)
        self.assertEqual(len(trials),4*len(pairs))
        self.assertEqual(sum(r['correct_option']=='A' for r in trials),len(trials)//2)
        self.assertTrue(all(r['audio_recorded'] is False for r in trials))
        self.assertTrue(any(r['contrast']=='tone' for r in trials))

    def test_confusion_audit_reports_tonal_minimal_pair_but_not_acoustic_validation(self):
        lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        result = analyze_root_confusions(lex)
        self.assertTrue(any(x['forms'] == ['pal','pál'] for x in result['minimal_pairs']))
        self.assertFalse(result['empirically_validated'])


if __name__ == '__main__':
    unittest.main()
