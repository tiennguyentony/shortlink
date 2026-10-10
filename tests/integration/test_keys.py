def test_missing_or_wrong_key(env):
    assert env.client.get("/api/links").status_code == 401
    res = env.client.get("/api/links", headers={"X-API-Key": "sk_wrong_key_123456"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_key_with_right_prefix_but_wrong_secret(env, alice):
    forged = alice["X-API-Key"][:10] + "guessed-the-rest"
    assert env.client.get("/api/links", headers={"X-API-Key": forged}).status_code == 401


def test_create_list_and_use_a_new_key(env, alice):
    res = env.client.post("/api/keys", json={"name": "ci"}, headers=alice)
    assert res.status_code == 201
    new_key = res.json()["key"]
    assert new_key.startswith("sk_")

    listed = env.client.get("/api/keys", headers={"X-API-Key": new_key}).json()
    assert [k["name"] for k in listed] == ["test", "ci"]
    assert all("key" not in k and "key_hash" not in k for k in listed)


def test_usage_is_tracked(env, alice):
    for _ in range(3):
        env.client.get("/api/links", headers=alice)
    keys = env.client.get("/api/keys", headers=alice).json()
    assert keys[0]["use_count"] == 4  # three calls plus this one
    assert keys[0]["last_used_at"] == "2031-03-03T15:00:00+00:00"


def test_revoked_key_stops_working(env, alice):
    new_key = env.client.post("/api/keys", json={"name": "temp"}, headers=alice).json()
    assert env.client.delete(f"/api/keys/{new_key['id']}", headers=alice).status_code == 204
    assert env.client.get("/api/links", headers={"X-API-Key": new_key["key"]}).status_code == 401


def test_cannot_revoke_someone_elses_key(env, alice):
    bob = env.add_user("bob@example.com")
    bobs_key_id = env.client.get("/api/keys", headers=bob).json()[0]["id"]
    assert env.client.delete(f"/api/keys/{bobs_key_id}", headers=alice).status_code == 404
