"""Blinded browser study sessions must never expose researcher answer keys."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError, Lexicon
from veka.cognates import read_pilot, make_pilot_manifest
from veka.cognate_session import read_blind_manifest, write_blind_session

ROOT = Path(__file__).resolve().parents[1]


class BlindedSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lex = Lexicon.from_csv(ROOT / "data" / "lexicon.csv")
        rows = read_pilot(ROOT / "data" / "cognate_candidates_v07.csv")
        cls.participant, cls.secret_key = make_pilot_manifest(rows, lex, "P001", seed=31, arm=0)

    def make_manifest(self, folder: Path, rows=None):
        path = folder / "participant.csv"
        data = self.participant if rows is None else rows
        with path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=list(self.participant[0]))
            writer.writeheader()
            writer.writerows(data)
        return path

    def test_complete_session_has_only_blind_fields_and_original_stimulus_order(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            out = folder / "session.json"
            write_blind_session(read_blind_manifest(self.make_manifest(folder)), out)
            data = json.loads(out.read_text())
            self.assertEqual(data["schema_version"], "veka.cognate-session.v07")
            self.assertEqual(data["participant_id"], "P001")
            self.assertEqual(len(data["trials"]), 18)
            self.assertEqual([x["presented_form"] for x in data["trials"]],
                             [x["presented_form"] for x in self.participant])
            self.assertEqual(set(data["trials"][0]), {"trial_id", "presented_form"})
            secret = json.dumps(data, ensure_ascii=False)
            for key in ("target_gloss", "correct_choice", "condition", "core_form", "nonce_control"):
                self.assertNotIn('"' + key + '"', secret)
            self.assertNotIn(self.secret_key[0]["target_gloss"] + '",', secret)

    def test_corrupt_manifest_rejected_before_any_output(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            out = folder / "session.json"
            for altered in [
                [dict(self.participant[0], response_gloss="pre-filled")] + self.participant[1:],
                self.participant[:-1] + [dict(self.participant[0])],
                [dict(self.participant[0], participant_id="P002")] + self.participant[1:],
                [dict(self.participant[0], trial_id="not-opaque")] + self.participant[1:],
                [dict(self.participant[0], presented_form="")] + self.participant[1:],
            ]:
                with self.subTest(row=altered[0]):
                    with self.assertRaises(VekaError):
                        write_blind_session(read_blind_manifest(self.make_manifest(folder, altered)), out)
                    self.assertFalse(out.exists())

    def test_missing_values_extra_column_and_bad_quotes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            path = self.make_manifest(folder)
            original = path.read_text()
            path.write_text(original + "bogus,extra,row\n")
            with self.assertRaises(VekaError):
                read_blind_manifest(path)
            path.write_text(original + '"unfinished\n')
            with self.assertRaises(VekaError):
                read_blind_manifest(path)
            path.write_text(original.replace("P001", "", 1))
            with self.assertRaises(VekaError):
                read_blind_manifest(path)

    def test_refuses_overwrite_and_same_source_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            src = self.make_manifest(folder)
            out = folder / "session.json"
            write_blind_session(read_blind_manifest(src), out)
            with self.assertRaises(VekaError):
                write_blind_session(read_blind_manifest(src), out)
            with self.assertRaises(VekaError):
                write_blind_session(read_blind_manifest(src), src)

    def test_cli_and_static_study_have_no_answer_key_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            src = self.make_manifest(folder)
            out = folder / "session.json"
            run = subprocess.run([sys.executable, "-m", "veka", "cognate-session",
                                  "--manifest", str(src), "--output", str(out)],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(out.is_file())
            self.assertFalse(json.loads(run.stdout)["human_data_collected"])
        page = (ROOT / "site" / "cognate-study.html").read_text(encoding="utf-8")
        self.assertIn('id="session-file"', page)
        self.assertIn('id="export-responses"', page)
        self.assertIn("performance.now()", page)
        self.assertNotIn("target_gloss", page)
        self.assertNotIn("https://cdn.", page)


if __name__ == "__main__":
    unittest.main()
