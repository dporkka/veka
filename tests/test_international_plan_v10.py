"""Tests for the noncanonical international-root research planning profile."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.international_plan import build_international_plan, read_review_priorities

ROOT = Path(__file__).resolve().parents[1]


class InternationalPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        cls.rows = read_candidates(ROOT / 'data/international_candidates_v10.csv')
        cls.priorities = read_review_priorities(ROOT / 'data/international_priorities_v10.csv')

    def test_queue_coverage_is_complete_and_noncanonical(self):
        legacy = read_candidates(ROOT / 'data/international_candidates_v04.csv')
        self.assertEqual(len(self.rows), 100)
        self.assertEqual([(r['concept_id'], r['core_form'], r['gloss']) for r in self.rows],
                         [(r['concept_id'], r['core_form'], r['gloss']) for r in legacy])
        self.assertGreaterEqual(sum(bool(r['candidate_form']) for r in self.rows), 20)
        report = build_international_plan(self.rows, self.lex, self.priorities, [])
        self.assertEqual(report['concept_count'], 100)
        self.assertEqual(report['canonical_changes'], 0)
        self.assertFalse(report['adoption_authorized'])
        self.assertEqual(report['rejected_drafts'], 0)
        self.assertEqual(len(report['queue']), 100)
        self.assertEqual(len(self.lex), 1025)
        self.assertEqual(sum(e.kind == 'compound' for e in self.lex.values()), 708)

    def test_priority_is_editorial_and_compound_migration_is_explicit(self):
        report = build_international_plan(self.rows, self.lex, self.priorities, [])
        queue = report['queue']
        self.assertEqual(queue, sorted(queue, key=lambda r: (-r['review_priority'], r['concept_id'])))
        school = next(r for r in queue if r['gloss'] == 'school')
        self.assertEqual(school['candidate_form'], 'se-ko-la')
        self.assertGreater(school['existing_compounds_affected'], 0)
        self.assertEqual(school['next_action'], 'verify_cross_family_attestations')
        self.assertFalse(school['recognition_measured'])
        self.assertTrue(school['false_friend_review_required'])
        self.assertIsNone(school['predicted_comprehension_rate'])

    def test_reject_missing_or_invalid_review_priorities(self):
        with self.assertRaises(VekaError):
            build_international_plan(self.rows, self.lex, self.priorities[:-1], [])
        wrong = [dict(r) for r in self.priorities]
        wrong[0]['exposure_tier'] = '100'
        with self.assertRaises(VekaError):
            build_international_plan(self.rows, self.lex, wrong, [])
        duplicate = [dict(r) for r in self.priorities]
        duplicate[-1]['concept_id'] = duplicate[0]['concept_id']
        with self.assertRaises(VekaError):
            build_international_plan(self.rows, self.lex, duplicate, [])

    def test_spoken_surface_collisions_block_promotion_even_if_spellings_differ(self):
        rows = [dict(r) for r in self.rows]
        rows[0].update(candidate_form='a-nis', status='unverified_draft')
        rows[1].update(candidate_form='an-is', status='unverified_draft')
        report = build_international_plan(rows, self.lex, self.priorities, [])
        selected = {r['concept_id']: r for r in report['queue']}
        self.assertEqual(selected[rows[0]['concept_id']]['next_action'],
                         'repair_spoken_surface_collision')
        self.assertIn('an-is', selected[rows[0]['concept_id']]['spoken_surface_collisions'])
        self.assertIn('a-nis', selected[rows[1]['concept_id']]['spoken_surface_collisions'])
        self.assertFalse(report['adoption_authorized'])

    def test_cli_plan_is_valid_json_and_not_canonical_lexicon(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'plan.json'
            cmd = [sys.executable, '-m', 'veka', 'international-plan', '--output', str(output)]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['schema_version'], 'veka.international-plan.v10')
            self.assertFalse(report['human_benefit_established'])
            self.assertEqual(report['canonical_changes'], 0)
