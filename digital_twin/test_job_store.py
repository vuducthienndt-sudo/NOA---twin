"""SQLite persistence and cancellation tests."""
import os
import tempfile
import unittest
from pathlib import Path

from digital_twin import job_store


class JobStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = os.environ.get("NOA_TWIN_DB_PATH")
        os.environ["NOA_TWIN_DB_PATH"] = str(Path(self.tmp.name) / "jobs.sqlite3")

    def tearDown(self):
        if self.original is None:
            os.environ.pop("NOA_TWIN_DB_PATH", None)
        else:
            os.environ["NOA_TWIN_DB_PATH"] = self.original
        self.tmp.cleanup()

    def test_atomic_claim(self):
        job = {"job_id": "claim_test", "status": "queued",
               "created_at": "2026-10-11T00:00:00Z", "request": {}}
        job_store.insert(job)
        self.assertTrue(job_store.transition("claim_test", "queued", "running"))
        self.assertFalse(job_store.transition("claim_test", "queued", "running"))
        self.assertTrue(job_store.transition("claim_test", "running", "quality_review"))
        self.assertEqual(job_store.get("claim_test")["status"], "quality_review")

    def test_persistence_and_cancel(self):
        job = {"job_id": "job_test", "status": "queued",
               "created_at": "2026-10-11T00:00:00Z",
               "request": {"purpose": "studio"}}
        job_store.insert(job)
        self.assertEqual(job_store.get("job_test")["request"]["purpose"], "studio")
        self.assertEqual(job_store.cancel("job_test"), "cancelled")
        self.assertEqual(job_store.get("job_test")["status"], "cancelled")
        self.assertIsNone(job_store.cancel("missing"))
        self.assertEqual(job_store.cancel("job_test"), "cancelled")


if __name__ == "__main__":
    unittest.main()
