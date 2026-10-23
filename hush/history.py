"""Dictation history: JSONL log with search, re-copy, privacy clear."""

from collections import deque
import json
import logging
import os
import threading
import time

from .config import HISTORY_PATH

log = logging.getLogger("hush.history")
_lock = threading.Lock()


def append(text: str, duration: float):
    """Append a dictation entry to the history JSONL log safely."""
    if not text:
        return
    entry = {"ts": time.time(), "text": text, "seconds": round(duration, 1)}
    parent_dir = os.path.dirname(HISTORY_PATH)
    with _lock:
        try:
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(HISTORY_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            log.error("Failed to append to history log %s: %s", HISTORY_PATH, e)


def load(limit=500):
    """Load the most recent `limit` history entries (newest first)."""
    with _lock:
        if not os.path.exists(HISTORY_PATH):
            return []
        recent_lines = deque(maxlen=limit)
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        recent_lines.append(s)
        except OSError as e:
            log.error("Failed to read history log %s: %s", HISTORY_PATH, e)
            return []

    entries = []
    # Parse only the capped slice of lines in reverse (newest first)
    for line in reversed(recent_lines):
        try:
            entries.append(json.loads(line))
        except (ValueError, TypeError):
            continue
    return entries


def clear():
    """Clear all recorded dictation history."""
    with _lock:
        try:
            if os.path.exists(HISTORY_PATH):
                os.remove(HISTORY_PATH)
        except OSError as e:
            log.error("Failed to remove history log %s: %s", HISTORY_PATH, e)
