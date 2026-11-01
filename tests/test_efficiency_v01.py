"""Cross-language efficiency audit must not manufacture human or phonetic evidence."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import VekaError
from veka.efficiency import (default_manifest, audit_efficiency,
                             score_efficiency_trials, read_efficiency_trials,
                             TRIAL_FIELDS)

ROOT = Path(__file__).resolve().parents[1]


class EfficiencyAuditTests(unittest.TestCase):
    def setUp(self):
        self.manifest = default_manifest()

    def test_frozen_manifest_is_versioned_in_data_not_derived_dynamically(self):
        snapshot = json.loads((ROOT / 'data/efficiency_manifest_v01.json').read_text(encoding='utf-8'))
        self.assertEqual(default_manifest(), snapshot)
        self.assertEqual(snapshot['schema_version'], 'veka.efficiency-manifest.v01')

    def test_existing_curated_translations_are_unverified_and_parseable(self):
        report = audit_efficiency(self.manifest)
        self.assertEqual(report["items"], 10)
        self.assertEqual(report["languages"], ["en", "pt-BR", "veka", "zh"])
        self.assertEqual(report["veka_parse_passes"], 10)
        self.assertFalse(report["comprehension_measured"])
        self.assertFalse(report["language_efficiency_ranked"])
        self.assertEqual(report["canonical_changes"], 0)
        self.assertEqual(report["independently_reviewed_variants"], 0)
        self.assertTrue(all(row["veka"]["spoken_syllables"] > 0 for row in report["rows"]))
        self.assertTrue(all(row["variants"]["zh"]["spoken_syllables"] is None for row in report["rows"]))

    def test_compounds_count_spoken_syllables_but_not_silent_hyphen(self):
        report = audit_efficiency(self.manifest)
        compound = next(row for row in report["rows"] if row["veka"]["text"].startswith("Ren-sak"))
        self.assertEqual(compound["veka"]["spoken_syllables"], 4)
        self.assertEqual(compound["veka"]["morphemes"], 4)
        self.assertEqual(compound["veka"]["words"], 3)

    def test_invalid_corpus_and_unreviewed_manual_metrics_fail_closed(self):
        failures = []
        bad = copy.deepcopy(self.manifest)
        bad["items"][1]["id"] = bad["items"][0]["id"]
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["items"][0]["veka"] = "Mi zzz gos."
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["items"][0]["variants"]["en"]["spoken_syllables"] = 4
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["items"][0]["variants"]["en"]["status"] = "independently_reviewed"
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["items"][0]["variants"]["xx"] = bad["items"][0]["variants"].pop("zh")
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["items"][0]["variants"]["en"]["extra"] = "quietly accepted"
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["items"][0]["variants"]["en"]["text"] = " "
        failures.append(bad)
        bad = copy.deepcopy(self.manifest)
        bad["schema_version"] = "unknown"
        failures.append(bad)
        for invalid in failures:
            with self.subTest(bad=invalid["items"][0]), self.assertRaises(VekaError):
                audit_efficiency(invalid)

    def test_annotated_qualitative_metrics_remain_descriptive(self):
        doc = copy.deepcopy(self.manifest)
        en = doc["items"][0]["variants"]["en"]
        en.update(status="independently_reviewed", review_id="editor-01",
                  spoken_syllables=6, morphemes=4, ambiguity_risk=1)
        report = audit_efficiency(doc)
        self.assertEqual(report["independently_reviewed_variants"], 1)
        item = report["rows"][0]["variants"]["en"]
        self.assertEqual(item["spoken_syllables"], 6)
        self.assertEqual(item["morphemes"], 4)
        self.assertEqual(item["ambiguity_risk"], 1)
        self.assertFalse(report["language_efficiency_ranked"])

    def test_empty_trial_template_no_observations(self):
        rows = read_efficiency_trials(ROOT / "data/efficiency_trials_v01.csv")
        self.assertEqual(rows, [])
        report = score_efficiency_trials(rows, self.manifest)
        self.assertFalse(report["observed"])
        self.assertEqual(report["trial_count"], 0)
        self.assertFalse(report["comparative_benefit_established"])

    def test_requires_reviewed_comparators_for_observations(self):
        row = self.row("P001", "en")
        with self.assertRaises(VekaError):
            score_efficiency_trials([row], self.manifest)

    def row(self, pid, lang, **kwargs):
        data = {"participant_id": pid, "background_family": "Sino-Tibetan",
                "item_id": "L01", "language": lang, "correct": "1",
                "elapsed_ms": "1500", "repair_ms": "500", "critical_error": "0"}
        data.update(kwargs)
        return data

    def test_trial_scoring_with_real_input_format_never_chooses_winner(self):
        doc = copy.deepcopy(self.manifest)
        doc["items"][0]["variants"]["en"]["status"] = "independently_reviewed"
        doc["items"][0]["variants"]["en"]["review_id"] = "editor-01"
        rows = [self.row("P001", "veka"), self.row("P002", "en", correct="0", critical_error="1")]
        report = score_efficiency_trials(rows, doc)
        self.assertTrue(report["observed"])
        self.assertEqual(report["by_language"]["veka"]["correct_per_minute"], 30)
        self.assertEqual(report["by_language"]["en"]["critical_errors"], 1)
        self.assertEqual(report["paired_cells"], 1)
        self.assertFalse(report["comparative_benefit_established"])
        self.assertNotIn("winner", report)
        for invalid in ([rows[0], rows[0]], [self.row("P001", "xx")],
                        [self.row("P001", "veka", elapsed_ms="0")],
                        [self.row("P001", "veka", correct="yes")],
                        [self.row("P001", "veka", critical_error="1")],
                        [self.row("P001", "veka", extra="bad")]):
            with self.subTest(invalid=invalid), self.assertRaises(VekaError):
                score_efficiency_trials(invalid, doc)

    def test_cli_template_is_editable_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.json'
            cmd = [sys.executable, '-m', 'veka', 'efficiency-template', '--output', str(path)]
            first = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), self.manifest)
            second = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')), self.manifest)
            path.write_text('{bad json', encoding='utf-8')
            audit = subprocess.run([sys.executable, '-m', 'veka', 'efficiency-audit',
                                    '--manifest', str(path)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(audit.returncode, 2)
            self.assertIn('VEKA ERROR', audit.stderr)
            self.assertNotIn('Traceback', audit.stderr)

    def test_cli_audit_and_score_are_reproducible(self):
        for cmd in ("efficiency-audit", "efficiency-score"):
            run = subprocess.run([sys.executable, "-m", "veka", cmd],
                                 cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)
            self.assertEqual(result["canonical_changes"], 0)
            self.assertFalse(result.get("comparative_benefit_established", False))


if __name__ == "__main__":
    unittest.main()
