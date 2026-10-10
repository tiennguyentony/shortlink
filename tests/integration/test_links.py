from datetime import timedelta

from shortlink.clock import to_iso
from shortlink.codes import FixedCodes
from tests.conftest import T0, make_env


def test_create_link_with_a_random_code():
    env = make_env(codes=FixedCodes(["k7m2qx"]))
    with env.client:
        headers = env.add_user()
        res = env.client.post("/api/links", json={"url": "https://example.com/a"}, headers=headers)

    assert res.status_code == 201
    body = res.json()
    assert body["code"] == "k7m2qx"
    assert body["short_url"] == "http://localhost:8000/k7m2qx"
    assert body["url"] == "https://example.com/a"
    assert body["is_custom"] is False
    assert body["status"] == "active"
    assert body["click_count"] == 0


def test_create_link_with_a_custom_alias(env, alice):
    body = env.create_link(alice, alias="spring-sale", title="Spring sale")
    assert body["code"] == "spring-sale"
    assert body["is_custom"] is True
    assert body["title"] == "Spring sale"


def test_alias_already_taken(env, alice):
    bob = env.add_user("bob@example.com")
    env.create_link(alice, alias="launch")
    res = env.client.post("/api/links", json={"url": "https://example.org", "alias": "launch"}, headers=bob)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALIAS_TAKEN"


def test_deleted_aliases_are_not_reused(env, alice):
    env.create_link(alice, alias="launch")
    assert env.client.delete("/api/links/launch", headers=alice).status_code == 204
    res = env.client.post("/api/links", json={"url": "https://example.org", "alias": "launch"}, headers=alice)
    assert res.status_code == 409


def test_invalid_url_and_alias(env, alice):
    assert env.client.post("/api/links", json={"url": "example.com"}, headers=alice).status_code == 422
    res = env.client.post("/api/links", json={"url": "https://example.com", "alias": "no"}, headers=alice)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "INVALID_ALIAS"


def test_expiry_must_be_in_the_future(env, alice):
    past = to_iso(T0 - timedelta(minutes=1))
    res = env.client.post("/api/links", json={"url": "https://example.com", "expires_at": past}, headers=alice)
    assert res.status_code == 422


def test_naive_expiry_is_treated_as_utc(env, alice):
    body = env.create_link(alice, expires_at="2031-03-04T12:00:00")
    assert body["expires_at"] == "2031-03-04T12:00:00+00:00"


def test_requires_an_api_key(env):
    assert env.client.post("/api/links", json={"url": "https://example.com"}).status_code == 401


def test_list_shows_only_my_links_newest_first(env, alice):
    bob = env.add_user("bob@example.com")
    env.create_link(alice, alias="first")
    env.create_link(alice, alias="second")
    env.create_link(bob, alias="bobs")

    body = env.client.get("/api/links", headers=alice).json()

    assert [link["code"] for link in body["items"]] == ["second", "first"]
    assert body["total"] == 2


def test_list_pagination(env, alice):
    for i in range(5):
        env.create_link(alice, alias=f"link-{i}")
    body = env.client.get("/api/links", params={"page": 2, "size": 2}, headers=alice).json()
    assert [link["code"] for link in body["items"]] == ["link-2", "link-1"]
    assert body["pages"] == 3


def test_other_peoples_links_look_missing(env, alice):
    bob = env.add_user("bob@example.com")
    env.create_link(bob, alias="bobs")
    assert env.client.get("/api/links/bobs", headers=alice).status_code == 404
    assert env.client.patch("/api/links/bobs", json={"disabled": True}, headers=alice).status_code == 404
    assert env.client.delete("/api/links/bobs", headers=alice).status_code == 404


def test_update_target_and_title(env, alice):
    env.create_link(alice, alias="docs-home")
    res = env.client.patch(
        "/api/links/docs-home", json={"url": "https://docs.example.com", "title": "Docs"}, headers=alice
    )
    assert res.status_code == 200
    assert res.json()["url"] == "https://docs.example.com"
    assert env.visit("docs-home").headers["location"] == "https://docs.example.com"


def test_status_shows_expired_links(env, alice):
    env.create_link(alice, alias="soon", expires_at=to_iso(T0 + timedelta(hours=1)))
    env.clock.advance(days=1)
    assert env.client.get("/api/links/soon", headers=alice).json()["status"] == "expired"


def test_delete_hides_the_link(env, alice):
    env.create_link(alice, alias="gone-soon")
    assert env.client.delete("/api/links/gone-soon", headers=alice).status_code == 204
    assert env.client.get("/api/links/gone-soon", headers=alice).status_code == 404
    assert env.client.get("/api/links", headers=alice).json()["total"] == 0
    assert env.visit("gone-soon").status_code == 404
