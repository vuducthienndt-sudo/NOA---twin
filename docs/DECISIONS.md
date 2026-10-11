# Architecture Decisions

## ADR-001 — FIE is excluded from V0.x
Reason: prove realtime conversation before introducing domain intelligence.

## ADR-002 — Brain Adapter is provider-independent
Reason: allow the temporary LLM to be replaced or augmented by FIE later without rewriting realtime/audio layers.

## ADR-003 — No model training in V0.1
Reason: integration latency and human interaction quality are the primary risks.

## ADR-004 — No photorealistic avatar in V0.1
Reason: realtime speech, cancellation, and turn-taking must be proven before visual polish.

## ADR-005 — Streaming-first
STT, brain output, TTS, and playback should stream wherever provider/runtime capabilities permit.

## ADR-006 — Cancellation is a first-class feature
Every layer participating in a response must support cancellation or safe abandonment.

## ADR-007 — Measure latency before optimizing
Instrument component timestamps before making architecture changes based on assumptions.
