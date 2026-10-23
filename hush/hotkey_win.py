"""Global hotkeys via a low-level keyboard hook (WH_KEYBOARD_LL).

Two bindings, both runtime-configurable:
  - hold chord (push-to-talk): fires on_hold_down when all chord keys are down,
    on_hold_up when any is released.
  - toggle combo: fires on_toggle on key-down of the final key while its
    modifiers are held. Non-modifier trigger keys are suppressed so they don't
    reach the focused app.

Callbacks are offloaded to an asynchronous queue worker to prevent blocking
the OS low-level hook thread, avoiding silent hook eviction by Windows LowLevelHooksTimeout.
Injected events (our own SendInput) are ignored.
"""

import ctypes
import ctypes.wintypes as wt
import queue
import threading

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x100, 0x101, 0x104, 0x105
LLKHF_INJECTED = 0x10

VK = {
    "Ctrl": (0xA2, 0xA3),
    "Alt": (0xA4, 0xA5),
    "Shift": (0xA0, 0xA1),
    "Win": (0x5B, 0x5C),
    "Space": (0x20,),
    "CapsLock": (0x14,),
    "Tab": (0x09,),
    "Enter": (0x0D,),
    "Esc": (0x1B,),
}

# Add standard letters A-Z (0x41 - 0x5A)
for c in range(ord("A"), ord("Z") + 1):
    VK[chr(c)] = (c,)

# Add digits 0-9 (0x30 - 0x39)
for d in range(10):
    VK[str(d)] = (0x30 + d,)

# Add function keys F1-F12 (0x70 - 0x7B)
for f in range(1, 13):
    VK[f"F{f}"] = (0x70 + f - 1,)

_MODIFIER_NAMES = ("Ctrl", "Alt", "Shift", "Win")


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", wt.WPARAM)]


_HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wt.WPARAM, wt.LPARAM)

user32.SetWindowsHookExW.restype = wt.HHOOK
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, _HOOKPROC, wt.HINSTANCE, wt.DWORD]
user32.UnhookWindowsHookEx.argtypes = [wt.HHOOK]
user32.CallNextHookEx.restype = ctypes.c_longlong
user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]


def _parse(combo: str):
    """'Ctrl+Alt+D' -> (frozenset of modifier key-groups, trigger vk tuple or None).

    A combo of only modifiers (e.g. 'Ctrl+Win') has trigger None: it is a chord.
    'F9 (hold)' -> single-key chord.
    """
    name = combo.replace(" (hold)", "")
    parts = [p.strip() for p in name.split("+")]
    mods = tuple(p for p in parts if p in _MODIFIER_NAMES)
    rest = [p for p in parts if p not in _MODIFIER_NAMES]
    trigger = VK.get(rest[0]) if rest else None
    return mods, trigger


class HotkeyHook:
    def __init__(self, on_hold_down, on_hold_up, on_toggle):
        self.on_hold_down = on_hold_down
        self.on_hold_up = on_hold_up
        self.on_toggle = on_toggle
        self._down = set()          # currently-pressed physical vk codes
        self._hold_active = False
        self._lock = threading.Lock()
        self._hold_mods, self._hold_trigger = _parse("Ctrl+Win")
        self._tog_mods, self._tog_trigger = _parse("Ctrl+Alt+D")
        self._thread_id = None
        self._hook = None
        self.accept_injected = False  # tests only: let SendInput events drive the hook
        self._proc = _HOOKPROC(self._callback)  # keep a reference alive
        self._queue = queue.SimpleQueue()
        self._worker_thread = threading.Thread(target=self._worker_loop, name="hotkey-worker", daemon=True)
        self._worker_thread.start()

    def _worker_loop(self):
        """Worker thread executing hotkey callbacks off the OS hook thread to prevent unhook timeouts."""
        while True:
            action = self._queue.get()
            if action is None:
                break
            try:
                if action == "down":
                    self.on_hold_down()
                elif action == "up":
                    self.on_hold_up()
                elif action == "toggle":
                    self.on_toggle()
            except Exception:
                pass

    def set_bindings(self, hold_chord: str, toggle_combo: str):
        with self._lock:
            self._hold_mods, self._hold_trigger = _parse(hold_chord)
            if toggle_combo == "Disabled":
                self._tog_mods, self._tog_trigger = (), None
            else:
                self._tog_mods, self._tog_trigger = _parse(toggle_combo)

    # ---- state helpers (call with lock held) ----
    def _group_down(self, name):
        vks = VK.get(name, ())
        return any(vk in self._down for vk in vks)

    def _cleanup_stuck_keys(self):
        """Re-verify physical key state with GetAsyncKeyState to prevent stuck keys after alt-tab / lock."""
        stale = []
        for vk in self._down:
            try:
                if not (user32.GetAsyncKeyState(vk) & 0x8000):
                    stale.append(vk)
            except Exception:
                pass
        for vk in stale:
            self._down.discard(vk)

    def _hold_chord_down(self):
        if not all(self._group_down(m) for m in self._hold_mods):
            return False
        if self._hold_trigger is not None:
            return any(vk in self._down for vk in self._hold_trigger)
        return bool(self._hold_mods)

    def _callback(self, n_code, w_param, l_param):
        if n_code >= 0:
            kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            injected = bool(kb.flags & LLKHF_INJECTED)
            # normal mode: react to physical keys only. Test mode additionally
            # accepts our own tagged SendInput events — but never other software's
            # injected keys (Explorer injects phantom Ctrl around the Win key).
            from .inject_win import INJECT_TAG
            if not injected or (self.accept_injected and kb.dwExtraInfo == INJECT_TAG):
                is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                suppress = False
                fire = None
                with self._lock:
                    if is_down:
                        self._down.add(kb.vkCode)
                    else:
                        self._down.discard(kb.vkCode)
                        self._cleanup_stuck_keys()

                    # toggle combo
                    if (is_down and self._tog_trigger and kb.vkCode in self._tog_trigger
                            and all(self._group_down(m) for m in self._tog_mods)):
                        fire = "toggle"
                        suppress = True
                    elif (not is_down and self._tog_trigger and kb.vkCode in self._tog_trigger
                            and all(self._group_down(m) for m in self._tog_mods)):
                        suppress = True  # swallow the matching key-up too

                    # hold chord
                    chord = self._hold_chord_down()
                    if chord and not self._hold_active:
                        self._hold_active = True
                        fire = fire or "down"
                        if self._hold_trigger is not None and kb.vkCode in self._hold_trigger:
                            suppress = True
                    elif not chord and self._hold_active:
                        self._hold_active = False
                        fire = fire or "up"
                        if self._hold_trigger is not None and kb.vkCode in self._hold_trigger:
                            suppress = True

                if fire:
                    self._queue.put(fire)

                if suppress:
                    return 1
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def start(self):
        threading.Thread(target=self._run, name="hotkey-hook", daemon=True).start()

    def _run(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc, None, 0)
        if not self._hook:
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def stop(self):
        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT
        if hasattr(self, "_queue"):
            self._queue.put(None)
