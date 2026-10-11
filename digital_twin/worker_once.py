"""Manual, fail-closed single-job runner for NOA Digital Twin.

Default: preflight only. This does not provision or stop a cloud GPU.
Run only on a manually provisioned GPU host with MuseTalk installed.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from digital_twin import job_store
from digital_twin.worker_preflight import check_job


def plan_job(job_id: str, manifest: Path, consent: Path,
             musetalk_dir: Path, hourly_usd: float,
             usd_vnd: float, max_minutes: float,
             cap_vnd: float) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise ValueError("Unknown job")
    estimate = check_job(job, manifest, consent, hourly_usd,
                         usd_vnd, max_minutes, cap_vnd)
    return {
        **estimate,
        "mode": "dry-run",
        "musetalk_dir": str(musetalk_dir.resolve()),
        "manifest": str(manifest.resolve()),
        "command": [
            sys.executable, "-m", "digital_twin.run_musetalk",
            "--manifest", str(manifest.resolve()),
            "--musetalk-dir", str(musetalk_dir.resolve()),
            "--out", str((Path("digital_twin/outputs") / job_id / "musetalk").resolve()),
            "--execute",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--job-id", required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--consent", type=Path, required=True)
    p.add_argument("--musetalk-dir", type=Path, required=True)
    p.add_argument("--hourly-usd", type=float, required=True)
    p.add_argument("--usd-vnd", type=float, required=True)
    p.add_argument("--max-minutes", type=float, required=True)
    p.add_argument("--cap-vnd", type=float, default=200000)
    p.add_argument("--execute", action="store_true",
                   help="Explicitly invoke MuseTalk on this machine")
    a = p.parse_args()
    plan = plan_job(a.job_id, a.manifest, a.consent, a.musetalk_dir,
                    a.hourly_usd, a.usd_vnd, a.max_minutes, a.cap_vnd)
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if not a.execute:
        print("DRY RUN: MuseTalk not started")
        return
    if not a.musetalk_dir.is_dir():
        p.error("MuseTalk checkout does not exist")
    # Claim exactly once; concurrent workers cannot execute the same job.
    if not job_store.transition(a.job_id, "queued", "running"):
        p.error("Job was already claimed, cancelled, or is no longer queued")
    timeout_seconds = max(1, int(a.max_minutes * 60))
    started_at = time.time()
    try:
        # Start a process group on POSIX so timeout can stop subprocesses too.
        kwargs = {"start_new_session": True} if os.name == "posix" else {}
        proc = subprocess.Popen(plan["command"], **kwargs)
        try:
            return_code = proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
            proc.wait()
            raise RuntimeError("Render exceeded local execution timeout")
        if return_code != 0:
            raise RuntimeError(f"MuseTalk adapter exited with code {return_code}")
        # MuseTalk catches task errors internally; verify output independently.
        # The adapter writes under outputs/test01/musetalk/results/v15 by default.
        # A fresh result is required to prevent accepting a stale video.
        output_dir = Path(plan["command"][-2]) / "results"
        videos = [
            item for item in output_dir.rglob("*.mp4")
            if item.stat().st_mtime >= started_at
            and item.stat().st_size > 1024
        ]
        if not videos:
            raise RuntimeError("No fresh non-empty MuseTalk video was produced")
        import shutil
        if shutil.which("ffprobe") is None:
            raise RuntimeError("ffprobe is required to verify output")
        valid = []
        for item in videos:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height",
                 "-of", "json", str(item)],
                capture_output=True, text=True, check=False,
            )
            if probe.returncode == 0:
                streams = json.loads(probe.stdout).get("streams", [])
                if streams and streams[0].get("width", 0) > 0 and streams[0].get("height", 0) > 0:
                    valid.append(item)
        if not valid:
            raise RuntimeError("No valid video stream found in fresh outputs")
        videos = valid
        job_store.transition(a.job_id, "running", "quality_review")
        print(json.dumps({"job_id": a.job_id, "status": "quality_review",
                          "candidate_videos": [str(v) for v in videos]},
                         ensure_ascii=False))
    except BaseException:
        job_store.transition(a.job_id, "running", "failed")
        raise


if __name__ == "__main__":
    main()
