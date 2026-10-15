"""Tiny in-memory TTL cache. Swap for Redis by re-implementing get_or_set/clear."""
import threading
import time

from app.config import CACHE_TTL


class TTLCache:
    def __init__(self, ttl: int):
        self.ttl = ttl
        self._data = {}
        self._lock = threading.Lock()

    def get_or_set(self, key, factory):
        now = time.time()
        with self._lock:
            hit = self._data.get(key)
            if hit and hit[0] > now:
                return hit[1]
        value = factory()  # computed outside the lock so factories may use the cache
        with self._lock:
            self._data[key] = (now + self.ttl, value)
        return value

    def clear(self):
        with self._lock:
            self._data.clear()


cache = TTLCache(CACHE_TTL)
