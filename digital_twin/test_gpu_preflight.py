import unittest
from digital_twin.gpu_preflight import estimate


class BudgetTests(unittest.TestCase):
    def test_under_cap(self):
        report = estimate(0.4, 1, 26000, 200000)
        self.assertTrue(report["within_cap"])
        self.assertEqual(report["projected_vnd"], 10400)

    def test_over_cap(self):
        self.assertFalse(estimate(3, 4, 26000, 200000)["within_cap"])

    def test_invalid_rate(self):
        with self.assertRaises(ValueError):
            estimate(1, 1, 0, 200000)


if __name__ == "__main__":
    unittest.main()
