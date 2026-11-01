"""Seven-form familiarity pilot uses the same strictly blinded pipeline."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import audit_candidates, read_candidates
from veka.root_study import plan_root_cohorts
from veka.cohort_plan import write_cohort_plan
from veka.root_adjudication import build_root_review, score_root_review

ROOT = Path(__file__).resolve().parents[1]
FAMILIAR = ROOT / 'data/familiar_candidates_v14.csv'
EXPECTED = {
    'woi': 'mu-si-ka', 'vik': 'se-ko-la', 'sau': 'bu-ku',
    'noi': 'os-pi-tal', 'dik': 'ka-me-ra', 'hek': 'dok-ta',
    'ru': 'me-tal',
}


class FamiliarRootStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        cls.candidates = read_candidates(FAMILIAR)

    def roster(self):
        return [dict(participant_id=f'P{language}{n}', background_stratum=language)
                for language in ('English', 'Mandarin', 'Portuguese') for n in (1, 2)]

    def test_familiar_pilot_manifest_exact_snapshot_is_unverified(self):
        self.assertEqual({r['core_form']: r['candidate_form'] for r in self.candidates}, EXPECTED)
        self.assertEqual({r['status'] for r in self.candidates}, {'unverified_draft'})
        report = audit_candidates(self.candidates, self.lex)
        self.assertEqual(report['structurally_testable'], 7)
        self.assertEqual(report['rejected_forms'], 0)
        self.assertFalse(report['recognition_measured'])

    def test_odd_count_balances_each_item_with_opposite_arms(self):
        plan = plan_root_cohorts(self.candidates, self.lex, self.roster(), seed=24)
        self.assertEqual(plan['summary']['trials_per_participant'], 7)
        self.assertFalse(plan['summary']['human_data_collected'])
        by_slot = {}
        for row in plan['researcher_keys']:
            key = (row['background_stratum'], row['concept_id'])
            by_slot.setdefault(key, []).append(row['condition'])
        self.assertTrue(by_slot)
        self.assertEqual({tuple(sorted(v)) for v in by_slot.values()}, {('candidate', 'core')})
        for participant in plan['participants']:
            conditions = Counter(row['condition'] for row in plan['researcher_keys']
                                 if row['participant_id'] == participant)
            self.assertEqual(sorted(conditions.values()), [3, 4])
        self.assertEqual(plan, plan_root_cohorts(self.candidates, self.lex,
                                                 list(reversed(self.roster())), seed=24))

    def test_7_form_review_and_score_roundtrip_in_all_three_backgrounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = plan_root_cohorts(self.candidates, self.lex, self.roster(), seed=34)
            responses, secret = root / 'responses', root / 'researcher'
            write_cohort_plan(plan, responses, secret)
            for pid, rows in plan['participants'].items():
                for row in rows:
                    row['response_gloss'] = 'synthetic'
                    row['response_ms'] = '1400'
                    row['prior_exposure'] = 'unknown'
                with (responses / (pid + '.csv')).open('w', encoding='utf8', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=rows[0])
                    w.writeheader()
                    w.writerows(rows)
            review = build_root_review(plan['researcher_keys'], responses,
                                       self.candidates, self.lex)
            self.assertEqual(len(review), 42)
            assert all('condition' not in row for row in review)
            judged = [dict(row, reviewer_id='R2', correct='0', critical_error='0',
                           review_note='synthetic rubric') for row in review]
            results = score_root_review(plan['researcher_keys'], responses, judged,
                                        self.candidates, self.lex)
            self.assertEqual(results['total_trials'], 42)
            self.assertEqual(set(results['by_background']), {'English', 'Mandarin', 'Portuguese'})
            self.assertEqual(results['by_concept']['F007']['core']['trials'], 3)
            self.assertFalse(results['comparative_benefit_established'])
            self.assertFalse(results['adoption_authorized'])
            # CLI must use the same explicit candidate packet for both steps.
            roster_file = root / 'roster.csv'
            with roster_file.open('w', encoding='utf8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=('participant_id', 'background_stratum'))
                w.writeheader()
                w.writerows(self.roster())
            result = subprocess.run([sys.executable, '-m', 'veka', 'root-study-plan',
                  '--candidates', str(FAMILIAR), '--roster', str(roster_file),
                  '--participants-dir', str(root / 'new-responses'),
                  '--researcher-dir', str(root / 'new-key')], cwd=ROOT,
                  text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['trials_per_participant'], 7)
            judged_path = root / 'judged.csv'
            with judged_path.open('w', encoding='utf8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=judged[0])
                w.writeheader()
                w.writerows(judged)
            score_cmd = [sys.executable, '-m', 'veka', 'root-study-score',
                         '--key', str(secret / 'researcher-key.csv'),
                         '--responses-dir', str(responses), '--reviews', str(judged_path)]
            wrong = subprocess.run(score_cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(wrong.returncode, 0)
            correct = subprocess.run(score_cmd + ['--candidates', str(FAMILIAR)],
                                     cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(correct.returncode, 0, correct.stderr)
            self.assertEqual(json.loads(correct.stdout)['total_trials'], 42)
            review_cli = subprocess.run([sys.executable, '-m', 'veka', 'root-study-review',
                  '--candidates', str(FAMILIAR),
                  '--key', str(secret / 'researcher-key.csv'),
                  '--responses-dir', str(responses), '--output', str(root / 'manual-review.csv')],
                  cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(review_cli.returncode, 0, review_cli.stderr)

    def test_candidate_packet_changes_do_not_relabel_recorded_trials(self):
        plan = plan_root_cohorts(self.candidates, self.lex, self.roster())
        wrong = [dict(row) for row in self.candidates]
        wrong[0]['candidate_form'] = 'mu-si-ko'
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'study'
            private = Path(tmp) / 'key'
            write_cohort_plan(plan, original, private)
            # Even before observing human results, the key must be immutable
            # against changed candidate source forms.
            from veka.root_adjudication import _validated_keys
            with self.assertRaises(VekaError):
                _validated_keys(plan['researcher_keys'], wrong, self.lex)


if __name__ == '__main__':
    unittest.main()
