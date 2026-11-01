"""Veka 0.5 experiments: deliberately RED before implementation."""
import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Entry, Lexicon, VekaError, parse, validate_word
from veka.profiles import load_profile
from veka.phonology import edit_distance, CRITICAL_OPERATORS
from veka.experimental_v05 import (
    DERIVATIONS, CORRELATIVE_SERIES, CORRELATIVE_DIMENSIONS,
    derive, parse_derivative, experimental_lexicon, correlative,
    audit_experimental_v05,
)

ROOT = Path(__file__).resolve().parents[1]


class ExperimentalMorphologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = Lexicon.from_csv(ROOT / 'data/lexicon.csv')

    def test_six_typed_operations_have_noncanonical_markers(self):
        self.assertEqual(set(DERIVATIONS), {
            'agent', 'patient', 'instrument', 'place', 'repeat', 'passive_able'
        })
        seen = set()
        for rule in DERIVATIONS.values():
            self.assertTrue(validate_word(rule.marker))
            self.assertNotIn(rule.marker, self.core)
            self.assertNotIn(rule.marker, seen)
            seen.add(rule.marker)

    def test_markers_are_structurally_distinct_from_critical_particles(self):
        markers = [r.marker for r in DERIVATIONS.values()]
        self.assertTrue(all(edit_distance(m, p) >= 2
                            for m in markers for p in CRITICAL_OPERATORS))
        self.assertTrue(all(edit_distance(a, b) >= 2
                            for i, a in enumerate(markers) for b in markers[i+1:]))

    def test_all_profile_combinations_keep_canonical_parser_untouched(self):
        tonal = load_profile('tonal')
        toneless = load_profile('toneless')
        self.assertEqual(len(experimental_lexicon(tonal)) - len(tonal), 356)
        self.assertEqual(len(experimental_lexicon(toneless)) - len(toneless), 356)
        self.assertEqual(parse('Mi fok-koin mel.', experimental_lexicon(toneless), strict=True)['predicate'], 'fok-koin')
        with self.assertRaises(VekaError):
            parse('Mi fok-koin mel.', experimental_lexicon(tonal), strict=True)
        with self.assertRaises(VekaError):
            parse('Mi fok-koin mel.', toneless, strict=True)

    def test_opt_in_agent_noun_and_ability_adjective_are_compositional(self):
        lex = experimental_lexicon(self.core)
        self.assertEqual(parse('Dak-rik gos.', lex, strict=True)['subject'], 'dak-rik')
        self.assertEqual(parse('Mel es dak-vau.', lex, strict=True)['predicate'], 'dak-vau')
        with self.assertRaises(VekaError):
            parse('Dak-rik gos.', self.core, strict=True)

    def test_agent_and_patient_have_distinct_semantics(self):
        agent = derive('dak', 'agent', self.core)
        patient = derive('dak', 'patient', self.core)
        self.assertNotEqual(agent.form, patient.form)
        self.assertEqual((agent.pos, agent.role, agent.source_valency),
                         ('noun', 'agent', 'transitive'))
        self.assertEqual((patient.pos, patient.role), ('noun', 'patient'))
        self.assertEqual(parse_derivative(agent.form, self.core), agent)
        self.assertEqual(parse_derivative(patient.form, self.core), patient)

    def test_repeat_preserves_verb_valency_and_is_opt_in_to_parser(self):
        word = derive('dak', 'repeat', self.core)
        self.assertEqual((word.pos, word.valency), ('verb', 'transitive'))
        with self.assertRaises(VekaError):
            parse(f'Mi pa {word.form} mel.', self.core)
        expanded = experimental_lexicon(self.core)
        ast = parse(f'Mi pa {word.form} mel.', expanded, strict=True)
        self.assertEqual(ast['predicate'], word.form)
        self.assertEqual(ast['object'], 'mel')
        self.assertEqual(len(self.core), 1025)
        self.assertNotIn(word.form, self.core)

    def test_intransitive_repetition_retains_valency(self):
        word = derive('gos', 'repeat', self.core)
        self.assertEqual(word.valency, 'intransitive')
        ast = parse(f'Mi {word.form}.', experimental_lexicon(self.core), strict=True)
        self.assertEqual(ast['predicate'], word.form)
        with self.assertRaises(VekaError):
            parse(f'Mi {word.form} mel.', experimental_lexicon(self.core), strict=True)

    def test_rejects_unlicensed_role_changes_and_compound_derivation(self):
        with self.assertRaises(VekaError):
            derive('gos', 'patient', self.core)
        with self.assertRaises(VekaError):
            derive('gos', 'passive_able', self.core)
        with self.assertRaises(VekaError):
            derive('ren', 'agent', self.core)
        with self.assertRaises(VekaError):
            derive('dak', 'unknown', self.core)
        with self.assertRaises(VekaError):
            derive('ren-fas', 'agent', self.core)
        with self.assertRaises(VekaError):
            parse_derivative('dak-rik-koin', self.core)

    def test_collision_guards_refuse_shadowed_marker_and_existing_derivative(self):
        known = derive('dak', 'agent', self.core)
        marker_collision = Lexicon(self.core)
        marker_collision[known.marker] = Entry(
            known.marker, 'hypothetical root', 'noun', 'root', '', '', '', '')
        with self.assertRaises(VekaError):
            experimental_lexicon(marker_collision)
        derived_collision = Lexicon(self.core)
        derived_collision[known.form] = Entry(
            known.form, 'conflicting word', 'noun', 'compound', '', 'dak', known.marker, '')
        with self.assertRaises(VekaError):
            experimental_lexicon(derived_collision)

    def test_every_licensed_word_roundtrips_and_cannot_shadow_canonical_words(self):
        expanded = experimental_lexicon(self.core)
        generated = set(expanded) - set(self.core)
        self.assertGreater(len(generated), 200)
        self.assertTrue(all(validate_word(form) for form in generated))
        self.assertEqual(len(generated), len(expanded) - len(self.core))
        for form in generated:
            result = parse_derivative(form, self.core)
            self.assertEqual(result.form, form)
            self.assertEqual(expanded[form].pos, result.pos)

    def test_audit_reports_machine_only_evidence(self):
        report = audit_experimental_v05(self.core)
        self.assertEqual(report['canonical_entries'], 1025)
        self.assertEqual(report['derivational_collisions'], 0)
        self.assertFalse(report['human_validated'])
        self.assertFalse(report['canonical_adopted'])


class CorrelativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')

    def test_matrix_is_total_and_semantically_deterministic(self):
        self.assertEqual(set(CORRELATIVE_SERIES), {
            'question', 'this', 'that', 'some', 'every', 'none'
        })
        self.assertEqual(set(CORRELATIVE_DIMENSIONS), {'person', 'thing', 'place', 'time'})
        keys = set()
        for s in CORRELATIVE_SERIES:
            for d in CORRELATIVE_DIMENSIONS:
                item = correlative(s, d, self.lex)
                self.assertEqual((item['series'], item['dimension']), (s, d))
                self.assertNotIn(item['semantic_id'], keys)
                keys.add(item['semantic_id'])
        self.assertEqual(len(keys), 24)

    def test_existing_quantifiers_are_reused_not_remapped(self):
        self.assertEqual(correlative('some', 'person', self.lex)['surface'], 'kis ren')
        self.assertEqual(correlative('every', 'person', self.lex)['surface'], 'al ren')
        self.assertEqual(correlative('every', 'time', self.lex)['surface'], 'al nus')
        self.assertEqual(parse('Kis ren gos.', self.lex)['subject_quantifier'], 'some')

    def test_no_unapproved_forms_for_unimplemented_semantics(self):
        self.assertIsNone(correlative('question', 'place', self.lex)['surface'])
        self.assertIsNone(correlative('none', 'person', self.lex)['surface'])
        self.assertIsNone(correlative('this', 'thing', self.lex)['surface'])
        with self.assertRaises(VekaError):
            correlative('all', 'person', self.lex)
        with self.assertRaises(VekaError):
            correlative('every', 'universe', self.lex)

    def test_cli_exposes_experiments_without_changing_default_parse(self):
        cmd = [sys.executable, '-m', 'veka']
        good = subprocess.run(cmd + ['experimental-derive', 'dak', 'repeat'],
                              cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        form = json.loads(good.stdout)['form']
        default = subprocess.run(cmd + ['parse', f'Mi {form} mel.'],
                                 cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(default.returncode, 2)
        opt = subprocess.run(cmd + ['parse', f'Mi {form} mel.', '--experimental-v05', '--strict'],
                             cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(opt.returncode, 0, opt.stderr)
        self.assertEqual(json.loads(opt.stdout)['predicate'], form)


if __name__ == '__main__':
    unittest.main()
