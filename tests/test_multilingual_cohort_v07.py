"""Regression tests for noncanonical six-language recognition cohorts."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.multilingual import LANGUAGE_GROUPS, make_cohort, score_cohort

ROOT = Path(__file__).resolve().parents[1]


class MultilingualCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexicon = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        cls.candidates = read_candidates(ROOT / 'data/international_candidates_v04.csv')

    def test_language_coverage_and_genealogical_family_labels(self):
        self.assertEqual(set(LANGUAGE_GROUPS), {'en', 'cmn', 'es', 'hi', 'pt', 'id'})
        self.assertEqual(LANGUAGE_GROUPS['en']['family'], LANGUAGE_GROUPS['hi']['family'])
        self.assertEqual(LANGUAGE_GROUPS['es']['family'], LANGUAGE_GROUPS['pt']['family'])
        self.assertNotEqual(LANGUAGE_GROUPS['id']['family'], LANGUAGE_GROUPS['cmn']['family'])

    def test_reproducible_blind_balanced_participant_and_concept_allocation(self):
        visible, key = make_cohort(self.candidates, self.lexicon, participants_per_language=4, seed=42)
        self.assertEqual((visible, key), make_cohort(self.candidates, self.lexicon, 4, 42))
        self.assertNotEqual((visible, key), make_cohort(self.candidates, self.lexicon, 4, 43))
        self.assertEqual(len(visible), 6 * 4 * 8)
        self.assertEqual(len(key), len(visible))
        self.assertEqual(len({row['trial_id'] for row in key}), len(key))
        self.assertTrue(all(not ({'condition', 'target_gloss', 'concept_id', 'family'} & row.keys()) for row in visible))
        self.assertTrue(all(row['response_gloss'] == '' for row in visible))
        self.assertTrue(all(row['status'] == 'unverified_draft' for row in key))
        by_participant = defaultdict(Counter)
        by_concept = defaultdict(Counter)
        for row in key:
            by_participant[row['participant_id']][row['condition']] += 1
            by_concept[(row['language'], row['concept_id'])][row['condition']] += 1
        self.assertEqual(len(by_participant), 24)
        self.assertTrue(all(c == {'core': 4, 'international': 4} for c in by_participant.values()))
        self.assertTrue(all(c == {'core': 2, 'international': 2} for c in by_concept.values()))

    def test_rejects_invalid_allocation_and_unusable_candidate_sets(self):
        for size in [0, 1, 3, 201, -2, True, '2']:
            with self.subTest(size=size), self.assertRaises(VekaError):
                make_cohort(self.candidates, self.lexicon, size)
        with self.assertRaises(VekaError):
            make_cohort(self.candidates[:1], self.lexicon, 2)
        with self.assertRaises(VekaError):
            make_cohort(self.candidates, self.lexicon, 2, seed='not a number')

    def test_per_language_scoring_is_descriptive_only(self):
        _, key = make_cohort(self.candidates, self.lexicon, 2, seed=4)
        fake = [dict(trial_id=row['trial_id'], correct='1' if row['condition'] == 'core' else '0',
                     response_ms='1200', repair_count='0') for row in key]
        report = score_cohort(key, fake)
        self.assertEqual(report['trials'], 96)
        self.assertEqual(set(report['languages']), set(LANGUAGE_GROUPS))
        for code, info in report['languages'].items():
            self.assertEqual(info['n'], 16)
            self.assertEqual(info['family'], LANGUAGE_GROUPS[code]['family'])
            self.assertEqual(info['conditions']['core']['accuracy'], 1.0)
            self.assertEqual(info['conditions']['international']['accuracy'], 0.0)
        self.assertFalse(report['causal_effect_established'])
        self.assertFalse(report['human_observations_independently_verified'])

    def test_score_rejects_incomplete_duplicate_or_unjudged_records_and_invalid_key(self):
        _, key = make_cohort(self.candidates, self.lexicon, 2, seed=4)
        fake = [dict(trial_id=row['trial_id'], correct='1',
                     response_ms='1200', repair_count='0') for row in key]
        with self.assertRaises(VekaError):
            score_cohort(key, fake[:-1])
        with self.assertRaises(VekaError):
            score_cohort(key, fake + [fake[0]])
        with self.assertRaises(VekaError):
            score_cohort(key, [dict(fake[0], correct=''), *fake[1:]])
        with self.assertRaises(VekaError):
            score_cohort([dict(key[0], language='xx'), *key[1:]], fake)
        with self.assertRaises(VekaError):
            score_cohort([dict(key[0], family='Indo-European'), *key[1:]] if key[0]['family'] != 'Indo-European'
                         else [dict(key[0], family='Wrong'), *key[1:]], fake)

    def test_score_rejects_tampered_design_and_malformed_csv_rows(self):
        _, key = make_cohort(self.candidates, self.lexicon, 2, seed=4)
        fake = [dict(trial_id=row['trial_id'], correct='1',
                     response_ms='1000', repair_count='0') for row in key]
        with self.assertRaises(VekaError):
            score_cohort([dict(key[0], condition='international' if key[0]['condition'] == 'core'
                               else 'core'), *key[1:]], fake)
        with self.assertRaises(VekaError):
            score_cohort([dict(key[0], trial_id=''), *key[1:]], fake)
        with self.assertRaises(VekaError):
            score_cohort(key, [dict(correct='1', response_ms='1000', repair_count='0'), *fake[1:]])

    def test_cli_writes_separate_artifacts_and_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            participant = Path(temp) / 'participant.csv'
            researcher = Path(temp) / 'key.csv'
            argv = [sys.executable, '-m', 'veka', 'international-cohort',
                    '--participants-per-language', '2', '--participant-csv', str(participant),
                    '--answer-key', str(researcher)]
            proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            summary = json.loads(proc.stdout)
            self.assertEqual(summary['participants'], 12)
            self.assertFalse(summary['human_data_collected'])
            with participant.open(newline='', encoding='utf-8') as f:
                visible = list(csv.DictReader(f))
            with researcher.open(newline='', encoding='utf-8') as f:
                key = list(csv.DictReader(f))
            self.assertEqual(len(key), 96)
            self.assertNotIn('condition', visible[0])
            self.assertEqual(subprocess.run(argv, cwd=ROOT, capture_output=True).returncode, 2)
            annotations = Path(temp) / 'annotation.csv'
            with annotations.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=('trial_id', 'correct', 'response_ms', 'repair_count'))
                writer.writeheader()
                writer.writerows({'trial_id': x['trial_id'], 'correct': '1', 'response_ms': '1000',
                                  'repair_count': '0'} for x in key)
            score = subprocess.run([sys.executable, '-m', 'veka', 'international-cohort-score',
                                    '--answer-key', str(researcher), '--annotated', str(annotations)],
                                   cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(score.returncode, 0, score.stderr)
            self.assertEqual(json.loads(score.stdout)['trials'], 96)


if __name__ == '__main__':
    unittest.main()
