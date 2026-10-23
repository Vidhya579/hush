# Hush Open Source Contribution Suite

This directory indexes the 10 distinct bug fixes, resiliency enhancements, and feature contributions implemented across Hush. Each Pull Request includes a dedicated branch, thorough root cause analysis, implementation diff, and test coverage.

## Summary Index of Pull Requests

| PR # | Branch Name | Component | Problem / Bug Solved | Out of Scope / Limitations |
| :---: | :--- | :--- | :--- | :--- |
| **01** | `fix/hotkey-callback-thread-safety` | Win32 Hotkey Hook (`hotkey_win.py`) | Fixes `WH_KEYBOARD_LL` hook callback blocking that caused Windows to silently unhook hotkeys (`LowLevelHooksTimeout`); adds stuck key clearance and expanded VK keys. | Does not bypass OS-level UIPI for typing into elevated administrator windows. |
| **02** | `fix/textproc-multiword-devanagari` | Text Processing (`textproc.py`) | Enables multi-word dictionary phrases (e.g. "Hush Engine") and Unicode Devanagari script tokenization for Hindi/Hinglish dictation. | Does not perform phonetic Romanized-to-Devanagari transliteration. |
| **03** | `fix/textproc-ellipsis-spacing` | Text Repair (`textproc.py`) | Prevents three-dot ellipses (`...` / `…`) from being collapsed into single periods; fixes spacing after punctuation before numbers, quotes, and Indic characters. | Does not change Whisper acoustic pause detection threshold. |
| **04** | `fix/audio-callback-exceptions-memory` | Audio Engine (`audio.py`) | Shields PortAudio stream callbacks from unhandled Python exceptions (`CallbackAbort`); eliminates $O(N^2)$ historical audio buffer concatenation in `read_range`. | Does not handle physical microphone unplugging during recording. |
| **05** | `fix/config-atomic-windows-replace` | Config Persistence (`config.py`) | Adds exponential backoff retries and fallback writes for Windows file locks (`[WinError 32]`); eliminates floating-point precision drift in stats. | Does not handle multi-user conflicting writes across OS sessions. |
| **06** | `fix/history-missing-dir-and-load` | Dictation History (`history.py`) | Fixes `FileNotFoundError` on non-existent parent directory, adds thread locking for concurrency, and uses a bounded `deque` to avoid parsing entire file history. | Retains lightweight JSONL format without external SQL dependencies. |
| **07** | `fix/websocket-reconnect-backoff` | React Frontend (`useHush.ts`) | Prevents reconnection loop storming with exponential backoff and randomized jitter; guarantees strict single-socket connection lifecycle. | Does not enable remote networking (remains strictly 127.0.0.1 for privacy). |
| **08** | `fix/sound-playback-duplicate-chime` | Audio Feedback (`useHush.ts`) | Eliminates duplicate double-chime audio echo by designating the background Python service as the single authoritative sound player when connected. | Does not replace built-in WAV audio sample files. |
| **09** | `fix/overlay-status-auto-clear` | Background Service (`service.py`) | Fixes capsule overlay pill permanently stuck displaying "✓ Inserted" or transient error messages by introducing a cancellation-safe auto-clear timer. | Fatal engine errors (missing model) deliberately remain visible. |
| **10** | `fix/dictionary-dedup-batch-import` | Dictionary Tab (`DictionaryTab.tsx`) | Implements case-insensitive deduplication, batch comma/newline list splitting, and quote trimming when adding custom dictionary entries. | Does not import directly from external file picker dialogs. |

---

## Final Integrated Branch
- **Branch**: `open-source-contributions-final`
- **Scope**: Seamless integration of all 10 bug fixes and architectural enhancements.
- **Verification**: 100% test pass rate across `tests/` test suites and zero TypeScript/bundling errors.
