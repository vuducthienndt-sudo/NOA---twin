# NOA Digital Twin — independent service API contract (v0.1)

NOA Digital Twin is a **separate service** consumed by NOA Studio and NOA Person.
This file is an interface specification, not a deployed API.

## Responsibility boundaries

- Digital Twin owns consent metadata, video/audio preprocessing, rendering,
  QA reports, model versions, and GPU job execution.
- NOA Studio owns scripts, scene editing, publishing, and output timelines.
- NOA Person owns conversations, real-time sessions and its client UI.
- Both products call Digital Twin through authenticated HTTP endpoints.
- Do not embed MuseTalk or other GPU dependencies in Next.js web servers.

## Proposed REST endpoints (not implemented yet)

`POST /v1/jobs`: create an asynchronous render job.

Request example:

```json
{
  "source_asset_id": "asset_video_001",
  "speech_asset_id": "asset_audio_001",
  "model": "musetalk-v1.5",
  "consent_record_id": "consent_001",
  "purpose": "studio",
  "output": {"aspect_ratio": "9:16", "max_seconds": 10}
}
```

Response: HTTP 202

```json
{
  "job_id": "job_001",
  "status": "queued",
  "status_url": "/v1/jobs/job_001"
}
```

`GET /v1/jobs/{job_id}`: return status:
`queued | preparing | running | quality_review | completed | failed | cancelled`.

`POST /v1/jobs/{job_id}/cancel`: request cancellation; GPU charges may
continue until the provider actually terminates the machine.

`GET /v1/jobs/{job_id}/quality`: return QA measurements and
`human_review_required` (always true for the initial version).

`GET /v1/jobs/{job_id}/result`: return short-lived authenticated download
URL only after completion and authorization.

## Security and safety

- Require explicit, verifiable consent and rights to the source voice/video.
- Store original and generated media in private storage.
- Use short-lived signed upload/download URLs and bearer auth between services.
- Separate authorization for Studio and Person users.
- Apply per-job cost caps, rate limits, audit logs and retention/deletion policies.
- Do not expose internal GPU instance addresses or model weights.
- Label externally published synthetic videos appropriately.
- Reject unauthorized attempts to impersonate other people.

## Implementation phases

1. Run and validate the existing MuseTalk CLI offline.
2. Implement a queue-backed worker with private asset storage.
3. Add REST gateway and job-status persistence.
4. Integrate NOA Studio as first consumer.
5. Add NOA Person only after latency and GPU cost testing.

**Current implementation:** preprocessing, MuseTalk CLI adapter, QA scripts,
CPU tests. The endpoints above are a design contract only.
