"""Versioned, noncanonical Veka cognate pilot regression contract."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError, parse
from veka.cognates import (read_pilot, audit_pilot, make_pilot_manifest,
                          score_pilot)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class CognatePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(DATA / "lexicon.csv")
        cls.rows = read_pilot(DATA / "cognate_candidates_v07.csv")

    def test_import_rejects_unterminated_quotes_and_extra_columns(self):
        header = ",".join(("concept_id", "gloss", "pos", "category", "core_form",
                           "candidate_form", "control_form", "priority", "status", "note"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "damaged.csv"
            path.write_text(header + "\nN01,taxi,noun,addition,,tak-si,yik-be,1,unverified_draft,\"unfinished\n",
                            encoding="utf-8")
            with self.assertRaises(VekaError):
                read_pilot(path)
            path.write_text(header + "\nN01,taxi,noun,addition,,tak-si,yik-be,1,unverified_draft,ok,extra\n",
                            encoding="utf-8")
            with self.assertRaises(VekaError):
                read_pilot(path)

    def test_pilot_has_ten_additions_and_eight_replacements_without_adoption(self):
        report = audit_pilot(self.rows, self.lex)
        self.assertEqual(report["candidate_count"], 18)
        self.assertEqual(report["categories"], {"addition": 10, "replacement": 8})
        self.assertEqual(report["rejected_count"], 0)
        self.assertEqual(report["adopted_count"], 0)
        self.assertFalse(report["recognition_measured"])
        self.assertEqual(len(self.lex), 1025)
        self.assertEqual(report["verified_evidence_records"], 0)

    def test_proposed_terms_have_no_parser_effect(self):
        for row in self.rows:
            self.assertNotIn(row["candidate_form"], self.lex)
            with self.assertRaises(VekaError):
                parse("Mi lin " + row["candidate_form"] + ".", self.lex)

    def test_replacement_semantics_are_exact(self):
        wrong = [dict(r) for r in self.rows]
        i = next(i for i, r in enumerate(wrong) if r["category"] == "replacement")
        wrong[i]["gloss"] = "irrelevant"
        with self.assertRaises(VekaError):
            audit_pilot(wrong, self.lex)

    def test_reserved_segments_and_collisions_rejected(self):
        base = [dict(r) for r in self.rows]
        for bad in ("vi-de-o", "su-si", "ko-fi", "mi-kas", "ri-ce", "za"):
            trial = [dict(r) for r in base]
            trial[0]["candidate_form"] = bad
            report = audit_pilot(trial, self.lex)
            self.assertGreater(report["rejected_count"], 0, bad)

    def test_duplicate_and_corrupt_study_rows_fail_closed(self):
        with self.assertRaises(VekaError):
            audit_pilot(self.rows + [dict(self.rows[0])], self.lex)
        altered = [dict(r) for r in self.rows]
        altered[1]["candidate_form"] = altered[0]["candidate_form"]
        with self.assertRaises(VekaError):
            audit_pilot(altered, self.lex)
        with self.assertRaises(VekaError):
            audit_pilot([dict(r, category="accepted") for r in self.rows], self.lex)

    def test_evidence_needs_attributable_verification_not_guesswork(self):
        evidence = [
            dict(concept_id="N01", language="Spanish", language_family="Indo-European",
                 attested_form="taxi", citation="https://example.org/spanish",
                 reviewer="analyst", verified="yes"),
            dict(concept_id="N01", language="Portuguese", language_family="Indo-European",
                 attested_form="táxi", citation="https://example.org/portuguese",
                 reviewer="analyst", verified="yes"),
        ]
        report = audit_pilot(self.rows, self.lex, evidence)
        self.assertEqual(report["verified_evidence_records"], 2)
        self.assertEqual(report["evidence"]["by_concept"]["N01"]["independent_families"], 1)
        self.assertFalse(report["recognition_measured"])
        with self.assertRaises(VekaError):
            audit_pilot(self.rows, self.lex, [dict(evidence[0], citation="")])

    def test_manifest_blindness_reproducibility_and_arms(self):
        visible, key = make_pilot_manifest(self.rows, self.lex, "P001", seed=11, arm=0)
        visible2, key2 = make_pilot_manifest(self.rows, self.lex, "P001", seed=11, arm=0)
        self.assertEqual((visible, key), (visible2, key2))
        self.assertEqual(len(visible), 18)
        self.assertEqual(len({r["trial_id"] for r in visible}), 18)
        self.assertTrue(all("condition" not in row and "target_gloss" not in row for row in visible))
        replacement = [r for r in key if r["category"] == "replacement"]
        self.assertEqual(sum(r["condition"] == "core" for r in replacement), 4)
        self.assertEqual(sum(r["condition"] == "international" for r in replacement), 4)
        addition = [r for r in key if r["category"] == "addition"]
        self.assertEqual(sum(r["condition"] == "international" for r in addition), 5)
        self.assertEqual(sum(r["condition"] == "nonce_control" for r in addition), 5)
        _, other = make_pilot_manifest(self.rows, self.lex, "P002", seed=11, arm=1)
        self.assertEqual(
            {r["concept_id"]: r["condition"] for r in replacement},
            {r["concept_id"]: ("international" if r["condition"] == "core" else "core")
             for r in other if r["category"] == "replacement"},
        )
        self.assertEqual(
            {r["concept_id"]: r["condition"] for r in addition},
            {r["concept_id"]: ("nonce_control" if r["condition"] == "international" else "international")
             for r in other if r["category"] == "addition"},
        )
        with self.assertRaises(VekaError):
            make_pilot_manifest(self.rows, self.lex, "P001", seed=11, arm=2)

    def test_real_results_required_and_groups_are_not_conflated(self):
        _, key = make_pilot_manifest(self.rows, self.lex, "P001", seed=11, arm=0)
        with self.assertRaises(VekaError):
            score_pilot(key, [])
        scored = [
            dict(trial_id=r["trial_id"], correct="1", response_ms="1200",
                 repair_count="0") for r in key
        ]
        result = score_pilot(key, scored)
        self.assertEqual(result["trials"], 18)
        self.assertEqual(result["groups"]["addition:international"]["n"], 5)
        self.assertEqual(result["groups"]["addition:nonce_control"]["n"], 5)
        self.assertEqual(result["groups"]["replacement:core"]["n"], 4)
        self.assertEqual(result["groups"]["replacement:international"]["n"], 4)
        self.assertFalse(result["recognition_measured_without_human_data"])
        self.assertFalse(result["causal_effect_established"])
        with self.assertRaises(VekaError):
            score_pilot(key, scored[:-1])
        with self.assertRaises(VekaError):
            score_pilot(key, scored + [scored[0]])
        with self.assertRaises(VekaError):
            score_pilot(key, [dict(scored[0], correct="yes")] + scored[1:])

    def test_nonce_controls_cannot_be_existing_words_or_grammar_fragments(self):
        for bad in ("mi", "vi-de-o", "mi-si", "dak"):
            modified = [dict(r) for r in self.rows]
            modified[0]["control_form"] = bad
            report = audit_pilot(modified, self.lex)
            self.assertGreater(report["rejected_count"], 0, bad)
        modified = [dict(r) for r in self.rows]
        modified[0]["control_form"] = modified[1]["control_form"]
        with self.assertRaises(VekaError):
            audit_pilot(modified, self.lex)

    def test_cli_audit_manifest_and_score(self):
        result = subprocess.run(
            [sys.executable, "-m", "veka", "cognate-audit"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["candidate_count"], 18)
        with tempfile.TemporaryDirectory() as directory:
            participant = str(Path(directory) / "participant.csv")
            key = str(Path(directory) / "researcher.csv")
            cmd = [sys.executable, "-m", "veka", "cognate-manifest",
                   "--participant", "P001", "--arm", "0",
                   "--output", participant, "--answer-key", key]
            made = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(made.returncode, 0, made.stderr)
            with open(participant, encoding="utf-8", newline="") as file:
                self.assertEqual(len(list(csv.DictReader(file))), 18)
            again = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)


if __name__ == "__main__":
    unittest.main()
