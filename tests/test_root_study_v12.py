"""Eight-root controlled study plan: study materials are not human outcomes."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.cohort_plan import write_cohort_plan
from veka.international import read_candidates
from veka.root_study import plan_root_cohorts

ROOT = Path(__file__).resolve().parents[1]


class RootStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.candidates = read_candidates(ROOT / "data/international_candidates_v04.csv")

    def roster(self):
        return [dict(participant_id=f"{lang}{idx}", background_stratum=lang)
                for lang in ("English", "Portuguese", "Mandarin", "Swahili")
                for idx in (1, 2)]

    def test_each_language_stratum_gets_complementary_balanced_conditions(self):
        plan = plan_root_cohorts(self.candidates, self.lex, self.roster(), seed=41)
        summary = plan["summary"]
        self.assertEqual(summary["planned_participants"], 8)
        self.assertEqual(summary["trials_per_participant"], 8)
        self.assertFalse(summary["human_data_collected"])
        self.assertFalse(summary["adoption_authorized"])
        self.assertEqual(len(plan["researcher_keys"]), 64)
        self.assertEqual({v["arm_0"] for v in summary["background_strata"].values()}, {1})
        self.assertEqual({v["arm_1"] for v in summary["background_strata"].values()}, {1})
        by_id = {row["participant_id"]: row["background_stratum"] for row in plan["assignments"]}
        by_key = {}
        for row in plan["researcher_keys"]:
            by_key.setdefault((by_id[row["participant_id"]], row["concept_id"]), []).append(row["condition"])
        for conditions in by_key.values():
            self.assertEqual(set(conditions), {"core", "candidate"})
        for pid, sheet in plan["participants"].items():
            self.assertEqual(len(sheet), 8)
            self.assertEqual(len({r["trial_id"] for r in sheet}), 8)
            self.assertEqual({r["response_gloss"] for r in sheet}, {""})
            self.assertNotIn("target_gloss", sheet[0])
            self.assertNotIn("condition", sheet[0])
            conds = [r["condition"] for r in plan["researcher_keys"]
                     if r["participant_id"] == pid]
            self.assertEqual(conds.count("core"), 4)
            self.assertEqual(conds.count("candidate"), 4)

    def test_reordering_roster_does_not_change_assignment(self):
        a = plan_root_cohorts(self.candidates, self.lex, self.roster(), seed=17)
        b = plan_root_cohorts(self.candidates, self.lex, list(reversed(self.roster())), seed=17)
        self.assertEqual(a, b)

    def test_unbalanced_or_unsafe_roster_fails(self):
        candidates = self.candidates
        for bad in ([], self.roster()[:-1],
                    [dict(self.roster()[0], participant_id="../escape")] + self.roster()[1:],
                    self.roster() + [self.roster()[0]]):
            with self.subTest(bad=bad), self.assertRaises(VekaError):
                plan_root_cohorts(candidates, self.lex, bad)

    def test_separated_private_files_and_no_overwrites(self):
        plan = plan_root_cohorts(self.candidates, self.lex, self.roster())
        with tempfile.TemporaryDirectory() as tmp:
            participant = Path(tmp) / "participant"
            private = Path(tmp) / "private"
            info = write_cohort_plan(plan, participant, private)
            self.assertEqual(info["participant_files"], 8)
            self.assertFalse((participant / "researcher-key.csv").exists())
            self.assertTrue((private / "researcher-key.csv").exists())
            self.assertEqual(len(list(participant.glob("*.csv"))), 8)
            with self.assertRaises(VekaError):
                write_cohort_plan(plan, participant, private)

    def test_cli_generates_empty_blinded_participant_sheets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            roster_path = root / "roster.csv"
            with roster_path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=("participant_id", "background_stratum"))
                writer.writeheader()
                writer.writerows(self.roster())
            process = subprocess.run([
                sys.executable, "-m", "veka", "root-study-plan",
                "--roster", str(roster_path),
                "--participants-dir", str(root / "participant"),
                "--researcher-dir", str(root / "researcher"),
                "--seed", "41",
            ], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result["trials_per_participant"], 8)
            self.assertFalse(result["human_data_collected"])
            self.assertTrue((root / "researcher" / "assignments.csv").exists())


if __name__ == "__main__":
    unittest.main()
