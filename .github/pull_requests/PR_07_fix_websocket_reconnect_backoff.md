# Pull Request #7: WebSocket Reconnection Storm Prevention with Exponential Backoff and Jitter

## 1. What was the bug before?
In `src/hooks/useHush.ts`, the frontend WebSocket connection handler managed disconnects using a fixed interval retry:
```typescript
ws.onclose = () => {
  setConnected(false);
  setRecording(false);
  setBusy(false);
  setState("idle");
  // Reconnect after 1.5 seconds
  reconnectTimeoutRef.current = window.setTimeout(connect, 1500);
};
```
This produced the following critical bugs:
1. **Connection Storming**: If the Python background service was loading or compiling an OpenVINO model (which can take 5 to 15 seconds), the frontend bombarded `ws://127.0.0.1:4874` every 1.5 seconds without backoff.
2. **Concurrent Sockets / Event Listener Leak**: If `connect()` was re-triggered (e.g. from state change, window re-focus, or dependency updates), previous timeout handles were not cleared. Multiple WebSocket instances were created simultaneously, leading to duplicate state subscriptions and UI thrashing.
3. **No Unmount Protection**: If components unmounted, in-flight connection timeouts could still fire and instantiate orphaned sockets.

## 2. What problem does this PR solve?
- **Exponential Backoff with Jitter**: Reconnection delays now scale progressively (1s -> 1.5s -> 2.25s ... capped at 10s) with added random jitter (`Math.random() * 500ms`) to prevent lockstep connection retries.
- **Strict Single-Socket Guarantee**: Clears pending reconnect timeouts before scheduling new attempts, and prevents new socket instantiations if a socket is already connecting or open.
- **Lifecycle Cleanup**: Added `isUnmountedRef` to abort in-flight connection attempts when the hook unmounts, cleaning up all timers and open sockets.
- **Successful Connection Reset**: Resets the retry attempt counter to 0 immediately upon a successful `onopen` handshake.

## 3. What is NOT solved / Limitations
- Does not change the WebSocket port (remains on default port 4874 on 127.0.0.1).
- Assumes local loopback connectivity (remote networking is intentionally disabled for privacy).

## 4. How was it tested?
- Tested full TypeScript compilation (`npx tsc --noEmit`), which completed with 0 errors.
- Verified timer cancellation and backoff sequence when service is stopped and started.
- Verified immediate clean reset upon successful connection.
