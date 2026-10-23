# Pull Request #1: Fix `WH_KEYBOARD_LL` Hook Callback Thread Blocking and Silent Unhook Timeout

## 1. What was the bug before?
In Windows, low-level keyboard hooks registered with `SetWindowsHookExW(WH_KEYBOARD_LL, ...)` execute on a dedicated hook procedure callback thread. The OS enforces a strict response timeout via the registry value `LowLevelHooksTimeout` (typically 200ms to 300ms, max 1000ms). If the hook procedure takes longer than this threshold, Windows silently discards the hook without raising any exception or notifying the application.

Previously, `HotkeyHook._callback` in `hush/hotkey_win.py` invoked `self.on_hold_down()`, `self.on_hold_up()`, and `self.on_toggle()` **synchronously** directly inside the OS hook callback. When `self.on_hold_down()` executed, `HushService.start_dictation()` performed microphone warming, audio stream acquisition retry loops with `time.sleep(0.12)`, and WebSocket broadcasts. During system load or microphone initialization delays, this easily exceeded the 200ms timeout, causing Windows to permanently unhook Hush. The user experienced this as global hotkeys (`Ctrl+Win`, `Ctrl+Alt+D`) suddenly stopping working until the app was fully restarted.

Additionally:
- Keys could remain stuck in `self._down` if Windows failed to deliver a `WM_KEYUP` event (e.g. during an Alt-Tab or screen lock transition).
- Key combinations were restricted to a small hardcoded set of keys (Ctrl, Alt, Shift, Win, Space, D, F9, F10), breaking custom bindings.

## 2. What problem does this PR solve?
- **Asynchronous Queue Worker**: Offloads callback execution from the Windows hook thread into a dedicated worker thread using `queue.SimpleQueue`. The hook callback now posts `"down"`, `"up"`, or `"toggle"` to the queue and returns immediately (<1ms) via `CallNextHookEx`.
- **Stuck Key Auto-Clear**: Periodically re-verifies physical key states using `user32.GetAsyncKeyState` on key releases to prevent phantom modifiers from jamming the chord detector.
- **Expanded Key Parsing Support**: Extended the `VK` table to support all standard alphanumeric keys (A-Z, 0-9), function keys (F1-F12), `CapsLock`, `Tab`, `Enter`, and `Esc`.
- **Clean Teardown**: Updated `stop()` to signal the queue worker to exit gracefully without leaking threads.

## 3. What is NOT solved / Limitations
- Does not bypass Windows UIPI restrictions for non-elevated apps attempting to inject keystrokes into elevated (Administrator) windows (that is an intentional OS security model and handled separately via Hush's UIPI detection and clipboard fallback).
- Linux hotkey handler (`hotkey_linux.py`) uses a different X11/Wayland event loop and is unaffected by this Win32 hook timeout.

## 4. How was it tested?
- Tested with high-latency mock callbacks (simulating 500ms audio stream delays); confirmed the OS hook thread returns immediately without being unhooked.
- Verified that `_queue` processes down, up, and toggle events in order.
- Verified expanded VK bindings for `F1`..`F12` and alphanumeric keys.
