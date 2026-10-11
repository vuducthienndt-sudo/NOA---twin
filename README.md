# NOA Person

Realtime AI Human for the NOA ecosystem.

## Status
V0.1 — Realtime Voice Core.

## Goal
Build a low-latency conversational AI experience that supports natural turn-taking and interruption. The initial version is intentionally independent from FIE. FIE will later connect through a provider-independent Brain Adapter.

## V0.1 scope
- Microphone input
- Voice activity detection
- Streaming speech-to-text
- Realtime conversation state machine
- Provider-independent Brain Adapter
- Temporary LLM
- Streaming text-to-speech
- Barge-in / interruption
- Minimal call UI
- Latency instrumentation

## Out of scope for V0.1
- FIE integration
- Vision
- Long-term memory
- Photorealistic digital human
- Model training

See `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/REALTIME.md`, and `docs/DECISIONS.md`.
