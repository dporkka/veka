"""Independent semantic judgment bridge for Veka's blinded root study."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.root_study import plan_root_cohorts
from veka.cohort_plan import write_cohort_plan
from veka.root_adjudication import (build_root_review, read_root_review,
                                    score_root_review, write_root_review)

ROOT = Path(__file__).resolve().parents[1]
KEY_FIELDS = ('participant_id', 'trial_id', 'concept_id', 'target_gloss',
              'condition', 'presented_form', 'background_stratum')
REVIEW_FIELDS = ('participant_id', 'trial_id', 'target_gloss', 'response_gloss',
                 'correct', 'critical_error', 'reviewer_id', 'review_note')


class RootAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        cls.candidates = read_candidates(ROOT / 'data/international_candidates_v04.csv')

    def make_study(self, tmp):
        roster = [dict(participant_id=f'{language}{i}', background_stratum=language)
                  for language in ('English', 'Mandarin') for i in (1, 2)]
        plan = plan_root_cohorts(self.candidates, self.lex, roster, seed=91)
        base = Path(tmp)
        participants = base / 'participants'
        researcher = base / 'researcher'
        write_cohort_plan(plan, participants, researcher)
        for pid, rows in plan['participants'].items():
            for row in rows:
                row['response_gloss'] = 'unverified answer'
                row['response_ms'] = '1200'
                row['prior_exposure'] = 'no'
            with (participants / f'{pid}.csv').open('w', newline='', encoding='utf8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0])
                writer.writeheader()
                writer.writerows(rows)
        return plan, participants, researcher

    def approved(self, review):
        return [dict(r, correct='1', critical_error='0',
                     reviewer_id='RaterA', review_note='manually judged sense') for r in review]

    def test_review_sheet_blinds_form_condition_and_background(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, participants, _ = self.make_study(tmp)
            packet = build_root_review(plan['researcher_keys'], participants, self.candidates, self.lex)
            self.assertEqual(len(packet), 32)
            self.assertEqual(tuple(packet[0]), REVIEW_FIELDS)
            self.assertEqual({r['correct'] for r in packet}, {''})
            self.assertNotIn('candidate', str(packet))
            self.assertNotIn('background_stratum', str(packet))
            output = Path(tmp) / 'private-review.csv'
            write_root_review(packet, output)
            self.assertEqual(read_root_review(output), packet)
            with self.assertRaises(VekaError):
                write_root_review(packet, output)

    def test_exact_keyed_report_only_descriptive_by_background(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, participants, _ = self.make_study(tmp)
            review = build_root_review(plan['researcher_keys'], participants, self.candidates, self.lex)
            result = score_root_review(plan['researcher_keys'], participants,
                                       self.approved(review), self.candidates, self.lex)
            self.assertEqual(result['total_trials'], 32)
            self.assertEqual(result['participants'], 4)
            self.assertEqual(result['by_background']['English']['candidate']['trials'], 8)
            self.assertEqual(result['by_concept_and_background']['C002']['English']['core']['trials'], 1)
            self.assertEqual(result['by_concept_and_background']['C002']['Mandarin']['candidate']['trials'], 1)
            self.assertEqual(result['by_background']['Mandarin']['core']['trials'], 8)
            self.assertEqual(result['by_condition']['candidate']['accuracy'], 1.0)
            self.assertFalse(result['adoption_authorized'])
            self.assertFalse(result['comparative_benefit_established'])
            self.assertFalse(result['independent_human_data_verified'])
            self.assertNotIn('English1', json.dumps(result))
            self.assertNotIn('unverified answer', json.dumps(result))

    def test_tampering_missing_duplicates_and_conflicts_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, participants, _ = self.make_study(tmp)
            review = build_root_review(plan['researcher_keys'], participants, self.candidates, self.lex)
            good = self.approved(review)
            bads = (good[:-1], good + [good[0]],
                    [dict(good[0], target_gloss='wrong')] + good[1:],
                    [dict(good[0], response_gloss='altered')] + good[1:],
                    [dict(good[0], correct='1', critical_error='1')] + good[1:],
                    [dict(good[0], correct='', critical_error='0')] + good[1:],
                    [dict(good[0], reviewer_id='')] + good[1:])
            for bad in bads:
                with self.subTest(bad=bad[:1]), self.assertRaises(VekaError):
                    score_root_review(plan['researcher_keys'], participants, bad,
                                      self.candidates, self.lex)

    def test_incomplete_or_mismatched_participant_response_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, participants, _ = self.make_study(tmp)
            pid = next(iter(plan['participants']))
            path = participants / f'{pid}.csv'
            with path.open(encoding='utf8') as stream:
                rows = list(csv.DictReader(stream))
            for key, value in (('response_gloss', ''), ('response_ms', '0'),
                               ('presented_form', 'fake'), ('prior_exposure', 'possibly'),
                               ('response_gloss', '=HYPERLINK(\"https://example.com\")'),
                               ('response_gloss', 'one' + chr(10) + 'more')):
                changed = [dict(r) for r in rows]
                changed[0][key] = value
                with path.open('w', newline='', encoding='utf8') as f:
                    w = csv.DictWriter(f, fieldnames=rows[0])
                    w.writeheader()
                    w.writerows(changed)
                with self.subTest(key=key), self.assertRaises(VekaError):
                    build_root_review(plan['researcher_keys'], participants, self.candidates, self.lex)
            with path.open('w', newline='', encoding='utf8') as f:
                w = csv.DictWriter(f, fieldnames=rows[0])
                w.writeheader()
                w.writerows(rows)

    def test_cli_exports_private_review_then_scores_claimed_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan, participants, researcher = self.make_study(tmp)
            review_path = Path(tmp) / 'review.csv'
            args = [sys.executable, '-m', 'veka', 'root-study-review',
                    '--key', str(researcher / 'researcher-key.csv'),
                    '--responses-dir', str(participants),
                    '--output', str(review_path)]
            first = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(first.stdout)['trials'], 32)
            rows = read_root_review(review_path)
            with review_path.open('w', newline='', encoding='utf8') as f:
                w = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
                w.writeheader()
                w.writerows(self.approved(rows))
            second = subprocess.run([sys.executable, '-m', 'veka', 'root-study-score',
                '--key', str(researcher / 'researcher-key.csv'),
                '--responses-dir', str(participants), '--reviews', str(review_path)],
                cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)['total_trials'], 32)


if __name__ == '__main__':
    unittest.main()
