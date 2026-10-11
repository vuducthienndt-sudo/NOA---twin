# Roadmap

## V0.1 — Realtime Voice Core

### Phase 1 — Foundation
- repository structure
- web shell
- realtime/backend service
- environment configuration
- health checks

### Phase 2 — User speech
- microphone capture
- VAD
- streaming STT
- speech-start / speech-end events

### Phase 3 — Brain
- Brain Adapter interface
- temporary LLM provider
- streaming response
- cancellation support

### Phase 4 — Voice output
- streaming TTS
- incremental playback
- output cancellation

### Phase 5 — Barge-in
- explicit realtime state machine
- interrupt AI speech on user voice
- preserve session context

### Phase 6 — Measurement
- latency telemetry
- error recovery
- basic integration tests

## Definition of done
A user can:
1. Start a call.
2. Say “Alo.”
3. Hear NOA answer.
4. Continue a contextual conversation.
5. Interrupt NOA while it is speaking.
6. Observe NOA stop quickly and listen to the new utterance.

Primary metric:
speech_ended -> playback_started

Target: about 2 seconds or better under normal conditions.

## Later milestones
V0.2: basic avatar + lip sync
V0.3: session/personality improvements
V0.4: long-term memory
V0.5: camera/vision
V1.0: FIE Bridge
