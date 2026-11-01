"""Controlled, synthetic fixtures for human-only Veka root-study adjudication."""
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
from veka.root_study_results import (
    KEY_FIELDS, RESPONSE_FIELDS, JUDGE_FIELDS, prepare_root_judge_sheet,
    read_root_study_csv, score_root_study,
)

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows, fields):
    with Path(path).open("w", newline="", encoding="utf8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class RootStudyResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.queue = read_candidates(ROOT / "data/international_candidates_v04.csv")

    def synthetic_records(self):
        roster = [
            {"participant_id": f"{lang}{i}", "background_stratum": lang}
            for lang in ("English", "Portuguese") for i in (1, 2)
        ]
        plan = plan_root_cohorts(self.queue, self.lex, roster, seed=17)
        key = plan["researcher_keys"]
        responses = []
        for participant, sheet in plan["participants"].items():
            for row in sheet:
                responses.append({
                    **row, "response_gloss": "synthetic response",
                    "response_ms": "1500", "prior_exposure": "no",
                })
        targets = {r["trial_id"]: r["target_gloss"] for r in key}
        judges = [
            {
                "trial_id": r["trial_id"], "target_gloss": targets[r["trial_id"]],
                "response_gloss": r["response_gloss"],
                "correct": "1", "critical_error": "0", "judge_id": "J1",
            }
            for r in responses
        ]
        return key, responses, judges

    def test_blinded_judge_sheet_contains_no_allocation_or_identity(self):
        key, responses, _ = self.synthetic_records()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_csv(folder / "key.csv", key, KEY_FIELDS)
            write_csv(folder / "responses.csv", responses, RESPONSE_FIELDS)
            result = prepare_root_judge_sheet(
                folder / "key.csv", folder / "responses.csv", folder / "judge.csv"
            )
            self.assertEqual(result["unscored_trials"], 32)
            rows = read_root_study_csv(folder / "judge.csv", JUDGE_FIELDS)
            self.assertEqual(len(rows), 32)
            self.assertEqual(rows[0]["correct"], "")
            self.assertNotIn("condition", rows[0])
            self.assertNotIn("participant_id", rows[0])
            self.assertNotIn("presented_form", rows[0])
            self.assertEqual(rows[0]["judge_id"], "")
            self.assertTrue(result["blinded_to_condition"])
            with self.assertRaises(VekaError):
                prepare_root_judge_sheet(
                    folder / "key.csv", folder / "responses.csv", folder / "judge.csv"
                )

    def test_scoring_uses_human_judgments_and_no_raw_responses_in_report(self):
        key, responses, judges = self.synthetic_records()
        report = score_root_study(key, responses, judges)
        self.assertEqual(report["submitted_trials"], 32)
        self.assertEqual(report["participants_claimed"], 4)
        self.assertEqual(report["first_sight_trials"], 32)
        self.assertEqual(report["by_condition"]["core"]["trials"], 16)
        self.assertEqual(report["by_condition"]["candidate"]["trials"], 16)
        self.assertEqual(report["by_condition"]["candidate"]["accuracy"], 1.0)
        self.assertEqual(report["by_condition"]["candidate"]["correct_per_minute"], 40.0)
        self.assertEqual(report["by_stratum"]["Portuguese"]["candidate"]["trials"], 8)
        self.assertEqual(len(report["by_concept"]), 8)
        self.assertFalse(report["independent_human_verification"])
        self.assertFalse(report["adoption_authorized"])
        self.assertNotIn("synthetic response", json.dumps(report))
        self.assertNotIn("English1", json.dumps(report))

    def test_prior_exposure_is_excluded_from_primary_first_sight(self):
        key, responses, judges = self.synthetic_records()
        target = next(row for row in key if row["condition"] == "candidate")
        response = next(row for row in responses if row["trial_id"] == target["trial_id"])
        response["prior_exposure"] = "yes"
        judged = next(row for row in judges if row["trial_id"] == target["trial_id"])
        judged["correct"] = "0"
        judged["critical_error"] = "1"
        report = score_root_study(key, responses, judges)
        self.assertEqual(report["submitted_trials"], 32)
        self.assertEqual(report["first_sight_trials"], 31)
        self.assertEqual(report["excluded_for_prior_exposure"], 1)
        self.assertEqual(report["by_condition"]["candidate"]["trials"], 15)
        self.assertEqual(report["all_submitted_critical_errors"], 1)
        self.assertEqual(report["by_condition"]["candidate"]["critical_errors"], 0)

    def test_critical_errors_count_only_with_incorrect_judgments(self):
        key, responses, judges = self.synthetic_records()
        target = next(row for row in key if row["condition"] == "candidate")
        judged = next(row for row in judges if row["trial_id"] == target["trial_id"])
        judged["correct"] = "0"
        judged["critical_error"] = "1"
        report = score_root_study(key, responses, judges)
        self.assertEqual(report["by_condition"]["candidate"]["critical_errors"], 1)
        self.assertFalse(report["human_benefit_established"])
        judged["correct"] = "1"
        with self.assertRaises(VekaError):
            score_root_study(key, responses, judges)

    def test_rejects_missing_duplicate_mismatched_or_unjudged_rows(self):
        key, responses, judges = self.synthetic_records()
        broken = [
            (key[:-1], responses, judges),
            (key, responses[:-1], judges),
            (key, responses + [responses[0]], judges),
            (key, responses, judges[:-1]),
            (key, [dict(responses[0], presented_form="tampered")] + responses[1:], judges),
            (key, [dict(responses[0], response_ms="nan")] + responses[1:], judges),
            (key, [dict(responses[0], response_ms="0")] + responses[1:], judges),
            (key, [dict(responses[0], prior_exposure="")] + responses[1:], judges),
            (key, [dict(responses[0], presentation_modality="audio")] + responses[1:], judges),
            (key, responses, [dict(judges[0], response_gloss="changed")] + judges[1:]),
            (key, responses, [dict(judges[0], correct="")] + judges[1:]),
            (key, responses, [dict(judges[0], judge_id="")] + judges[1:]),
            (key, responses, [dict(judges[0], guess="yes")] + judges[1:]),
        ]
        for k, r, j in broken:
            with self.subTest(broken=(len(k), len(r), len(j))), self.assertRaises(VekaError):
                score_root_study(k, r, j)

    def test_cli_scores_only_explicitly_supplied_judged_data(self):
        key, responses, judges = self.synthetic_records()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_csv(folder / "key.csv", key, KEY_FIELDS)
            write_csv(folder / "responses.csv", responses, RESPONSE_FIELDS)
            write_csv(folder / "judges.csv", judges, JUDGE_FIELDS)
            prepare = subprocess.run(
                [sys.executable, "-m", "veka", "root-study-judge",
                 "--key", str(folder / "key.csv"),
                 "--responses", str(folder / "responses.csv"),
                 "--output", str(folder / "blank.csv")],
                cwd=ROOT, text=True, capture_output=True
            )
            self.assertEqual(prepare.returncode, 0, prepare.stderr)
            self.assertEqual(json.loads(prepare.stdout)["unscored_trials"], 32)
            command = [sys.executable, "-m", "veka", "root-study-score",
                       "--key", str(folder / "key.csv"),
                       "--responses", str(folder / "responses.csv"),
                       "--judgments", str(folder / "judges.csv")]
            scored = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(scored.returncode, 0, scored.stderr)
            self.assertEqual(json.loads(scored.stdout)["first_sight_trials"], 32)
            self.assertEqual(json.loads(scored.stdout)["independent_human_verification"], False)
            bad = subprocess.run(command[:-1] + [str(folder / "blank.csv")],
                                 cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("VEKA ERROR", bad.stderr)


if __name__ == "__main__":
    unittest.main()
