"""Tests for the human review quality gate."""
import unittest

from digital_twin.heygen_scorecard import evaluate


class HeygenScorecardTests(unittest.TestCase):
    def test_perfect_scores_pass(self):
        scores = {
            "identity": 5, "vietnamese_lip_sync": 5, "mouth_teeth": 5,
            "temporal_stability": 5, "natural_motion": 5,
            "body_preservation": 5,
        }
        self.assertEqual(evaluate(scores)["review_gate"], "candidate_pass")
        self.assertEqual(evaluate(scores)["weighted_score_out_of_5"], 5)

    def test_identity_failure_blocks_high_average(self):
        scores = {
            "identity": 2, "vietnamese_lip_sync": 5, "mouth_teeth": 5,
            "temporal_stability": 5, "natural_motion": 5,
            "body_preservation": 5,
        }
        result = evaluate(scores)
        self.assertEqual(result["review_gate"], "needs_improvement")
        self.assertIn("identity", result["below_minimum"])

    def test_missing_score_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"identity": 5})

    def test_fraction_rejected(self):
        scores = dict.fromkeys((
            "identity", "vietnamese_lip_sync", "mouth_teeth",
            "temporal_stability", "natural_motion", "body_preservation"), 5)
        scores["identity"] = 4.5
        with self.assertRaises(ValueError):
            evaluate(scores)


if __name__ == "__main__":
    unittest.main()
