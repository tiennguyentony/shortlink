from datetime import datetime
from zoneinfo import ZoneInfo

from shortlink.cache import CachedLink, RedirectCache
from shortlink.clock import Clock, from_iso
from shortlink.domain.errors import LinkGone, NotFound
from shortlink.repositories.links import LinkRepo


class RedirectService:
    """Turns a short code into a target URL. This runs on every click."""

    def __init__(self, links: LinkRepo, cache: RedirectCache, clock: Clock, tz: ZoneInfo):
        self.links = links
        self.cache = cache
        self.clock = clock
        self.tz = tz

    def resolve(self, code: str) -> CachedLink:
        entry = self.cache.get(code)
        if entry is None:
            entry = self._load(code)
            self.cache.put(code, entry)
        if entry.expires_at is not None and self._now() >= entry.expires_at:
            raise LinkGone("expired")
        return entry

    def _load(self, code: str) -> CachedLink:
        link = self.links.by_code(code)
        if link is None or link.deleted_at:
            raise NotFound("Link")
        if link.disabled:
            raise LinkGone("disabled")
        expires_at = from_iso(link.expires_at).replace(tzinfo=None) if link.expires_at else None
        return CachedLink(link_id=link.id, target_url=link.target_url, expires_at=expires_at)

    def _now(self) -> datetime:
        # Expiry is a wall-clock time for the team, so compare in the team's timezone.
        return self.clock.now().astimezone(self.tz).replace(tzinfo=None)
