# Realtime Contract

## Events to instrument
- speech_started
- speech_ended
- transcription_partial
- transcription_ready
- brain_request_started
- brain_first_token
- tts_request_started
- tts_first_audio
- playback_started
- interruption_detected
- playback_cancelled

## Required metric
`speech_ended -> playback_started`

## Barge-in behavior
When user speech is detected during AI playback:
1. emit interruption_detected
2. abort current brain stream if appropriate
3. cancel TTS generation where possible
4. stop audio playback immediately
5. transition to USER_SPEAKING
6. capture new speech
7. maintain valid conversation context

## Design requirement
All long-running operations should accept cancellation via AbortSignal or an equivalent mechanism.

## Transport
Do not choose WebRTC merely because this is a "call" product. V0.1 should use the simplest transport that achieves low latency. Audio capture/playback can remain browser-native while backend streaming may use WebSocket. Re-evaluate WebRTC when peer media transport or server media routing creates a concrete need.
