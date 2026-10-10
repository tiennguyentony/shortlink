"""In-process cache for the redirect hot path (ADR-001)."""

import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CachedLink:
    link_id: int
    target_url: str
    expires_at: datetime | None


class RedirectCache:
    """A small thread-safe LRU cache: code -> where to send the visitor.

    Only active links are cached. Anything that changes where a code points,
    or whether it should redirect at all, must call `evict(code)`.
    """

    def __init__(self, max_entries: int = 10_000):
        self.max_entries = max_entries
        self._entries: OrderedDict[str, CachedLink] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, code: str) -> CachedLink | None:
        with self._lock:
            entry = self._entries.get(code)
            if entry is None:
                self.misses += 1
                return None
            self._entries.move_to_end(code)
            self.hits += 1
            return entry

    def put(self, code: str, entry: CachedLink) -> None:
        with self._lock:
            self._entries[code] = entry
            self._entries.move_to_end(code)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def evict(self, code: str) -> None:
        with self._lock:
            self._entries.pop(code, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
