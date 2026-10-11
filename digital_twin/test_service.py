"""API smoke tests; skipped if optional API packages are not installed."""
import os
import tempfile
from pathlib import Path
import unittest

try:
    from fastapi.testclient import TestClient
    from digital_twin.service import app
except ImportError:
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "Install requirements-api.txt")
class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_db = os.environ.get("NOA_TWIN_DB_PATH")
        os.environ["NOA_TWIN_DB_PATH"] = str(Path(self.tmp.name) / "jobs.sqlite3")
        os.environ["NOA_TWIN_API_KEY"] = "test-secret"
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer test-secret"}

    def tearDown(self):
        os.environ.pop("NOA_TWIN_API_KEY", None)
        if self.original_db is None:
            os.environ.pop("NOA_TWIN_DB_PATH", None)
        else:
            os.environ["NOA_TWIN_DB_PATH"] = self.original_db
        self.tmp.cleanup()

    def test_auth_and_job_lifecycle(self):
        body = {
            "source_asset_id": "video1",
            "speech_asset_id": "audio1",
            "consent_record_id": "consent1",
            "purpose": "studio",
        }
        self.assertEqual(self.client.post("/v1/jobs", json=body).status_code, 401)
        result = self.client.post("/v1/jobs", json=body, headers=self.headers)
        self.assertEqual(result.status_code, 202)
        job_id = result.json()["job_id"]
        self.assertEqual(
            self.client.get(f"/v1/jobs/{job_id}", headers=self.headers).json()["status"],
            "queued",
        )
        self.assertEqual(
            self.client.get(f"/v1/jobs/{job_id}/result", headers=self.headers).status_code,
            409,
        )
        self.assertEqual(
            self.client.post(f"/v1/jobs/{job_id}/cancel", headers=self.headers).json()["status"],
            "cancelled",
        )

    def test_invalid_request(self):
        result = self.client.post(
            "/v1/jobs",
            json={"source_asset_id": "", "speech_asset_id": "a",
                  "consent_record_id": "c", "purpose": "studio"},
            headers=self.headers,
        )
        self.assertEqual(result.status_code, 422)


if __name__ == "__main__":
    unittest.main()
