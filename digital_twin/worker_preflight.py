"""Validate a consented, bounded GPU render job before any paid execution.

This module does not start a GPU, fetch private media or render a video.
"""
from __future__ import annotations

import json
from pathlib import Path


class PreflightError(ValueError):
    pass


def check_job(job: dict, manifest_path: Path, consent_path: Path,
              hourly_usd: float, usd_vnd: float,
              max_minutes: float, cap_vnd: float = 200000) -> dict:
    if job.get("status") != "queued":
        raise PreflightError("Only queued jobs can be considered")
    request = job.get("request") or {}
    if request.get("model") != "musetalk-v1.5":
        raise PreflightError("Unsupported model")
    if request.get("purpose") not in ("studio", "person"):
        raise PreflightError("Unsupported purpose")
    if not manifest_path.is_file() or not consent_path.is_file():
        raise PreflightError("Manifest and consent evidence must exist")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    consent = json.loads(consent_path.read_text(encoding="utf-8"))
    if consent.get("consent_record_id") != request.get("consent_record_id"):
        raise PreflightError("Consent record mismatch")
    if consent.get("approved") is not True:
        raise PreflightError("Consent must be approved")
    if consent.get("purpose") != request.get("purpose"):
        raise PreflightError("Consent purpose mismatch")
    if consent.get("source_asset_id") != request.get("source_asset_id"):
        raise PreflightError("Source asset mismatch")
    if consent.get("speech_asset_id") != request.get("speech_asset_id"):
        raise PreflightError("Speech asset mismatch")
    if manifest.get("status") != "prepared_not_rendered":
        raise PreflightError("Manifest is not prepared")
    for key in ("source_video", "speech_audio"):
        file = Path(manifest.get(key, ""))
        if not file.is_file():
            raise PreflightError(f"Missing prepared asset: {key}")
    seconds = float(manifest.get("target_seconds", 0))
    requested_seconds = float((request.get("output") or {}).get("max_seconds", 0))
    if seconds <= 0 or seconds > 60 or seconds > requested_seconds:
        raise PreflightError("Prepared duration exceeds job limits")
    if hourly_usd <= 0 or usd_vnd <= 0 or max_minutes <= 0 or cap_vnd <= 0:
        raise PreflightError("Price, FX, duration and cap must be positive")
    estimated_vnd = hourly_usd * usd_vnd * max_minutes / 60
    if estimated_vnd > cap_vnd:
        raise PreflightError(f"Estimated GPU cost {estimated_vnd:.0f} VND exceeds cap")
    return {
        "job_id": job["job_id"],
        "eligible_for_manual_gpu_run": True,
        "estimated_gpu_vnd": round(estimated_vnd),
        "max_minutes": max_minutes,
        "budget_cap_vnd": cap_vnd,
        "warning": "Preflight is not a provider-side spending limit or proof of consent authenticity.",
    }
