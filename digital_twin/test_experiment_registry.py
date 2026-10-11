"""CPU-only checks for comparable avatar experiments."""
import unittest

from digital_twin.experiment_registry import build_record, compare


class ExperimentRegistryTests(unittest.TestCase):
    def test_compare_same_assets(self):
        scores = dict.fromkeys((
            "identity", "vietnamese_lip_sync", "mouth_teeth",
            "temporal_stability", "natural_motion", "body_preservation"), 5)
        a = build_record("e1", "musetalk-v1.5", "source", "audio",
                         10, 2, 1000, scores)
        b = build_record("e2", "heygen-authorized-reference", "source",
                         "audio", 10, 0, 0, scores)
        result = compare([a, b])
        self.assertEqual(result["reviewed_count"], 2)
        self.assertEqual(result["ranked"][0]["model"], "heygen-authorized-reference")

    def test_reject_different_audio(self):
        a = build_record("e1", "musetalk-v1.5", "source", "audio1", 10, 1, 100)
        b = build_record("e2", "musetalk-v1.5", "source", "audio2", 10, 1, 100)
        with self.assertRaises(ValueError):
            compare([a, b])

    def test_unreviewed_is_not_ranked(self):
        a = build_record("e1", "musetalk-v1.5", "source", "audio", 10, 1, 100)
        b = build_record("e2", "reference-conditioned-research",
                         "source", "audio", 10, 1, 100)
        self.assertEqual(compare([a, b])["ranked"], [])

    def test_reject_negative_cost(self):
        with self.assertRaises(ValueError):
            build_record("e1", "musetalk-v1.5", "source", "audio", 10, 1, -1)


if __name__ == "__main__":
    unittest.main()
