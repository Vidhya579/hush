# Pull Request #9: Auto-Clear "✓ Inserted" and Transient Error States on Floating Overlay Capsule

## 1. What was the bug before?
When a dictation session finished, `HushService._on_finished` in `hush/service.py` set the state to `"inserted"` via:
```python
else:
    self._set_state("inserted", "✓ Inserted")
```
However, no timer or transition back to `"idle"` was scheduled.
Similarly, transient errors like `"No speech detected"` or `"No mic signal — check mic mute"` were broadcast with no clear schedule.

As a result, the floating capsule overlay remained permanently frozen displaying `"✓ Inserted"` or `"No speech detected"` on top of the user's active window until another dictation was triggered.

## 2. What problem does this PR solve?
- **Cancellation-Safe State Reversion**: Introduced `_schedule_auto_clear(expected_state, delay_s)` in `HushService`.
- **Automatic "✓ Inserted" Dismissal**: Reverts the overlay to `"idle"` after 2.0 seconds of showing the success checkmark.
- **Automatic Transient Error Dismissal**: Clears non-fatal dictation errors after 2.5 to 3.0 seconds.
- **Race Condition Safety**: If a new dictation starts while an auto-clear timer is pending (`self.recording == True` or `self._state != expected_state`), the clear event is cleanly aborted, ensuring active dictations are never interrupted.

## 3. What is NOT solved / Limitations
- Persistent startup or configuration errors (e.g., missing model files) deliberately remain displayed so the user is informed that configuration action is needed.

## 4. How was it tested?
- Tested state transitions: verified `"inserted"` transitions to `"idle"` after 2.0s.
- Tested starting a new dictation within 1.0s of completion: verified the new `"listening"` state is preserved and not clobbered by the previous timer.
- Ran TypeScript compilation and service unit checks.
