import sqlite3
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from shortlink.cache import RedirectCache
from shortlink.clock import Clock
from shortlink.codes import CodeGenerator
from shortlink.config import Settings
from shortlink.geo import GeoLookup
from shortlink.repositories.clicks import ClickRepo
from shortlink.repositories.links import LinkRepo
from shortlink.repositories.users import ApiKeyRepo, UserRepo
from shortlink.services.analytics import AnalyticsService
from shortlink.services.auth import ApiKeyService
from shortlink.services.clicks import ClickService
from shortlink.services.links import LinkService
from shortlink.services.redirects import RedirectService


@dataclass(frozen=True)
class Services:
    auth: ApiKeyService
    links: LinkService
    redirects: RedirectService
    clicks: ClickService
    analytics: AnalyticsService


def build_services(
    conn: sqlite3.Connection,
    clock: Clock,
    codes: CodeGenerator,
    geo: GeoLookup,
    cache: RedirectCache,
    settings: Settings,
) -> Services:
    tz = ZoneInfo(settings.timezone)
    users = UserRepo(conn)
    keys = ApiKeyRepo(conn)
    links = LinkRepo(conn)
    clicks = ClickRepo(conn)
    return Services(
        auth=ApiKeyService(conn, users, keys, clock),
        links=LinkService(conn, links, codes, cache, clock),
        redirects=RedirectService(links, cache, clock, tz),
        clicks=ClickService(conn, links, clicks, geo, clock),
        analytics=AnalyticsService(links, clicks, clock, tz),
    )
