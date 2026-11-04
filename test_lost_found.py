"""
Unit tests for the Smart Campus Lost and Found System.
Run:  python -m unittest -v      (or press the Testing flask in VS Code)
"""
import sqlite3
import unittest

import lost_found as lf
from demo import load_sample_data


class LostFoundTests(unittest.TestCase):
    def setUp(self):
        self.con = lf.connect(":memory:")          # temporary database
        self.lost_ids, self.found_ids = load_sample_data(self.con)

    def tearDown(self):
        self.con.close()

    def test_similarity_range(self):
        self.assertEqual(lf.similar("Wallet", "wallet "), 1.0)
        self.assertTrue(0 < lf.similar("Wallet", "Black Wallet") < 1)

    def test_scores_of_the_report(self):
        self.assertEqual(lf.find_matches(self.con, 1), [(1, "Wallet", 82.3)])
        self.assertEqual(lf.find_matches(self.con, 2), [(2, "Water Bottle", 93.4)])

    def test_no_match_below_threshold(self):
        self.assertEqual(lf.find_matches(self.con, 3), [])

    def test_found_outside_14_days_scores_zero(self):
        lost = {"category": "Wallet", "item_name": "Wallet", "color": "Black",
                "location": "Library", "lost_date": "2026-10-01"}
        found = {"category": "Wallet", "item_name": "Wallet", "color": "Black",
                 "location": "Library", "found_date": "2026-10-20"}
        self.assertEqual(lf.match_score(lost, found), 0.0)

    def test_matches_are_saved_only_once(self):
        lf.find_matches(self.con, 1)
        lf.find_matches(self.con, 1)
        n = self.con.execute("SELECT COUNT(*) FROM match_record").fetchone()[0]
        self.assertEqual(n, 1)

    def test_proof_of_ownership(self):
        self.assertTrue(lf.proof_ok("a lion sticker inside", "sticker of a lion inside"))
        self.assertFalse(lf.proof_ok("blue pen", "sticker of a lion inside"))

    def test_verify_and_return(self):
        lf.find_matches(self.con, 1)
        self.assertIn("failed", lf.verify_and_return(self.con, 1, "blue pen", "2026-10-15"))
        self.assertIn("returned", lf.verify_and_return(
            self.con, 1, "lion sticker inside", "2026-10-15"))
        self.assertEqual(lf.summary(self.con)["recovered"], 1)

    def test_foreign_key_is_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            lf.report_lost(self.con, "S999", "Keys", "Keys", "Silver", "Block A", "2026-10-20")


if __name__ == "__main__":
    unittest.main()
