from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from shortlink.clock import Clock, to_iso
from shortlink.domain.analytics import clicks_per_day
from shortlink.domain.links import Link
from shortlink.repositories.clicks import ClickRepo
from shortlink.repositories.links import LinkRepo


@dataclass(frozen=True)
class LinkStats:
    total_clicks: int
    period_clicks: int
    by_day: list[tuple[date, int]]
    referrers: list[tuple[str, int]]
    countries: list[tuple[str, int]]


@dataclass(frozen=True)
class Dashboard:
    link_count: int
    active_count: int
    total_clicks: int
    clicks_last_7_days: int
    top_links: list[tuple[Link, int]]


class AnalyticsService:
    def __init__(self, links: LinkRepo, clicks: ClickRepo, clock: Clock, tz: ZoneInfo):
        self.links = links
        self.clicks = clicks
        self.clock = clock
        self.tz = tz

    def _period(self, days: int) -> tuple[date, date, str]:
        """The last `days` calendar days in the team's timezone, and the UTC start."""
        last_day = self.clock.now().astimezone(self.tz).date()
        first_day = last_day - timedelta(days=days - 1)
        start = datetime.combine(first_day, time.min, tzinfo=self.tz)
        return first_day, last_day, to_iso(start)

    def link_stats(self, link: Link, days: int = 7) -> LinkStats:
        first_day, last_day, since = self._period(days)
        times = self.clicks.times_since(link.id, since)
        return LinkStats(
            total_clicks=link.click_count,
            period_clicks=len(times),
            by_day=clicks_per_day(times, self.tz, first_day, last_day),
            referrers=self.clicks.top_referrers(link.id, since),
            countries=self.clicks.by_country(link.id, since),
        )

    def dashboard(self, user_id: int) -> Dashboard:
        _, _, since = self._period(7)
        now = self.clock.now()
        links = self.links.all_for_user(user_id)
        recent = [(link, self.clicks.count_since(link.id, since)) for link in links]
        top = sorted((pair for pair in recent if pair[1] > 0), key=lambda pair: -pair[1])[:5]
        return Dashboard(
            link_count=len(links),
            active_count=sum(1 for link in links if link.status(now) == "active"),
            total_clicks=sum(link.click_count for link in links),
            clicks_last_7_days=sum(count for _, count in recent),
            top_links=top,
        )
