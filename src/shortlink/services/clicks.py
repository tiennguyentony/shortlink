import sqlite3
from dataclasses import dataclass

from shortlink.clock import Clock, to_iso
from shortlink.domain.analytics import is_bot, referrer_host
from shortlink.geo import GeoLookup
from shortlink.repositories.clicks import ClickRepo
from shortlink.repositories.links import LinkRepo


@dataclass(frozen=True)
class Visit:
    """What we know about one request to a short link. Never stored as-is."""

    ip: str | None
    user_agent: str | None
    referrer: str | None


class ClickService:
    def __init__(
        self,
        conn: sqlite3.Connection,
        links: LinkRepo,
        clicks: ClickRepo,
        geo: GeoLookup,
        clock: Clock,
    ):
        self.conn = conn
        self.links = links
        self.clicks = clicks
        self.geo = geo
        self.clock = clock

    def record(self, link_id: int, visit: Visit) -> bool:
        """Count a click. Returns False if the visit was not counted."""
        if is_bot(visit.user_agent):
            return False
        country = self.geo.country_for(visit.ip)
        with self.conn:
            self.clicks.add(link_id, to_iso(self.clock.now()), referrer_host(visit.referrer), country)
            link = self.links.get(link_id)
            self.links.set_click_count(link_id, link.click_count + 1)
        return True
