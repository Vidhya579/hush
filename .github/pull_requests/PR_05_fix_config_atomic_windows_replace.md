# Pull Request #5: Resilient Atomic Config Save on Windows Against Transient File-Lock Errors

## 1. What was the bug before?
In `hush/config.py`, configuration persistence is handled by writing data to a `.tmp` file and replacing the target file:
```python
def save(self):
    with self._lock:
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        os.replace(tmp, CONFIG_PATH)
```
On Windows, `os.replace` relies on the Win32 `MoveFileExW` API with `MOVEFILE_REPLACE_EXISTING`.
If any background process on the system has `config.json` open with shared read access (such as Windows Defender / antivirus scanning recently written files, Windows Search Indexer, or an editor), `os.replace` immediately throws:
`PermissionError: [WinError 32] The process cannot access the file because it is being used by another process` or `[WinError 5] Access is denied`.

This uncaught exception caused service crashes during dictation stat updates or preference changes, leaving orphaned `.tmp` files in `%LOCALAPPDATA%\Hush`.

Additionally, cumulative audio seconds in session stats suffered from floating-point accumulation errors (e.g. `14.200000000000001` instead of `14.2`).

## 2. What problem does this PR solve?
- **Exponential Backoff Retry**: When `os.replace` encounters transient file locks, it retries up to 5 times with exponential backoff (20ms, 40ms, 80ms, 160ms, 320ms), giving indexers/antivirus tools time to release the file handle.
- **Fail-Safe Fallback**: If file replacement is still blocked after 5 attempts, falls back to direct write to `CONFIG_PATH` and cleans up the temporary file, ensuring user settings are never lost.
- **Directory Auto-Creation**: Guarantees parent `APP_DIR` exists before attempting write operations.
- **Stats Floating-Point Rounding**: Rounds `audio_seconds` to 2 decimal places to eliminate precision artifacts.

## 3. What is NOT solved / Limitations
- Does not arbitrate conflicting multi-user concurrent writes across separate OS sessions (Hush runs strictly as a single-instance user application).

## 4. How was it tested?
- Added `tests/test_config.py`:
  - Verified `audio_seconds` accumulates without floating point drift.
  - Mocked `os.replace` raising `PermissionError` and verified the fallback save writes `config.json` reliably without crashing.
- All unit tests pass cleanly.
