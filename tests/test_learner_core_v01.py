"""Contracts for evidence-bounded learner vocabulary and compound classification."""
import json
import subprocess
import sys
import unittest

from veka.core import VekaError
from veka.everyday import load_lessons
from veka.lessons import LESSONS
from veka.profiles import load_profile
from veka.learner_core import audit_learner_core


class LearnerCoreTests(unittest.TestCase):
    def test_default_sources_count_once_and_never_fake_real_usage_frequency(self):
        result = audit_learner_core(budget=12)
        self.assertEqual(result['schema_version'], 'veka.learner-core.v01')
        self.assertEqual(result['corpus']['source_examples'],
                         sum(len(level['examples']) for level in load_lessons()) + len(LESSONS))
        self.assertLess(result['corpus']['unique_sentences'], result['corpus']['source_examples'])
        self.assertEqual(result['corpus']['deduped_examples'],
                         result['corpus']['source_examples'] - result['corpus']['unique_sentences'])
        self.assertEqual(result['corpus']['type'], 'curated_editorial_lessons_not_usage_sample')
        self.assertFalse(result['natural_language_frequency_measured'])
        self.assertFalse(result['human_comprehension_validated'])
        self.assertFalse(result['canonical_lexicon_modified'])
        self.assertEqual(result['lexicon']['root_count'], 317)
        self.assertEqual(result['lexicon']['transparent_compound_count'], 708)
        self.assertEqual(result['lexicon']['total_headwords'], 1025)

    def test_transparent_compound_is_decomposed_not_memorized_as_atomic_root(self):
        result = audit_learner_core(budget=317)
        self.assertIn('ren-sak', [c['form'] for c in result['compounds_observed']])
        self.assertNotIn('ren-sak', [row['form'] for row in result['root_inventory']])
        self.assertIn('ren', [row['form'] for row in result['root_inventory']])
        self.assertIn('sak', [row['form'] for row in result['root_inventory']])
        self.assertEqual(result['lexicon']['compound_memorization_policy'],
                         'transparent_composition_not_additional_atomic_roots')
        self.assertEqual(result['coverage']['fully_lexically_covered_sentences'],
                         result['corpus']['unique_sentences'])

    def test_budget_means_stable_priority_not_speech_performance(self):
        first = audit_learner_core(budget=9)
        second = audit_learner_core(budget=9)
        self.assertEqual(first, second)
        self.assertEqual(len(first['selected_roots']), 9)
        self.assertEqual(first['coverage']['budget'], 9)
        self.assertLess(first['coverage']['fully_lexically_covered_sentences'],
                        first['corpus']['unique_sentences'])
        self.assertEqual(len({root['form'] for root in first['selected_roots']}), 9)
        self.assertTrue(all(root['kind'] == 'root' for root in first['selected_roots']))
        self.assertGreater(first['root_inventory'][0]['sentence_occurrences'], 0)

    def test_critical_contrasts_are_screening_gaps_not_observed_confusions(self):
        result = audit_learner_core(budget=12)
        pairs = {tuple(row['forms']): row for row in result['critical_contrasts']}
        self.assertEqual(set(pairs), {('mi', 'ti'), ('ne', 'na'), ('ran', 'ren')})
        self.assertIn('na', pairs[('ne', 'na')]['not_seen_in_curriculum'])
        self.assertFalse(pairs[('ne', 'na')]['acoustic_confusion_measured'])
        self.assertEqual(pairs[('mi', 'ti')]['not_seen_in_curriculum'], [])

    def test_bounded_canonical_example_override_rejects_unknown_and_experimental_forms(self):
        lex = load_profile('tonal')
        single = audit_learner_core(budget=1, sentences=['Mi gos.'], lex=lex)
        self.assertEqual(single['coverage']['fully_lexically_covered_sentences'], 0)
        self.assertEqual(single['corpus']['unique_sentences'], 1)
        self.assertEqual(single['corpus']['type'], 'supplied_canonical_examples_not_usage_sample')
        with self.assertRaises(VekaError):
            audit_learner_core(budget=10, sentences=['Mi xyz.'], lex=lex)
        with self.assertRaises(VekaError):
            audit_learner_core(budget=10, sentences=['Mi fok mel.'], lex=lex)
        with self.assertRaises(VekaError):
            audit_learner_core(budget=10, sentences=['Mi gos.', 'Mi gos.'], lex=lex)

    def test_invalid_budgets_and_malformed_corpus_fail_closed(self):
        for bad in (0, -1, 318, True, 1.5, '10'):
            with self.subTest(bad=bad), self.assertRaises(VekaError):
                audit_learner_core(budget=bad)
        for bad in ([], [''], [7], ['Mi gos!', 'Mi gos!']):
            with self.subTest(bad=bad), self.assertRaises(VekaError):
                audit_learner_core(budget=10, sentences=bad)

    def test_researcher_can_audit_new_canonical_examples_from_strict_csv(self):
        import csv
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from veka.learner_core import load_learner_examples_csv

        with TemporaryDirectory() as folder:
            path = Path(folder) / 'curriculum.csv'
            with path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['sentence'])
                writer.writerow(['Mi gos.'])
                writer.writerow(['Ti gos.'])
            rows = load_learner_examples_csv(path)
            self.assertEqual(rows, ['Mi gos.', 'Ti gos.'])
            report = audit_learner_core(sentences=rows, budget=2)
            self.assertEqual(report['corpus']['unique_sentences'], 2)
            proc = subprocess.run([sys.executable, '-m', 'veka', 'learner-core',
                                   '--sentences-csv', str(path), '--budget', '2'],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['corpus']['type'],
                             'supplied_canonical_examples_not_usage_sample')
            path.write_text('sentence,target_meaning\nMi gos.,secret\n', encoding='utf-8')
            with self.assertRaises(VekaError):
                load_learner_examples_csv(path)
            path.write_text('sentence\nMi xyz.\n', encoding='utf-8')
            with self.assertRaises(VekaError):
                audit_learner_core(sentences=load_learner_examples_csv(path))
            path.write_text('sentence\nMi gos.\nMi gos.\n', encoding='utf-8')
            with self.assertRaises(VekaError):
                audit_learner_core(sentences=load_learner_examples_csv(path))

    def test_cli_is_json_and_rejects_out_of_range_budget(self):
        proc = subprocess.run([sys.executable, '-m', 'veka', 'learner-core', '--budget', '10'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(len(report['selected_roots']), 10)
        self.assertFalse(report['natural_language_frequency_measured'])
        proc = subprocess.run([sys.executable, '-m', 'veka', 'learner-core', '--budget', '0'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)
        self.assertIn('VEKA ERROR:', proc.stderr)


if __name__ == '__main__':
    unittest.main()
