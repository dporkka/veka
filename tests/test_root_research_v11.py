"""A complete, noncanonical root inventory and opt-in scenario comparison."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.core import Lexicon, VekaError
from veka.international import read_candidates
from veka.root_research import build_root_inventory, compare_scenarios, read_scenarios

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {
    "recognition_acquisition": 35,
    "pronunciation_listening": 25,
    "compactness": 15,
    "semantic_clarity": 15,
    "cross_family_access": 10,
}


def scenario(concept_id, condition, form, *, recognition=50, critical="0"):
    return {
        "concept_id": concept_id, "condition": condition, "form": form,
        "recognition_acquisition": str(recognition),
        "pronunciation_listening": "70", "compactness": "80",
        "semantic_clarity": "90", "cross_family_access": "40",
        "critical_error_count": critical,
        "scenario_note": "Explicit synthetic test assumption, not participant data.",
    }


class RootResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = Lexicon.from_csv(ROOT / "data/lexicon.csv")
        cls.queue = read_candidates(ROOT / "data/international_candidates_v04.csv")

    def test_exhaustive_inventory_covers_roots_and_compound_dependencies(self):
        before = dict(self.lex)
        report = build_root_inventory(self.lex, self.queue)
        roots = report["roots"]
        self.assertEqual(len(roots), 317)
        self.assertEqual(report["canonical_compounds"], 708)
        self.assertEqual({r["form"] for r in roots}, {
            x.form for x in self.lex.values() if x.kind == "root"})
        self.assertEqual(sum(r["head_compounds"] for r in roots), 708)
        self.assertEqual(sum(r["modifier_compounds"] for r in roots), 708)
        self.assertEqual(report["queued_roots"], 100)
        self.assertEqual(report["unmapped_roots"], 217)
        self.assertEqual(report["proposed_candidates"], 8)
        self.assertEqual(self.lex, before)
        self.assertFalse(report["adoption_authorized"])

    def test_protected_grammar_numbers_and_time_are_never_suggested_for_replacement(self):
        rows = {r["form"]: r for r in build_root_inventory(self.lex, self.queue)["roots"]}
        for form in ("mi", "pa", "ne", "nul", "ran", "sek", "nal"):
            self.assertEqual(rows[form]["research_status"], "protected_structural")
            self.assertIsNone(rows[form]["candidate_form"])
        self.assertEqual(rows["woi"]["candidate_form"], "mu-si-ka")
        self.assertEqual(rows["woi"]["research_status"], "draft_needs_evidence")
        self.assertEqual(rows["bon"]["research_status"], "needs_proposal")

    def test_queue_must_match_canonical_and_not_duplicate_root_meanings(self):
        with self.assertRaises(VekaError):
            build_root_inventory(self.lex, self.queue + [dict(self.queue[0], concept_id="NEW")])
        with self.assertRaises(VekaError):
            build_root_inventory(self.lex, [dict(self.queue[0], gloss="banana")])

    def test_scenario_weighting_is_explicit_comparative_and_never_authorizes_changes(self):
        rows = [
            scenario("C002", "core", "woi", recognition=20),
            scenario("C002", "candidate", "mu-si-ka", recognition=90),
        ]
        result = compare_scenarios(rows, self.lex, self.queue)
        item = result["comparisons"][0]
        self.assertEqual(item["concept_id"], "C002")
        self.assertEqual(item["delta_points"], 24.5)
        self.assertEqual(result["weights_percent"], WEIGHTS)
        self.assertEqual(item["research_gate"], "scenario_only")
        self.assertFalse(result["human_benefit_established"])
        self.assertFalse(result["adoption_authorized"])

    def test_critical_errors_block_candidate_even_if_weighted_scenario_wins(self):
        rows = [
            scenario("C002", "core", "woi", recognition=20),
            scenario("C002", "candidate", "mu-si-ka", recognition=95, critical="1"),
        ]
        item = compare_scenarios(rows, self.lex, self.queue)["comparisons"][0]
        self.assertEqual(item["research_gate"], "critical_error_review")
        self.assertGreater(item["delta_points"], 0)

    def test_incomplete_invalid_or_unverified_scenarios_fail_closed(self):
        core = scenario("C002", "core", "woi")
        candidate = scenario("C002", "candidate", "mu-si-ka")
        for broken in [
            [candidate], [core, core], [core, dict(candidate, form="da-ta")],
            [core, dict(candidate, recognition_acquisition="101")],
            [core, dict(candidate, semantic_clarity="NaN")],
            [core, dict(candidate, critical_error_count="-1")],
            [core, dict(candidate, scenario_note="")],
            [core, dict(candidate, concept_id="C999")],
        ]:
            with self.subTest(broken=broken), self.assertRaises(VekaError):
                compare_scenarios(broken, self.lex, self.queue)

    def test_no_scenarios_means_no_scored_hypotheses(self):
        result = compare_scenarios([], self.lex, self.queue)
        self.assertEqual(result["comparisons"], [])
        self.assertFalse(result["evidence_observed"])
        self.assertFalse(result["adoption_authorized"])

    def test_cli_exports_inventory_and_accepts_an_opt_in_scenario_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "roots.json"
            bare = subprocess.run([sys.executable, "-m", "veka", "root-research",
                                   "--output", str(out)], cwd=ROOT, text=True,
                                  capture_output=True, check=True)
            report = json.loads(bare.stdout)
            self.assertEqual(report["root_inventory"]["canonical_roots"], 317)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), report)
            self.assertEqual(report["scenario_comparison"]["comparisons"], [])
            path = Path(tmp) / "scenarios.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=tuple(scenario(
                    "C002", "core", "woi").keys()))
                writer.writeheader()
                writer.writerows([
                    scenario("C002", "core", "woi"),
                    scenario("C002", "candidate", "mu-si-ka")])
            scored = subprocess.run([sys.executable, "-m", "veka", "root-research",
                                     "--scenarios", str(path)], cwd=ROOT, text=True,
                                    capture_output=True, check=True)
            self.assertEqual(len(json.loads(scored.stdout)["scenario_comparison"]["comparisons"]), 1)
            self.assertEqual(len(read_scenarios(path)), 2)

    def test_scenario_csv_rejects_undeclared_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong.csv"
            path.write_text("concept_id,score\nC002,99\n", encoding="utf-8")
            with self.assertRaises(VekaError):
                read_scenarios(path)


if __name__ == "__main__":
    unittest.main()
