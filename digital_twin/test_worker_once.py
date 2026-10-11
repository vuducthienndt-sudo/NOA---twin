"""Tests for single-job worker planning without launching a GPU."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from digital_twin import job_store
from digital_twin.worker_once import plan_job


class WorkerOnceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = os.environ.get("NOA_TWIN_DB_PATH")
        os.environ["NOA_TWIN_DB_PATH"] = str(self.root / "jobs.sqlite3")
        (self.root / "video.mp4").write_bytes(b"test")
        (self.root / "audio.wav").write_bytes(b"test")
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({
            "status": "prepared_not_rendered",
            "source_video": str(self.root / "video.mp4"),
            "speech_audio": str(self.root / "audio.wav"),
            "target_seconds": 10,
        }))
        self.consent = self.root / "consent.json"
        self.consent.write_text(json.dumps({
            "consent_record_id": "consent_1", "approved": True,
            "purpose": "studio", "source_asset_id": "video_1",
            "speech_asset_id": "audio_1",
        }))
        job_store.insert({
            "job_id": "job_1", "status": "queued", "created_at": "2026-10-11",
            "request": {
                "model": "musetalk-v1.5", "purpose": "studio",
                "source_asset_id": "video_1", "speech_asset_id": "audio_1",
                "consent_record_id": "consent_1",
                "output": {"max_seconds": 10},
            },
        })

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop("NOA_TWIN_DB_PATH", None)
        else:
            os.environ["NOA_TWIN_DB_PATH"] = self.old_db
        self.tmp.cleanup()

    def test_plan_no_execution(self):
        result = plan_job("job_1", self.manifest, self.consent,
                          self.root / "musetalk", 0.5, 26000, 20, 200000)
        self.assertEqual(result["mode"], "dry-run")
        self.assertEqual(result["command"][-1], "--execute")
        self.assertIn("job_1", result["command"][-2])
        self.assertEqual(job_store.get("job_1")["status"], "queued")

    def test_missing_job(self):
        with self.assertRaises(ValueError):
            plan_job("unknown", self.manifest, self.consent,
                     self.root / "musetalk", 0.5, 26000, 20, 200000)


if __name__ == "__main__":
    unittest.main()
