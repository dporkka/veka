"""Study design contracts: no synthetic human measurements or key leakage."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.cohort_plan import read_cohort_roster, plan_cognate_cohorts, write_cohort_plan
from veka.cognates import read_pilot
from veka.core import Lexicon, VekaError

ROOT = Path(__file__).resolve().parents[1]


class CohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / 'data/lexicon.csv')
        cls.candidates = read_pilot(ROOT / 'data/cognate_candidates_v07.csv')

    def roster(self):
        return [dict(participant_id=f'{lang}{i}', background_stratum=lang)
                for lang in ('English', 'Portuguese', 'Mandarin', 'Swahili')
                for i in (1, 2)]

    def test_balanced_arms_and_no_unverified_claims(self):
        plan = plan_cognate_cohorts(self.candidates, self.lex, self.roster(), seed=101)
        self.assertEqual(plan['summary']['planned_participants'], 8)
        self.assertFalse(plan['summary']['human_data_collected'])
        self.assertFalse(plan['summary']['recognition_measured'])
        self.assertEqual(plan['summary']['background_strata'],
                         {'English': {"arm_0": 1, "arm_1": 1},
                          'Portuguese': {"arm_0": 1, "arm_1": 1},
                          'Mandarin': {"arm_0": 1, "arm_1": 1},
                          'Swahili': {"arm_0": 1, "arm_1": 1}})
        for pid, packet in plan['participants'].items():
            self.assertEqual(len(packet), 18)
            self.assertNotIn('condition', packet[0])
            self.assertNotIn('target_gloss', packet[0])
            self.assertEqual({r['response_gloss'] for r in packet}, {''})
            self.assertEqual({r['participant_id'] for r in packet}, {pid})
        self.assertEqual(len(plan['researcher_keys']), 144)
        self.assertEqual({r['condition'] for r in plan['researcher_keys']},
                         {'core', 'international', 'nonce_control'})

    def test_seed_and_row_order_do_not_change_assignments(self):
        roster = self.roster()
        a = plan_cognate_cohorts(self.candidates, self.lex, roster, seed=405)
        b = plan_cognate_cohorts(self.candidates, self.lex, list(reversed(roster)), seed=405)
        self.assertEqual(a, b)

    def test_refuse_odd_or_singleton_strata(self):
        for invalid in (self.roster()[:-1], [self.roster()[0]]):
            with self.assertRaisesRegex(VekaError, 'even number'):
                plan_cognate_cohorts(self.candidates, self.lex, invalid)

    def test_reject_bad_pseudonym_or_duplicate(self):
        roster = self.roster()
        for bad in ('../unsafe', 'contains space', '', 'a'*70):
            with self.subTest(bad=bad), self.assertRaises(VekaError):
                plan_cognate_cohorts(self.candidates, self.lex,
                                    [dict(roster[0], participant_id=bad)] + roster[1:])
        with self.assertRaises(VekaError):
            plan_cognate_cohorts(self.candidates, self.lex, roster + [roster[0]])
        formula = '=1+2'
        hostile = [dict(row, background_stratum=formula)
                   if row['background_stratum'] == 'English' else row for row in roster]
        with self.assertRaises(VekaError):
            plan_cognate_cohorts(self.candidates, self.lex, hostile)


    def test_strict_csv_rejects_malformed_or_identity_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'roster.csv'
            path.write_text('participant_id,background_stratum,email\nA1,English,a@b.com\n')
            with self.assertRaises(VekaError):
                read_cohort_roster(path)
            path.write_text('participant_id,background_stratum\nA1,English,extra\n')
            with self.assertRaises(VekaError):
                read_cohort_roster(path)

    def test_write_outputs_separately_and_refuses_overwrites(self):
        plan = plan_cognate_cohorts(self.candidates, self.lex, self.roster())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p, k = root / 'participant', root / 'researcher'
            result = write_cohort_plan(plan, p, k)
            self.assertEqual(result['participant_files'], 8)
            self.assertEqual(len(list(p.glob('*.csv'))), 8)
            self.assertEqual(len(list(k.glob('*.csv'))), 2)
            with (p / 'English1.csv').open(newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 18)
            self.assertNotIn('target_gloss', rows[0])
            self.assertNotIn('arm', rows[0])
            self.assertFalse((p / 'researcher-key.csv').exists())
            with (k / 'researcher-key.csv').open(newline='') as stream:
                researcher = list(csv.DictReader(stream))
            self.assertEqual(len(researcher), 144)
            with self.assertRaises(VekaError):
                write_cohort_plan(plan, p, k)
            self.assertFalse((p / 'researcher-key.csv').exists())

    def test_cli_creates_balanced_separate_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster = root / 'cohort.csv'
            with roster.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=('participant_id', 'background_stratum'))
                writer.writeheader()
                writer.writerows(self.roster())
            process = subprocess.run([
                sys.executable, '-m', 'veka', 'cohort-plan',
                '--roster', str(roster),
                '--participants-dir', str(root / 'participants'),
                '--researcher-dir', str(root / 'researcher'), '--seed', '101',
            ], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(process.stdout)['planned_participants'], 8)
            self.assertTrue((root / 'researcher' / 'researcher-key.csv').exists())
            self.assertFalse((root / 'participants' / 'researcher-key.csv').exists())

    def test_directory_overlap_is_blocked_before_writes(self):
        plan = plan_cognate_cohorts(self.candidates, self.lex, self.roster())
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'participants'
            with self.assertRaises(VekaError):
                write_cohort_plan(plan, p, p / 'researcher')
            self.assertFalse(p.exists())


if __name__ == '__main__':
    unittest.main()
