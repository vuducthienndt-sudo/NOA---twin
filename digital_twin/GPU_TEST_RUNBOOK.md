# NOA Digital Twin — controlled GPU test

## Preconditions

1. Use a video of a person who has explicitly consented to this use.
2. Prepare an authorized Vietnamese speech recording as a WAV file.
3. Confirm actual GPU hourly rate, billing granularity, taxes, storage fees,
   idle charges and cancellation mechanism in the provider's console.
4. Hard first-test spending target: **200,000 VND**, including any extra fees.
5. Stop the GPU instance immediately after output and log collection.

## Workflow

### A. CPU preparation

```bash
python digital_twin/prepare.py --video samples/person.mp4 --audio samples/speech.wav --seconds 10 --out outputs/test01 --consent
pip install -r digital_twin/requirements-references.txt
python digital_twin/select_references.py --video outputs/test01/source_25fps.mp4 --out outputs/test01/references --count 8
```

### B. GPU quote and preflight

The example below uses **illustrative inputs**, not a verified provider price
or live USD/VND exchange rate. Replace them with the actual quote.

```bash
python digital_twin/gpu_preflight.py --hourly-usd 0.40 --hours 1 --vnd-per-usd 26000 --cap-vnd 200000
```

The preflight prints GPU name and free memory if `nvidia-smi` exists.
It does not guarantee the model fits VRAM. A successful budget estimate
does not prevent billing; provider-side limits and prompt shutdown matter.

### C. MuseTalk 1.5 inference

Follow https://github.com/TMElyralab/MuseTalk for exact environment,
dependencies, model downloads and weights. Then:

```bash
python digital_twin/run_musetalk.py --manifest outputs/test01/manifest.json --musetalk-dir /path/to/MuseTalk --out outputs/test01/musetalk
```

Inspect `run_plan.json` and the generated YAML. Only then use `--execute`
with an available GPU. The adapter may need adjustment for the checked-out
MuseTalk revision; do not treat it as validated GPU execution yet.

### D. Output QA

Locate the actual generated MP4, then:

```bash
python digital_twin/quality_check.py --source outputs/test01/source_25fps.mp4 --rendered /path/to/rendered.mp4 --out outputs/test01/qa.json --mouth-box 0.30 0.48 0.40 0.20
```

Check that FPS, resolution and frame counts match. The fixed mouth ROI is
a manual approximation; update it to match the subject. Human inspection
is required for teeth, eyes, voice identity, Vietnamese lip-sync and
temporal stability.

## Report to record

- GPU provider and exact machine type
- Quoted price and actual billed amount
- Input duration and output duration
- Total runtime including setup and failed attempts
- `qa.json` preservation gate
- Human notes: face fidelity, teeth, lip-sync, head/body motion
- Decision: keep MuseTalk, tune, or research a stronger model

**Current status:** GPU inference not performed. No generated video or
verified quality claim.
