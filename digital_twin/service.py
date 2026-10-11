"""NOA Digital Twin standalone API prototype.

Install: pip install fastapi uvicorn
Run: NOA_TWIN_API_KEY=<secret> uvicorn digital_twin.service:app --host 127.0.0.1 --port 8787

This is a job-acceptance prototype: it does NOT execute MuseTalk, download
media, provision GPU, or produce synthetic videos.
"""
from __future__ import annotations

import hmac
import os
import uuid
from datetime import datetime, timezone
from typing import Literal

from digital_twin import job_store

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(title="NOA Digital Twin", version="0.1.0")


def authorize(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("NOA_TWIN_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="API key not configured")
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Bearer token required")
    if not hmac.compare_digest(authorization[len(prefix):], expected):
        raise HTTPException(status_code=403, detail="Invalid API token")


class OutputSpec(BaseModel):
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    max_seconds: float = Field(default=10, gt=0, le=60)


class CreateJob(BaseModel):
    source_asset_id: str = Field(min_length=1, max_length=128)
    speech_asset_id: str = Field(min_length=1, max_length=128)
    model: Literal["musetalk-v1.5"] = "musetalk-v1.5"
    consent_record_id: str = Field(min_length=1, max_length=128)
    purpose: Literal["studio", "person"]
    output: OutputSpec = Field(default_factory=OutputSpec)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "rendering_enabled": False}


@app.post("/v1/jobs", status_code=202, dependencies=[Depends(authorize)])
def create_job(request: CreateJob) -> dict:
    job_id = "job_" + uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    job = {
        "job_id": job_id,
        "status": "queued",
        "created_at": now,
        "request": request.model_dump(),
        "human_review_required": True,
        "rendering_enabled": False,
    }
    job_store.insert(job)
    return {"job_id": job_id, "status": "queued",
            "status_url": f"/v1/jobs/{job_id}"}


@app.get("/v1/jobs/{job_id}", dependencies=[Depends(authorize)])
def get_job(job_id: str) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/v1/jobs/{job_id}/cancel", dependencies=[Depends(authorize)])
def cancel_job(job_id: str) -> dict:
    status = job_store.cancel(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if status != "cancelled":
        raise HTTPException(status_code=409, detail="Cannot cancel this job")
    return {"job_id": job_id, "status": "cancelled"}


@app.get("/v1/jobs/{job_id}/quality", dependencies=[Depends(authorize)])
def get_quality(job_id: str) -> dict:
    if job_store.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": "not_available",
            "human_review_required": True}


@app.get("/v1/jobs/{job_id}/result", dependencies=[Depends(authorize)])
def get_result(job_id: str) -> dict:
    if job_store.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    raise HTTPException(status_code=409, detail="No render worker is connected")
