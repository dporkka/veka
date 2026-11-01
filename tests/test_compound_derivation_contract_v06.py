"""Opt-in Veka 0.6 semantic review contracts; no new canonical words."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from veka.compound_semantics import audit_compound_semantics, load_compound_reviews
from veka.core import VekaError
from veka.extended import derive
from veka.profiles import load_profile

ROOT = Path(__file__).resolve().parents[1]


class CompoundSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_unreviewed_specialized_senses_preserve_canonical_alias_policy(self):
        result = audit_compound_semantics(self.lex)
        self.assertEqual(result["schema_version"], "veka.compound-semantics.v06")
        self.assertEqual(result["total_compounds"], 708)
        self.assertEqual(result["surface_equivalent_count"], 708)
        self.assertEqual(result["canonical_structural_policy"], "compositional_alias")
        self.assertEqual(result["unreviewed_count"], 708)
        self.assertEqual(result["reviewed_count"], 0)
        self.assertFalse(result["human_listening_validated"])
        self.assertFalse(result["canonical_lexicon_modified"])
        match = next(row for row in result["items"] if row["compound"] == "ren-sak")
        self.assertEqual(match["spoken_form"], "ren sak")
        self.assertEqual(match["phrase_gloss"], "knowledgeable person")
        self.assertEqual(match["dictionary_gloss"], "expert")
        self.assertEqual(match["classification"], "unreviewed")
        self.assertTrue(match["distinct_meaning_unverified"])

    def test_review_rows_are_explicit_editorial_not_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.csv"
            path.write_text(
                "compound,classification,evidence_note\n"
                "ren-sak,potential_lexicalization,expert may denote specialized knowledge\n"
            )
            review = load_compound_reviews(path, self.lex)
        result = audit_compound_semantics(self.lex, review)
        self.assertEqual(result["reviewed_count"], 1)
        self.assertEqual(result["unreviewed_count"], 707)
        entry = next(x for x in result["items"] if x["compound"] == "ren-sak")
        self.assertEqual(entry["classification"], "potential_lexicalization")
        self.assertTrue(entry["requires_context_for_distinct_meaning"])
        self.assertTrue(entry["distinct_meaning_unverified"])
        self.assertFalse(entry["human_listening_validated"])

    def test_compositional_alias_remains_spoken_equivalence_not_new_lexeme(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.csv"
            path.write_text(
                "compound,classification,evidence_note\n"
                "ren-sak,compositional_alias,interpret expert as knowledgeable person\n"
            )
            reviews = load_compound_reviews(path, self.lex)
        result = audit_compound_semantics(self.lex, reviews)
        entry = next(x for x in result["items"] if x["compound"] == "ren-sak")
        self.assertFalse(entry["requires_context_for_distinct_meaning"])
        self.assertFalse(entry["distinct_meaning_unverified"])
        self.assertEqual(self.lex["ren-sak"].gloss, "expert")
        self.assertEqual(len(self.lex), 1025)

    def test_malformed_review_csv_fails_closed(self):
        rows = [
            "ren-sak,unknown_class,different meaning",
            "ren-sak,potential_lexicalization,",
            "ren-sak,compositional_alias,interpretation\nren-sak,compositional_alias,duplicated",
            "ren,potential_lexicalization,not compound",
            "fake-sak,potential_lexicalization,unknown compound",
        ]
        for row in rows:
            with self.subTest(row=row), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "review.csv"
                path.write_text("compound,classification,evidence_note\n" + row + "\n")
                with self.assertRaises(VekaError):
                    load_compound_reviews(path, self.lex)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.csv"
            path.write_text("compound,status\nren-sak,compositional_alias\n")
            with self.assertRaises(VekaError):
                load_compound_reviews(path, self.lex)

    def test_toneless_profile_is_equivalent_and_review_is_not_mutation(self):
        alt = load_profile("toneless")
        result = audit_compound_semantics(alt)
        self.assertEqual(result["surface_equivalent_count"], 708)
        self.assertEqual(result["unreviewed_count"], 708)

    def test_cli_compound_review_emits_research_only_json(self):
        run = subprocess.run(
            [sys.executable, "-m", "veka", "compound-semantics", "--top", "1"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["surface_equivalent_count"], 708)
        self.assertEqual(len(report["items"]), 1)
        self.assertFalse(report["human_listening_validated"])

    def test_cli_review_csv_and_full_export_uses_same_editorial_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            review = directory / "review.csv"
            output = directory / "all_compounds.json"
            review.write_text(
                "compound,classification,evidence_note\n"
                "ren-sak,potential_lexicalization,expert may be a conventional title\n"
            )
            run = subprocess.run(
                [sys.executable, "-m", "veka", "compound-semantics",
                 "--review-file", str(review), "--top", "1",
                 "--output", str(output)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            preview = json.loads(run.stdout)
            exported = json.loads(output.read_text())
            self.assertEqual(len(preview["items"]), 1)
            self.assertEqual(len(exported["items"]), 708)
            self.assertEqual(preview["reviewed_count"], 1)
            self.assertEqual(exported["reviewed_count"], 1)
            self.assertFalse(exported["canonical_lexicon_modified"])


class DerivationRoleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lex = load_profile("tonal")

    def test_subject_and_object_nominalizations_differ(self):
        sender = derive("dak-nes", self.lex)["semantic_contract"]
        sent = derive("dak-mol", self.lex)["semantic_contract"]
        self.assertEqual(sender["denoted_role"], "base_subject")
        self.assertEqual(sent["denoted_role"], "base_object")
        self.assertEqual(sender["input_roles"], ["subject", "object"])
        self.assertEqual(sent["input_roles"], ["subject", "object"])

    def test_causative_and_repeat_have_explicit_argument_maps(self):
        cause = derive("gos-vuk", self.lex)["semantic_contract"]
        repeated = derive("dak-koin", self.lex)["semantic_contract"]
        self.assertEqual(cause["output_roles"], ["subject", "object"])
        self.assertEqual(cause["argument_map"], {
            "subject": "causer", "object": "base_subject"
        })
        self.assertEqual(repeated["output_roles"], ["subject", "object"])
        self.assertEqual(repeated["argument_map"], {
            "subject": "base_subject", "object": "base_object"
        })
        self.assertEqual(derive("gos-koin", self.lex)["semantic_contract"]["output_roles"], ["subject"])

    def test_reverse_attempt_does_not_entail_success(self):
        semantic = derive("dak-kas", self.lex)["semantic_contract"]
        self.assertEqual(semantic["event_relation"], "attempt_to_reverse_prior_event")
        self.assertFalse(semantic["success_entails_reversal"])
        self.assertEqual(semantic["output_roles"], ["subject", "object"])

    def test_passive_ability_is_not_assertion_of_event(self):
        semantics = derive("dak-vau", self.lex)["semantic_contract"]
        self.assertEqual(semantics["denoted_role"], "base_object")
        self.assertFalse(semantics["bare_form_asserts_event_occurrence"])
        self.assertEqual(semantics["output_roles"], [])

    def test_invalid_valencies_continue_to_fail(self):
        for word in ("dak-vuk", "gos-mol", "gos-vau", "gos-kas"):
            with self.subTest(word=word), self.assertRaises(VekaError):
                derive(word, self.lex)


if __name__ == "__main__":
    unittest.main()
