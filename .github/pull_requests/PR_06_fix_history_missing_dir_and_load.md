# Pull Request #6: Fix History Logger Directory Creation, Concurrency Safety, and Bounded Line Loading

## 1. What was the bug before?
In `hush/history.py`:
1. **`FileNotFoundError` on non-existent parent directory**: `history.append(text, duration)` executed `with open(HISTORY_PATH, "a", encoding="utf-8") as f:` without checking if the parent directory existed. If Hush was freshly installed, portable, or if `%LOCALAPPDATA%\Hush` had not been initialized, calling `append()` crashed with `FileNotFoundError`.
2. **Unbounded memory usage & redundant parsing**: In `history.load(limit=500)`, the function read every single line of the file and parsed every line via `json.loads(line)` into memory before slicing `entries[-limit:][::-1]`. For users with thousands of entries accumulated over months, this parsed thousands of unneeded JSON objects on startup and UI refresh.
3. **Lack of thread safety**: `history.py` lacked file/thread locking, leading to potential corrupt writes or read conflicts when background transcription threads logged entries concurrently.

## 2. What problem does this PR solve?
- **Auto-Directory Creation**: Ensures `os.path.dirname(HISTORY_PATH)` is created automatically prior to appending.
- **Thread Synchronization**: Protects file writes, reads, and deletions using a module-level `threading.Lock`.
- **Bounded Buffer Loading**: Uses `collections.deque(maxlen=limit)` to retain only the last `limit` lines from the file, parsing JSON only for the lines that will actually be returned.
- **Empty / Corrupt Line Tolerance**: Gracefully skips empty strings and malformed lines.

## 3. What is NOT solved / Limitations
- Does not implement an external SQL database (retains lightweight JSONL format to maintain zero external C/Rust dependencies and transparent portability).

## 4. How was it tested?
- Added `tests/test_history.py`:
  - Verified directory auto-creation with deep nested paths.
  - Verified `load(limit=5)` with 20 items parses and returns exactly the latest 5 items in newest-first order.
  - Verified `clear()` cleanly deletes the history file.
- All unit tests pass cleanly.
