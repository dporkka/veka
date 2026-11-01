"""Researcher annotation remains separate from the participant browser session."""
import csv
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError, Lexicon
from veka.cognates import read_pilot, make_pilot_manifest, score_pilot
from veka.cognate_session import prepare_judge_sheet

ROOT = Path(__file__).resolve().parents[1]


class JudgeSheetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lex = Lexicon.from_csv(ROOT / "data" / "lexicon.csv")
        cls.participant, cls.key = make_pilot_manifest(
            read_pilot(ROOT / "data" / "cognate_candidates_v07.csv"),
            lex, "P001", arm=0)

    def make_files(self, tmp, responses=None):
        key = tmp / "secret.csv"
        observed = tmp / "responses.csv"
        with key.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.key[0]))
            writer.writeheader(); writer.writerows(self.key)
        rows = responses if responses is not None else [
            dict(participant_id=row["participant_id"], trial_id=row["trial_id"],
                 presented_form=row["presented_form"], response_gloss="unknown",
                 response_ms="1200", prior_exposure="no", first_language="Turkish",
                 language_background_family="Turkic", timing_interrupted="no")
            for row in self.participant
        ]
        with observed.open("w", newline="", encoding="utf-8") as f:
            writer=csv.DictWriter(f, fieldnames=[
                "participant_id", "trial_id", "presented_form", "response_gloss",
                "response_ms", "prior_exposure", "first_language",
                "language_background_family", "timing_interrupted"
            ])
            writer.writeheader(); writer.writerows(rows)
        return key,observed

    def test_private_judge_sheet_matches_answer_key_but_excludes_condition(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp=Path(folder); key,observed=self.make_files(tmp)
            output=tmp/"judge.csv"
            summary=prepare_judge_sheet(key,observed,output)
            with output.open(encoding="utf-8",newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),18)
            self.assertFalse(summary["human_data_verified"])
            self.assertNotIn("condition",rows[0])
            self.assertEqual(rows[0]["target_gloss"],self.key[0]["target_gloss"])
            self.assertEqual(rows[0]["response_gloss"],"unknown")
            self.assertEqual(rows[0]["correct"],"")
            self.assertEqual(rows[0]["repair_count"],"")
            with self.assertRaises(VekaError):
                score_pilot(self.key,rows)
            for row in rows:
                row["correct"]="0";row["repair_count"]="0"
            result=score_pilot(self.key,rows)
            self.assertEqual(result["trials"],18)
            self.assertFalse(result["causal_effect_established"])

    def test_rejects_mismatched_or_missing_responses(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp=Path(folder)
            key,observed=self.make_files(tmp)
            with observed.open(encoding="utf-8",newline="") as f: rows=list(csv.DictReader(f))
            wrong=[dict(x) for x in rows];wrong[0]["presented_form"]="forged"
            key,observed=self.make_files(tmp,wrong)
            with self.assertRaises(VekaError):prepare_judge_sheet(key,observed,tmp/"judge.csv")
            key,observed=self.make_files(tmp,rows[:-1])
            with self.assertRaises(VekaError):prepare_judge_sheet(key,observed,tmp/"judge.csv")
            key,observed=self.make_files(tmp,rows+[rows[0]])
            with self.assertRaises(VekaError):prepare_judge_sheet(key,observed,tmp/"judge.csv")

    def test_browser_escaped_negative_participant_id_matches_key(self):
        lex = Lexicon.from_csv(ROOT / "data" / "lexicon.csv")
        participant, secret = make_pilot_manifest(
            read_pilot(ROOT / "data" / "cognate_candidates_v07.csv"),
            lex, "-P001", arm=0)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            key = root / "key.csv"
            responses = root / "responses.csv"
            output = root / "judgments.csv"
            with key.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(secret[0]))
                writer.writeheader()
                writer.writerows(secret)
            fields = ("participant_id", "trial_id", "presented_form",
                      "response_gloss", "response_ms", "prior_exposure",
                      "first_language", "language_background_family",
                      "timing_interrupted")
            rows = [{
                "participant_id": "'" + row["participant_id"],
                "trial_id": row["trial_id"],
                "presented_form": row["presented_form"],
                "response_gloss": "unknown",
                "response_ms": "1200", "prior_exposure": "no",
                "first_language": "Turkish",
                "language_background_family": "Turkic",
                "timing_interrupted": "no",
            } for row in participant]
            with responses.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            self.assertEqual(prepare_judge_sheet(key, responses, output)["trials"], 18)
            rows[0]["participant_id"] = "'P001"
            tampered = root / "tampered.csv"
            with tampered.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(VekaError):
                prepare_judge_sheet(key, tampered, root / "reject.csv")

    def test_private_judge_sheet_neutralizes_spreadsheet_formulas(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            responses = [
                dict(participant_id=row["participant_id"],
                     trial_id=row["trial_id"],
                     presented_form=row["presented_form"],
                     response_gloss='=HYPERLINK("https://example.org")',
                     response_ms="1200", prior_exposure="no",
                     first_language="+SUM(1,1)",
                     language_background_family="@IMPORTXML(1)",
                     timing_interrupted="no")
                for row in self.participant
            ]
            key, data = self.make_files(root, responses)
            output = root / "judge.csv"
            prepare_judge_sheet(key, data, output)
            with output.open(encoding="utf-8", newline="") as stream:
                first = next(csv.DictReader(stream))
            for field in ("response_gloss", "first_language",
                          "language_background_family"):
                self.assertTrue(first[field].startswith("'"), field)

    def test_key_or_response_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp=Path(folder);key,observed=self.make_files(tmp)
            for out in (key,observed):
                with self.assertRaises(VekaError):prepare_judge_sheet(key,observed,out)


if __name__=="__main__":
    unittest.main()
