# NOA Digital Twin V1 — identity-first test harness

This module is **isolated from the existing realtime NOA Person application**.
It prepares real-person video for an audio-driven lip-sync experiment without
changing the source person's eye, hair, hand or body motion.

## Goal

- Consented real human; no invented KOL.
- 10-second talking-head output.
- Identity fidelity and Vietnamese voice fidelity take priority over gesture generation.
- Monthly spending cap: 1,000,000 VND; initial GPU test cap: 200,000 VND.
- No GPU purchase before a successful comparison.

## Prepare a test (free, local, CPU)

Install FFmpeg (including ffprobe) and Python 3.10+.

```bash
python digital_twin/prepare.py --video samples/person.mp4 --audio samples/speech.wav --out outputs/test01 --seconds 10 --start 0 --consent
```

Outputs:

- `source_25fps.mp4`: **original real frames** and real body motion; no synthesized face
- `speech_16k.wav`: new authorized speech, 16kHz mono PCM
- `reference_frame.jpg`: reference for side-by-side evaluation
- `manifest.json`: input paths and preparation status

The audio file must already contain the desired speech. This module **does not
clone voices** and **does not run MuseTalk yet**. Do not describe prepared files
as an AI-rendered video.

## GPU experiment — next integration

1. Set up the **official MuseTalk 1.5 repository** on a rented CUDA GPU.
2. Download weights following its current official instructions and license.
3. Feed `source_25fps.mp4` and `speech_16k.wav` into its inference entrypoint.
4. Preserve original frames outside the generated face/mouth region when possible.
5. Compare output against original source in a blind review for identity, teeth,
   eye stability, mouth sync and temporal flicker.
6. Record actual GPU time, cost and failed renders. Stop before spending 200,000 VND.

Official project: https://github.com/TMElyralab/MuseTalk

**Important:** model inference flags and weight paths are version-dependent;
verify against the checked-out MuseTalk revision before adding an executable adapter.
The current code is preparation-only, not a claim of HeyGen-equivalent quality.

## Data safety

Obtain explicit consent for the person's likeness and voice. Keep sample footage
out of public repositories; do not commit `samples/` or `outputs/`.

## MuseTalk 1.5 adapter (added)

Clone the official MuseTalk project **separately** and install its dependencies
following the upstream README. Do not add model weights to this Git repository.

```bash
# Prepare a config and command without using GPU:
python digital_twin/run_musetalk.py --manifest outputs/test01/manifest.json --musetalk-dir /path/to/MuseTalk --out outputs/test01/musetalk

# Only after verifying the plan, dependencies, GPU price and consent:
python digital_twin/run_musetalk.py --manifest outputs/test01/manifest.json --musetalk-dir /path/to/MuseTalk --out outputs/test01/musetalk --execute
```

The adapter copies the official `configs/inference/test.yaml`, replaces
`video_path` and `audio_path`, and invokes `python -m scripts.inference`
with the MuseTalk 1.5 model paths. It does **not** download models or rent GPU.
Upstream configuration layouts can change; inspect `noa_test.yaml` before
executing. This has not yet been tested with real GPU inference.

## HeyGen research integration

See [HEYGEN_RESEARCH.md](HEYGEN_RESEARCH.md) for sourced architecture notes
and a precise separation between published HeyGen methods and our own code.

Select sharp, temporally diverse reference frames on CPU:

```bash
pip install -r digital_twin/requirements-references.txt
python digital_twin/select_references.py --video outputs/test01/source_25fps.mp4 --out outputs/test01/references --count 8
```

This is a reference-selection **preprocessing** utility. The current MuseTalk
adapter does not consume these selected images; they are for inspection and
future identity-conditioning experiments. It is not Sparse Reference Attention.

## Automated preservation QA

After a MuseTalk render, compare source and generated videos (same resolution,
FPS and frame count required):

```bash
python digital_twin/quality_check.py \
  --source outputs/test01/source_25fps.mp4 \
  --rendered outputs/test01/musetalk/results/your_output.mp4 \
  --out outputs/test01/qa.json \
  --mouth-box 0.30 0.48 0.40 0.20
```

Adjust the **normalized mouth box** for the actual speaker framing.
The quality gate measures mean absolute pixel differences **outside** this box
and excess frame-to-frame change outside it. Thresholds are preliminary,
not validated against commercial output. This is *not* biometric identity
verification, lip-sync scoring, voice similarity scoring or face tracking.

CPU-only synthetic smoke tests:

```bash
python -m unittest digital_twin.test_quality_check
```

Passing QA is not enough to publish; review the face, teeth, voice, lip-sync
and original footage rights manually.

## Human-review contact sheet

After rendering, generate an original-vs-AI side-by-side comparison image:

```bash
python digital_twin/visual_review.py \
  --source outputs/test01/source_25fps.mp4 \
  --rendered /path/to/rendered.mp4 \
  --out outputs/test01/contact_sheet.jpg \
  --samples 8
```

The contact sheet shows 8 time-aligned samples: source left, AI right.
Review eyes, teeth, mouth, jaw, hairline and background for drift. This
does not validate Vietnamese speech synchronization, voice fidelity or
identity automatically. Use `python -m unittest discover -s digital_twin
-p 'test_*.py' -v` for CPU tests.

## Standalone HTTP API prototype

Install and run **locally only**:

```bash
pip install -r digital_twin/requirements-api.txt
export NOA_TWIN_API_KEY="replace-with-a-long-random-secret"
uvicorn digital_twin.service:app --host 127.0.0.1 --port 8787
```

Create a queued request (not rendered):

```bash
curl -X POST http://127.0.0.1:8787/v1/jobs \
  -H "Authorization: Bearer $NOA_TWIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"source_asset_id":"video1","speech_asset_id":"audio1","consent_record_id":"consent1","purpose":"studio"}'
```

This is a **nonproduction prototype**. Jobs are stored in SQLite (default `digital_twin/outputs/jobs.sqlite3`)
and survive server restarts; set `NOA_TWIN_DB_PATH` to override. Consent identifiers are accepted but not yet
validated against an authoritative consent store; asset identifiers are
not yet resolved to private media. There is no background worker, no
GPU, no persistence, no user-scoped authorization, and no rendered output.
Do not expose it publicly or connect real customer traffic. For the
intended contract, see `API_CONTRACT.md`.

## Manual single-job worker

Run `python -m digital_twin.worker_once --help` for options. It defaults to dry-run and checks the SQLite job, prepared manifest, consent record and estimated GPU budget. `--execute` calls the MuseTalk adapter only on an already provisioned GPU machine. It does not provision/stop cloud GPUs, enforce provider billing caps, verify consent authenticity, persist render completion, or verify output existence. Do not use with real customer media until those controls are implemented.

Each manual Worker invocation now uses a job-specific MuseTalk output directory under `digital_twin/outputs/<job_id>/musetalk/`. A fresh MP4 with a decodable video stream moves the task only to `quality_review`, not `completed`. The worker process timeout does not stop billing at the GPU provider; review the video manually and terminate the rented machine separately.

## First real 10-second pilot: CPU media gate

On a machine with FFprobe installed, inspect the **authorized** input
video and target audio before preparing MuseTalk inputs:

`python -m digital_twin.pilot_media_check --video private/source.mp4 --audio private/speech.wav --out private/pilot_media_report.json`

The tool checks stream presence, durations (up to 60 seconds), minimum
video dimensions, sample rate and audio/video duration alignment. It
does **not** verify consent, measure lip sync, or start a GPU. A passing
report only means the media is technically plausible as a pilot input.
Avoid committing private media, voice recordings or consent documents.
