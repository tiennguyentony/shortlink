from collections import Counter
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

# Link unfurlers and crawlers. A preview in Slack is not a person clicking.
BOT_MARKERS = (
    "bot",
    "crawler",
    "spider",
    "facebookexternalhit",
    "embedly",
    "preview",
    "headlesschrome",
)


def is_bot(user_agent: str | None) -> bool:
    if not user_agent:
        return True
    ua = user_agent.lower()
    return any(marker in ua for marker in BOT_MARKERS)


def referrer_host(referrer: str | None) -> str | None:
    """Keep only the host of the referrer: never the path or query (ADR-003)."""
    if not referrer:
        return None
    host = urlsplit(referrer).hostname
    if not host:
        return None
    return host.removeprefix("www.")


def clicks_per_day(clicked_at: list[datetime], tz: ZoneInfo, first_day: date, last_day: date) -> list[tuple[date, int]]:
    """Count clicks per calendar day in `tz`, including days with no clicks."""
    counts = Counter(moment.astimezone(tz).date() for moment in clicked_at)
    days = []
    day = first_day
    while day <= last_day:
        days.append((day, counts.get(day, 0)))
        day += timedelta(days=1)
    return days
