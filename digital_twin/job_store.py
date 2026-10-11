"""SQLite-backed job records for the NOA Digital Twin API prototype."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

_lock = threading.Lock()


def db_path() -> Path:
    return Path(os.environ.get("NOA_TWIN_DB_PATH", "digital_twin/outputs/jobs.sqlite3"))


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            request_json TEXT NOT NULL
        )
    """)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def insert(job: dict) -> None:
    with _lock, connect() as conn:
        conn.execute(
            "INSERT INTO jobs(job_id, status, created_at, request_json) VALUES(?,?,?,?)",
            (job["job_id"], job["status"], job["created_at"],
             json.dumps(job["request"], ensure_ascii=False)),
        )


def get(job_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    if row is None:
        return None
    return {
        "job_id": row["job_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "request": json.loads(row["request_json"]),
        "human_review_required": True,
        "rendering_enabled": False,
    }


def cancel(job_id: str) -> str | None:
    with _lock, connect() as conn:
        result = conn.execute(
            "UPDATE jobs SET status='cancelled' WHERE job_id=? AND status='queued'",
            (job_id,),
        )
        if result.rowcount == 1:
            return "cancelled"
        row = conn.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return row["status"] if row else None


def transition(job_id: str, expected: str, target: str) -> bool:
    """Atomically change one job state; prevents duplicate worker claims."""
    allowed = {
        ("queued", "running"),
        ("running", "quality_review"),
        ("running", "failed"),
    }
    if (expected, target) not in allowed:
        raise ValueError("Invalid job state transition")
    with _lock, connect() as conn:
        result = conn.execute(
            "UPDATE jobs SET status=? WHERE job_id=? AND status=?",
            (target, job_id, expected),
        )
        return result.rowcount == 1
