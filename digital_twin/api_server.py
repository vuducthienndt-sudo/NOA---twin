"""NOA Digital Twin minimal API prototype (stdlib, no GPU, no media uploads).

Start: NOA_API_TOKEN=... python -m digital_twin.api_server
Security: bind localhost by default; use an authenticated reverse proxy for
any public deployment. In-memory jobs are lost on restart.
"""
from __future__ import annotations

import hmac
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

JOBS: dict[str, dict] = {}
MAX_BODY = 16 * 1024
ALLOWED_PURPOSES = {"studio", "person"}
ALLOWED_MODELS = {"musetalk-v1.5"}


def validate_job(body: object) -> dict:
    if not isinstance(body, dict):
        raise ValueError("JSON object required")
    for field in ("source_asset_id", "speech_asset_id", "consent_record_id"):
        value = body.get(field)
        if not isinstance(value, str) or not (1 <= len(value) <= 128):
            raise ValueError(f"Invalid {field}")
    if body.get("purpose") not in ALLOWED_PURPOSES:
        raise ValueError("Invalid purpose")
    if body.get("model") not in ALLOWED_MODELS:
        raise ValueError("Unsupported model")
    output = body.get("output", {})
    if not isinstance(output, dict):
        raise ValueError("Invalid output")
    duration = output.get("max_seconds", 10)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 0 < duration <= 10:
        raise ValueError("max_seconds must be between 0 and 10")
    if output.get("aspect_ratio", "9:16") not in {"9:16", "16:9", "1:1"}:
        raise ValueError("Unsupported aspect_ratio")
    return {
        "source_asset_id": body["source_asset_id"],
        "speech_asset_id": body["speech_asset_id"],
        "consent_record_id": body["consent_record_id"],
        "purpose": body["purpose"],
        "model": body["model"],
        "output": {"max_seconds": duration,
                   "aspect_ratio": output.get("aspect_ratio", "9:16")},
    }


class Handler(BaseHTTPRequestHandler):
    def reply(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self) -> bool:
        expected = os.environ.get("NOA_API_TOKEN", "")
        provided = self.headers.get("Authorization", "")
        if not expected or not hmac.compare_digest(provided, f"Bearer {expected}"):
            self.reply(401, {"error": "unauthorized"})
            return False
        return True

    def do_POST(self) -> None:
        if not self.authorized():
            return
        path = urlsplit(self.path).path
        if path == "/v1/jobs":
            try:
                length = int(self.headers.get("Content-Length", "-1"))
                if not 0 <= length <= MAX_BODY:
                    self.reply(413, {"error": "invalid body size"})
                    return
                body = json.loads(self.rfile.read(length))
                job = validate_job(body)
            except (ValueError, json.JSONDecodeError) as exc:
                self.reply(400, {"error": str(exc)})
                return
            job_id = "job_" + secrets.token_hex(12)
            JOBS[job_id] = {"job_id": job_id, "status": "queued",
                            "request": job, "human_review_required": True}
            self.reply(202, {"job_id": job_id, "status": "queued",
                             "status_url": f"/v1/jobs/{job_id}"})
            return
        if path.startswith("/v1/jobs/") and path.endswith("/cancel"):
            job_id = path[len("/v1/jobs/"):-len("/cancel")].strip("/")
            job = JOBS.get(job_id)
            if job is None:
                self.reply(404, {"error": "not_found"})
                return
            if job["status"] in {"completed", "failed", "cancelled"}:
                self.reply(409, {"error": "terminal_job"})
                return
            job["status"] = "cancelled"
            self.reply(200, {"job_id": job_id, "status": "cancelled"})
            return
        self.reply(404, {"error": "not_found"})

    def do_GET(self) -> None:
        if not self.authorized():
            return
        path = urlsplit(self.path).path
        if path == "/health":
            self.reply(200, {"service": "noa-digital-twin", "status": "prototype"})
            return
        if path.startswith("/v1/jobs/"):
            parts = path.strip("/").split("/")
            if len(parts) < 3 or parts[:2] != ["v1", "jobs"]:
                self.reply(404, {"error": "not_found"})
                return
            job = JOBS.get(parts[2])
            if job is None:
                self.reply(404, {"error": "not_found"})
                return
            if len(parts) == 3:
                self.reply(200, job)
                return
            if len(parts) == 4 and parts[3] == "quality":
                self.reply(200, {"job_id": parts[2], "status": job["status"],
                                 "human_review_required": True,
                                 "metrics": None})
                return
            if len(parts) == 4 and parts[3] == "result":
                self.reply(409, {"error": "render_not_implemented"})
                return
        self.reply(404, {"error": "not_found"})


def main() -> None:
    if not os.environ.get("NOA_API_TOKEN"):
        raise SystemExit("Set NOA_API_TOKEN to a secret value before starting")
    host = os.environ.get("NOA_API_HOST", "127.0.0.1")
    port = int(os.environ.get("NOA_API_PORT", "8765"))
    print(f"NOA Digital Twin API prototype listening on {host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
