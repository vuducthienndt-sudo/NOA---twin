"""CPU-only API contract validation tests."""
import unittest
from digital_twin.api_server import validate_job


def request():
    return {
        "source_asset_id": "video1",
        "speech_asset_id": "audio1",
        "consent_record_id": "consent1",
        "purpose": "studio",
        "model": "musetalk-v1.5",
        "output": {"max_seconds": 10, "aspect_ratio": "9:16"},
    }


class ApiContractTests(unittest.TestCase):
    def test_valid_job(self):
        self.assertEqual(validate_job(request())["purpose"], "studio")

    def test_requires_consent_reference(self):
        job = request()
        job.pop("consent_record_id")
        with self.assertRaises(ValueError):
            validate_job(job)

    def test_limits_duration(self):
        job = request()
        job["output"]["max_seconds"] = 60
        with self.assertRaises(ValueError):
            validate_job(job)

    def test_rejects_unknown_model(self):
        job = request()
        job["model"] = "untrusted"
        with self.assertRaises(ValueError):
            validate_job(job)


if __name__ == "__main__":
    unittest.main()
