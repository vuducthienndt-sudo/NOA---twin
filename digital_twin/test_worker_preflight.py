"""CPU-only tests of worker fail-closed validation."""
import json
import tempfile
import unittest
from pathlib import Path

from digital_twin.worker_preflight import PreflightError, check_job


class WorkerPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.video = self.root / "source.mp4"
        self.audio = self.root / "speech.wav"
        self.video.write_bytes(b"placeholder")
        self.audio.write_bytes(b"placeholder")
        self.manifest = self.root / "manifest.json"
        self.consent = self.root / "consent.json"
        self.manifest.write_text(json.dumps({
            "status": "prepared_not_rendered",
            "source_video": str(self.video),
            "speech_audio": str(self.audio),
            "target_seconds": 10,
        }))
        self.consent.write_text(json.dumps({
            "consent_record_id": "c1", "approved": True,
            "purpose": "studio", "source_asset_id": "v1",
            "speech_asset_id": "a1",
        }))
        self.job = {
            "job_id": "j1", "status": "queued",
            "request": {
                "model": "musetalk-v1.5", "purpose": "studio",
                "consent_record_id": "c1", "source_asset_id": "v1",
                "speech_asset_id": "a1", "output": {"max_seconds": 10},
            },
        }

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, **kwargs):
        return check_job(self.job, self.manifest, self.consent,
                         hourly_usd=0.5, usd_vnd=26000,
                         max_minutes=20, **kwargs)

    def test_eligible(self):
        result = self.check()
        self.assertTrue(result["eligible_for_manual_gpu_run"])
        self.assertEqual(result["estimated_gpu_vnd"], 4333)

    def test_missing_consent(self):
        self.consent.unlink()
        with self.assertRaises(PreflightError):
            self.check()

    def test_consent_mismatch(self):
        self.job["request"]["consent_record_id"] = "different"
        with self.assertRaises(PreflightError):
            self.check()

    def test_over_budget(self):
        with self.assertRaises(PreflightError):
            self.check(cap_vnd=100)

    def test_not_queued(self):
        self.job["status"] = "cancelled"
        with self.assertRaises(PreflightError):
            self.check()


if __name__ == "__main__":
    unittest.main()
