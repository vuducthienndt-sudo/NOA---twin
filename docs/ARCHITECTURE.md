# Architecture

## Core principle
NOA Person is a realtime interaction layer. It must remain independent from FIE during V0.x.

```
User microphone
  -> VAD / turn detection
  -> streaming STT
  -> Conversation Orchestrator
  -> Brain Adapter
  -> Temporary LLM
  -> streaming TTS
  -> audio playback
```

Future:
```
NOA Person -> Brain Adapter -> FIE Bridge -> FIE
```

## Primary modules
- realtime: turn state, interruption, cancellation, transport
- brain: provider-independent intelligence interface
- conversation: session context and response metadata
- voice: STT and TTS adapters
- avatar: event interface only in V0.1
- memory: session-only in V0.1
- web: call interface and client audio controls

## Realtime states
IDLE
LISTENING
USER_SPEAKING
PROCESSING
AI_SPEAKING
INTERRUPTED
ERROR

Critical transition:
AI_SPEAKING -> speech detected -> INTERRUPTED -> cancel output -> USER_SPEAKING

## Future structured response
```json
{
  "text": "Tell me what happened.",
  "emotion": "concerned",
  "gesture": "small_nod",
  "speakingStyle": "soft"
}
```

Avatar and voice implementations must consume metadata without changing the Brain contract.
