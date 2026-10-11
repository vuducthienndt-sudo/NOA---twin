# HeyGen research translated into NOA Digital Twin engineering

Updated: 2026-10-11. These are **published research descriptions**, not HeyGen's complete production source code.

## Verified primary sources

- Avatar V model report: https://www.heygen.com/research/avatar-v-model
- Avatar V technical PDF: https://dynamic.heygen.ai/www/Paper%20Links/avatarv_tech_report.pdf
- Avatar V inference engineering: https://www.heygen.com/research/avatar-v-inference
- TAVR open-source implementation: https://github.com/heygen-com/TAVR
- TAVR model card: https://huggingface.co/HeyGenAI/TAVR

## 1. Reference-video conditioning

HeyGen Avatar V conditions on the full token sequence of a reference video instead
of relying only on a single portrait embedding. The reference preserves fine
details and habitual facial motion. The published design includes selecting
diverse viewpoints and expressions for its identity-preserving image engine.

**NOA translation now:** select representative reference frames spanning
the original video, avoiding blurred, dark and near-duplicate frames. Keep
the source video unchanged outside the lip-sync model's generated region.
See `select_references.py`. This is a *lightweight preprocessing analogue*,
not an implementation of Avatar V video token conditioning.

## 2. Sparse Reference Attention

Avatar V describes asymmetric attention: generated tokens can attend to
reference tokens, while reference tokens attend within their own set.
The design avoids naive all-to-all attention between all reference and
generation tokens, improving scaling with reference length.

**NOA translation later:** requires modifying/training an attention-based
generation backbone. A frame sampler or MuseTalk wrapper **does not implement**
Sparse Reference Attention. Track as a research-only future work item.

## 3. Motion representation and talking style

HeyGen uses a separate motion representation as a conditioning and learning
target for speaking style, head gestures and facial dynamics.

**NOA translation now:** reuse motion from the real video. Do not synthesize
new hand gestures. Future: add motion reference extraction and quantitative
comparison before any custom motion model training.

## 4. Identity-aware super-resolution

Avatar V's SR refiner inherits identity/video reference conditioning and
focuses on detail recovery in perceptually sensitive areas such as mouth
and teeth.

**NOA translation now:** avoid face-wide AI upscaling and limit processing
to a mouth ROI, with blending against the original source frames.
A future identity-aware refiner would require its own model and tests.

## 5. Inference efficiency

Published Avatar V inference engineering includes reference-context and
attention KV caching, chunked generation, distilled denoising, and streaming
VAE decoding. These optimizations belong to its large DiT inference stack.

**NOA translation now:** cache prepared video and extracted reference frames
on disk; do not reprocess inputs on each test. This is application-level
caching, **not** Avatar V KV caching.

## 6. TAVR — available research baseline, not budget default

HeyGen's TAVR code and model weights are public. Its model card lists
Wan2.1-T2V-14B as base, 20 default reference frames, 896x480 at 25 fps,
and a Hopper GPU with at least 80GB memory. TAVR has an Apache-2.0
release, but some third-party dependencies have different licenses,
including Ultralytics YOLO AGPL-3.0. Review all dependency and model
licenses before commercial deployment.

**NOA decision:** do not make TAVR the first paid GPU test. Study its
reference-conditioning code, then test MuseTalk 1.5 on a short clip.

## Budget and acceptance gates

Monthly operating/research ceiling: 1,000,000 VND.
Initial paid GPU experiment ceiling: 200,000 VND, subject to price confirmation.

- Identity: eye/nose/skin geometry and teeth should not visibly drift.
- Lip sync: Vietnamese phonemes should track the authorized voice audio.
- Temporal consistency: no noticeable frame-to-frame face flicker.
- Body: original shoulder/hand movement remains intact.
- Record GPU time, total cost and number of failed renders.

No quality or cost guarantee until an actual consented sample is rendered.

## 7. Additional official HeyGen disclosures (October 2026)

Sources:
- https://www.heygen.com/research/avatar-inference-at-scale
- https://www.heygen.com/research/heygen-x-google-cloud-bringing-avatar-iv-to-tpus
- https://community.heygen.com/public/resources/avatar-v-live-webinar-recap-top-questions-answered-2026-04-16
- https://help.heygen.com/en/articles/12805098-fine-tune-avatar-gestures-and-movements-with-custom-motion-prompts-avatar-iv-v
- https://www.heygen.com/blog/how-to-create-high-quality-digital-twins
- https://www.heygen.com/blog/how-to-create-digital-twin-avatar

### Publicly described model architecture — confirmed vs inferred

HeyGen's engineering account describes a **Diffusion Transformer (DiT) trained
with flow matching**, conditioned on rich reference image/video tokens, audio,
and optional text/scene controls. Its production inference pipeline has:
1. Audio-conditioned video latent generation for lip sync and motion.
2. Identity-aware super-resolution, prioritizing face, teeth, mouth and skin.
3. Chunked streaming VAE decode, with cross-chunk continuity conditioning.

HeyGen publicly describes Avatar IV as a model stack exceeding 18B parameters
and optimized across multi-accelerator hardware. These disclosures explain
why a mouth-region lip-sync model alone is **not** architecturally equivalent
to HeyGen's full-avatar generation. They do not reveal full training data,
model weights, private recipes or a reproducible HeyGen implementation.

### Avatar V personal training vs Avatar IV

HeyGen's Avatar V webinar says its personal avatar combines a photo,
cloned voice and a short reference video (approximately 15 seconds), and
fine-tunes a model based on that reference. Its public guidance also
emphasizes explicit video consent, consistent identity, lighting and clear
audio. Do not assume that 15 seconds guarantees HeyGen-level quality in
an unrelated open-source model.

### Motion controls and speech conditioning

HeyGen exposes expression, gesture and gaze controls; IV supports scene
motion prompting while V provides additional structured controls.
This implies NOA should separate **speech/audio**, **identity reference**,
**motion/style reference**, and **optional directed motion** in its eventual
job schema. It does NOT mean MuseTalk can accept all those controls.

### Proposed NOA architecture, NOT implemented

```text
Verified owner consent + source video + clean speech
        |
        +--> Identity reference bank (sharp/diverse frames)
        +--> Audio feature extraction + Vietnamese speech test
        +--> Motion reference / expression guidance
        |
        v
  Video generation backbone (future DiT/flow matching research)
        |
        v
  Identity-aware mouth/face refinement
        |
        v
  Temporal consistency + lip sync + identity review
        |
        v
  Human approval before publishing
```

**Current executable baseline:** MuseTalk 1.5 for a cheap 10-second
consented pilot. It performs audio-driven lip synchronization, not
HeyGen's entire generative motion and identity-refinement pipeline.
Reference frame selection and worker safety are separate modules;
do not claim that they condition MuseTalk unless wired into the model.

### Experiment decision gates

- Baseline A: original consented video + MuseTalk lip-sync; measure
  face/teeth drift, Vietnamese lip sync and shoulder/hand preservation.
- Candidate B: public full-frame, reference-conditioned audio-to-video
  model **only after** checking license, memory footprint and cost.
- Candidate C: identity-aware refinement **only if** B is strong enough
  and mouth/teeth fidelity remains the bottleneck.
- Record a blind side-by-side comparison with the same 10-second audio
  against an authorized HeyGen sample; do not assume parity.
- Stop before paid experiments when the estimated cap exceeds 200,000 VND;
  the app-side estimate is not a provider-side spending guard.

**Research conclusion:** A MuseTalk-only implementation may validate
the pipeline, but it is unlikely to reproduce the entire HeyGen avatar
behavior stack. Treat HeyGen as a measured quality target, not a promise.

## 8. Executable human quality gate

`heygen_scorecard.py` records a **human review** of the same 10-second
source/audio clip across different models. All six fields must be integers
from 1 (unusable) to 5 (excellent):

| Criterion | Weight | Minimum |
| --- | ---: | ---: |
| identity | 25% | 4 |
| vietnamese_lip_sync | 25% | 4 |
| mouth_teeth | 15% | 3 |
| temporal_stability | 15% | 3 |
| natural_motion | 10% | 3 |
| body_preservation | 10% | 4 |

The candidate passes the **review gate** only when weighted score >= 4/5
and every minimum is met. These are NOA's proposed thresholds, not
HeyGen-published quality scores. A pass does not establish objective
identity matching, voice quality or publication permission.

Example:
`python -m digital_twin.heygen_scorecard --scores review_scores.json --out review_result.json`

Record a separate scorecard for each model and reviewer. Use identical
source footage, speech audio, duration and crop to avoid misleading
comparisons. No real-world scores have been recorded yet.

## 9. Controlled experiment registry

The `experiment_registry.py` module records model label, source asset ID,
speech asset ID, clip duration, observed GPU minutes, manually entered cost,
and optional human scorecard. Comparison **rejects different source/audio
or clip lengths** and ranks only reviewed outputs. No results or expenses
are fabricated; the database is not automatically linked to RunPod billing.

The initial A/B protocol uses the **same authorized 10-second footage and
Vietnamese audio** for MuseTalk 1.5 and any other permitted model or
authorized HeyGen reference. Reviewers score outputs independently using
`heygen_scorecard.py`. Capture objective output metadata separately and
log the GPU provider's actual charges before deciding whether to scale.

Usage: `python -m digital_twin.experiment_registry --records experiment_a.json experiment_b.json --out comparison.json`.

This does not train a HeyGen-like model or produce a render. It creates
repeatable evidence for choosing the next technical direction.
