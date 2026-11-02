from collections import defaultdict, deque
from threading import Lock
import time


class RateLimiter:
    """Per-process request limits; deployment documentation states that boundary."""
    def __init__(self, limit=120, window=60):
        self.limit, self.window = limit, window
        self.buckets = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key):
        with self.lock:
            now = time.monotonic()
            queue = self.buckets[key]
            while queue and queue[0] <= now - self.window:
                queue.popleft()
            if len(queue) >= self.limit:
                return False
            queue.append(now)
            return True
