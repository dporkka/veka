"""Noncanonical language transfer proposals and observational conversation benchmark."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.everyday import load_dialogues
from veka.language_transfer import (load_proposals, audit_proposals,
                                    read_conversation_trials, score_conversations,
                                    CONVERSATION_FIELDS)

ROOT = Path(__file__).resolve().parents[1]


class BorrowingProposalsTests(unittest.TestCase):
    def setUp(self):
        self.requirements = load_dialogues()
        self.doc = load_proposals(ROOT / 'data/language_transfer_v01.json')

    def test_catalog_has_precise_contrasts_without_promoting_syntax(self):
        result = audit_proposals(self.doc, self.requirements)
        self.assertGreaterEqual(result['proposals'], 6)
        self.assertEqual(result['canonical_changes'], 0)
        self.assertEqual(result['approved_proposals'], 0)
        self.assertFalse(result['human_benefit_established'])
        self.assertTrue(all(item['requires_human_validation'] for item in result['items']))
        self.assertIn('ED-083', next(r for r in result['items'] if r['id'] == 'evidence_source')['scenario_ids'])
        self.assertEqual(len(Lexicon.from_csv(ROOT / 'data/lexicon.csv')), 1025)

    def test_duplicate_unknown_scenario_and_fabricated_approval_fail(self):
        for mutate in ('duplicate', 'unknown', 'approval', 'invented_form'):
            with self.subTest(mutate=mutate):
                data = json.loads(json.dumps(self.doc))
                if mutate == 'duplicate':
                    data['proposals'][1]['id'] = data['proposals'][0]['id']
                if mutate == 'unknown':
                    data['proposals'][0]['scenario_ids'] = ['ED-999']
                if mutate == 'approval':
                    data['proposals'][0]['status'] = 'approved'
                if mutate == 'invented_form':
                    data['proposals'][0]['veka_word'] = 'fake'
                with self.assertRaises(VekaError):
                    audit_proposals(data, self.requirements)

    def test_empty_contrast_and_empty_source_rejected(self):
        for field in ('contrasts', 'source_languages'):
            data = json.loads(json.dumps(self.doc))
            data['proposals'][0][field] = []
            with self.subTest(field=field), self.assertRaises(VekaError):
                audit_proposals(data, self.requirements)


class ConversationBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.requirements = load_dialogues()

    def row(self, participant, language, correct=1, elapsed_ms='2000', **changes):
        row = dict(participant_id=participant, background_family='Austronesian',
                   scenario_id='ED-083', language=language, correct=str(correct),
                   elapsed_ms=str(elapsed_ms), repair_ms='0', critical_error='0')
        row.update(changes)
        return row

    def test_empty_template_never_claims_observed_data(self):
        data = read_conversation_trials(ROOT / 'data/conversation_trials_v01.csv')
        self.assertEqual(data, [])
        report = score_conversations(data, self.requirements)
        self.assertFalse(report['observed'])
        self.assertFalse(report['comparative_benefit_established'])
        self.assertEqual(report['balanced_scenario_family_cells'], 0)

    def test_descriptive_correct_per_minute_and_comparator_coverage(self):
        data = [
            self.row('P1', 'veka', 1, '2000', repair_ms='1000'),
            self.row('P2', 'globasa', 1, '2000'),
            self.row('P3', 'indonesian', 0, '1000', critical_error='1'),
        ]
        result = score_conversations(data, self.requirements)
        self.assertTrue(result['observed'])
        self.assertEqual(result['participants'], 3)
        self.assertEqual(result['by_language']['veka']['total_ms'], 3000)
        self.assertAlmostEqual(result['by_language']['veka']['correct_per_minute'], 20.0)
        self.assertEqual(result['by_language']['indonesian']['critical_errors'], 1)
        self.assertEqual(result['balanced_scenario_family_cells'], 1)
        self.assertFalse(result['comparative_benefit_established'])
        self.assertNotIn('winner', result)

    def test_invalid_rows_fail_closed(self):
        valid = self.row('P1', 'veka')
        bad = [
            {'language': 'unknown'}, {'elapsed_ms': '0'}, {'repair_ms': '-1'},
            {'correct': 'yes'}, {'critical_error': '1'},
            {'scenario_id': 'ED-999'}, {'background_family': ''},
            {'participant_id': 'P/1'}, {'background_family': '=SUM(1)'},
            {'elapsed_ms': '9' * 5000}, {'extra': 'untrusted'},
        ]
        for change in bad:
            with self.subTest(change=change), self.assertRaises(VekaError):
                score_conversations([dict(valid, **change)], self.requirements)
        with self.assertRaises(VekaError):
            score_conversations([valid, dict(valid, language='globasa')], self.requirements)
        with self.assertRaises(VekaError):
            score_conversations([valid, self.row('P1', 'indonesian', scenario_id='ED-081',
                                               background_family='Indo-European')], self.requirements)

    def test_strict_csv_rejects_extra_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.csv'
            path.write_text(','.join(CONVERSATION_FIELDS) + '\n' + ','.join(
                self.row('P1', 'veka')[k] for k in CONVERSATION_FIELDS) + ',EXTRA\n', encoding='utf-8')
            with self.assertRaises(VekaError):
                read_conversation_trials(path)

    def test_cli_json_and_empty_outcomes(self):
        for cmd in ('borrowing-audit', 'conversation-score'):
            with self.subTest(cmd=cmd):
                run = subprocess.run([sys.executable, '-m', 'veka', cmd],
                                     cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                report = json.loads(run.stdout)
                self.assertEqual(report['canonical_changes'], 0)
                self.assertFalse(report['human_benefit_established'])


if __name__ == '__main__':
    unittest.main()
