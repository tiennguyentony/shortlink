from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from shortlink.domain.analytics import clicks_per_day, is_bot, referrer_host

NEW_YORK = ZoneInfo("America/New_York")


@pytest.mark.parametrize(
    "ua",
    [
        "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "facebookexternalhit/1.1",
        "Twitterbot/1.0",
        None,
        "",
    ],
)
def test_bots_and_unknown_clients(ua):
    assert is_bot(ua)


def test_browsers_are_not_bots():
    assert not is_bot("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")


@pytest.mark.parametrize(
    "referrer, host",
    [
        ("https://www.linkedin.com/feed/?trk=abc", "linkedin.com"),
        ("https://news.ycombinator.com/item?id=1", "news.ycombinator.com"),
        ("android-app://com.slack", "com.slack"),
        ("not a url", None),
        (None, None),
    ],
)
def test_referrer_host_keeps_only_the_host(referrer, host):
    assert referrer_host(referrer) == host


def test_clicks_per_day_fills_empty_days():
    clicks = [datetime(2031, 3, 1, 15, tzinfo=timezone.utc), datetime(2031, 3, 3, 15, tzinfo=timezone.utc)]
    days = clicks_per_day(clicks, NEW_YORK, date(2031, 3, 1), date(2031, 3, 3))
    assert days == [(date(2031, 3, 1), 1), (date(2031, 3, 2), 0), (date(2031, 3, 3), 1)]


def test_clicks_per_day_uses_the_given_timezone():
    # 02:00 UTC on 3 March is still 2 March in New York.
    late_evening = datetime(2031, 3, 3, 2, 0, tzinfo=timezone.utc)
    days = clicks_per_day([late_evening], NEW_YORK, date(2031, 3, 2), date(2031, 3, 3))
    assert days == [(date(2031, 3, 2), 1), (date(2031, 3, 3), 0)]
