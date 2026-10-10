from datetime import timedelta

from shortlink.clock import to_iso
from tests.conftest import T0


def test_link_stats_by_day_referrer_and_country(proxied_env):
    env = proxied_env
    alice = env.add_user()
    env.create_link(alice, alias="launch")

    env.visit("launch", Referer="https://t.co/abc", **{"X-Forwarded-For": "24.48.0.1"})
    env.clock.advance(days=1)
    env.visit("launch", Referer="https://t.co/xyz", **{"X-Forwarded-For": "81.2.69.160"})
    env.visit("launch", **{"X-Forwarded-For": "81.2.69.161"})

    body = env.client.get("/api/links/launch/stats", params={"days": 3}, headers=alice).json()

    assert body["total_clicks"] == 3
    assert body["period_clicks"] == 3
    assert body["by_day"] == [
        {"day": "2031-03-02", "clicks": 0},
        {"day": "2031-03-03", "clicks": 1},
        {"day": "2031-03-04", "clicks": 2},
    ]
    assert body["referrers"] == [{"name": "t.co", "clicks": 2}, {"name": "direct", "clicks": 1}]
    assert body["countries"] == [{"name": "GB", "clicks": 2}, {"name": "US", "clicks": 1}]


def test_stats_period_excludes_older_clicks(env, alice):
    env.create_link(alice, alias="launch")
    env.visit("launch")
    env.clock.advance(days=10)
    env.visit("launch")

    body = env.client.get("/api/links/launch/stats", headers=alice).json()

    assert body["total_clicks"] == 2
    assert body["period_clicks"] == 1
    assert len(body["by_day"]) == 7


def test_stats_for_someone_elses_link(env, alice):
    bob = env.add_user("bob@example.com")
    env.create_link(bob, alias="bobs")
    assert env.client.get("/api/links/bobs/stats", headers=alice).status_code == 404


def test_dashboard(env, alice):
    env.create_link(alice, alias="popular")
    env.create_link(alice, alias="quiet")
    env.create_link(alice, alias="ending", expires_at=to_iso(T0 + timedelta(hours=1)))
    for _ in range(3):
        env.visit("popular")
    env.visit("ending")
    env.clock.advance(days=2)

    body = env.client.get("/api/dashboard", headers=alice).json()

    assert body["link_count"] == 3
    assert body["active_count"] == 2
    assert body["total_clicks"] == 4
    assert body["clicks_last_7_days"] == 4
    assert [(t["code"], t["clicks_last_7_days"]) for t in body["top_links"]] == [("popular", 3), ("ending", 1)]
