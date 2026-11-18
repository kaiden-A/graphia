from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    """Small in-process limiter. Approximate across multiple Cloud Run instances."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            if len(self._events) > 5_000:
                stale = [item for item, values in self._events.items() if not values]
                for item in stale:
                    self._events.pop(item, None)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


login_limiter = SlidingWindowLimiter()
upload_limiter = SlidingWindowLimiter()
guest_limiter = SlidingWindowLimiter()
cli_limiter = SlidingWindowLimiter()
