"""Source-backed, not-yet-reviewed loanword leads remain hypotheses."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from veka.core import Lexicon
from veka.global_comprehension import (
    EVIDENCE_FIELDS, read_global_csv, audit_global_candidates,
)
from veka.international import read_candidates

BASE = Path(__file__).resolve().parents[1]
LEADS = BASE / "data/global_music_leads_v07.csv"


class MusicLeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexicon = Lexicon.from_csv(BASE / "data/lexicon.csv")
        cls.candidates = read_candidates(BASE / "data/international_candidates_v04.csv")

    def test_evidence_is_explicitly_unreviewed_even_with_public_sources(self):
        rows = read_global_csv(LEADS, EVIDENCE_FIELDS)
        self.assertEqual(len(rows), 5)
        self.assertEqual({r["concept_id"] for r in rows}, {"C002"})
        self.assertEqual({r["candidate_form"] for r in rows}, {"mu-si-ka"})
        self.assertEqual({r["attestation_verified"] for r in rows}, {"no"})
        self.assertEqual({r["semantic_equivalent"] for r in rows}, {"unknown"})
        self.assertEqual(len({r["language_family"] for r in rows}), 5)
        self.assertTrue(all(r["source_url"].startswith("https://") for r in rows))

    def test_evidence_review_queue_keeps_sources_but_does_not_count_cognates(self):
        rows = read_global_csv(LEADS, EVIDENCE_FIELDS)
        audit = audit_global_candidates(self.candidates, self.lexicon, rows)
        self.assertEqual(audit["evidence_records"], 5)
        self.assertEqual(audit["pending_review_records"], 5)
        self.assertEqual(audit["verified_attestations"], 0)
        self.assertEqual(audit["candidates"]["C002"]["verified_families"], 0)
        self.assertEqual(len(audit["review_queue"]), 5)
        self.assertEqual({r["attestation_verified"] for r in audit["review_queue"]}, {"no"})
        self.assertTrue(all(r["source_url"].startswith("https://") for r in audit["review_queue"]))
        self.assertFalse(audit["recognition_measured"])
        self.assertFalse(audit["eligible_for_adoption"])

    def test_cli_shows_unreviewed_sources_not_measured_readability(self):
        proc = subprocess.run([
            sys.executable, "-m", "veka", "global-audit",
            "--evidence", str(LEADS),
        ], cwd=BASE, capture_output=True, text=True, check=True)
        audit = json.loads(proc.stdout)
        self.assertEqual(audit["pending_review_records"], 5)
        self.assertEqual(audit["verified_attestations"], 0)
        self.assertFalse(audit["recognition_measured"])


if __name__ == "__main__":
    unittest.main()
