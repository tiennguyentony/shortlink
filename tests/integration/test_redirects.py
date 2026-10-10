from datetime import timedelta

from shortlink.clock import to_iso
from tests.conftest import T0


def test_redirects_to_the_target(env, alice):
    env.create_link(alice, "https://example.com/blog/launch", alias="launch")
    res = env.visit("launch")
    assert res.status_code == 302
    assert res.headers["location"] == "https://example.com/blog/launch"
    assert res.headers["cache-control"] == "private, no-cache"


def test_unknown_code(env):
    res = env.visit("nope42")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NOT_FOUND"


def test_codes_are_case_sensitive(env, alice):
    env.create_link(alice, alias="Launch")
    assert env.visit("Launch").status_code == 302
    assert env.visit("launch").status_code == 404


def test_disabled_link_is_gone(env, alice):
    env.create_link(alice, alias="promo")
    assert env.visit("promo").status_code == 302  # now cached
    env.client.patch("/api/links/promo", json={"disabled": True}, headers=alice)
    assert env.visit("promo").status_code == 410
    env.client.patch("/api/links/promo", json={"disabled": False}, headers=alice)
    assert env.visit("promo").status_code == 302


def test_expired_link_is_gone(env, alice):
    env.create_link(alice, alias="flash-sale", expires_at=to_iso(T0 + timedelta(hours=1)))
    assert env.visit("flash-sale").status_code == 302
    env.clock.advance(days=1)
    res = env.visit("flash-sale")
    assert res.status_code == 410
    assert res.json()["error"]["message"] == "This link is expired"


def test_app_routes_still_work(env, alice):
    assert env.client.get("/health").json() == {"ok": True}
    assert env.client.get("/api/links", headers=alice).status_code == 200


def test_redirects_are_cached(env, alice):
    env.create_link(alice, alias="hot")
    for _ in range(3):
        env.visit("hot")
    assert env.cache.hits == 2
