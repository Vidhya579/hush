# Pull Request #8: Eliminate Concurrent Frontend/Backend Duplicate Audio Chimes

## 1. What was the bug before?
Hush provides audible start and stop chimes to inform the user when dictation begins and finishes.
However, sound playback was triggered in two places simultaneously:
1. In `src/hooks/useHush.ts`, `startDictation`, `stopDictation`, and `playSound` called `playLocalSound("start")` using the HTML5 Web Audio API in the Electron renderer process.
2. Immediately afterwards, `useHush.ts` transmitted `{ action: "start_dictation" }` or `{ action: "play_sound" }` over the local WebSocket to `hush/service.py`.
3. In `hush/service.py`, `start_dictation()` and `handle_message` independently invoked `sounds.play("start")` via Windows `winsound.PlaySound`.

Because both the Chromium browser audio subsystem and the Python Win32 subsystem played the same WAV file concurrently with a slight IPC latency jitter (30-80ms), users heard a harsh, stuttering echo or double chime every time dictation was triggered from the UI or previewed in Preferences.

## 2. What problem does this PR solve?
- **Unified Audio Authority**: Designates the background Python service (`sounds.play`) as the authoritative sound player during active WebSocket connections.
- **Offline Fallback Preservation**: Renderer-side `playLocalSound` is retained strictly as an offline fallback when disconnected from the backend or running in demo/standalone UI mode.
- **Clean Chime Previews**: Preview buttons in the Preferences tab now route through the authoritative backend player without triggering parallel browser audio.

## 3. What is NOT solved / Limitations
- Does not change the sound sample files (`sounds/start.wav`, `sounds/stop.wav`).
- Volume is controlled via OS system audio settings.

## 4. How was it tested?
- Tested full TypeScript compilation (`npx tsc --noEmit`) - passed with 0 errors.
- Verified that triggering dictation in connected mode plays exactly one sound chime.
- Verified that disconnected state falls back cleanly to local HTML5 Audio.
