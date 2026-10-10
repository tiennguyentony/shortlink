from shortlink.repositories.clicks import ClickRepo


def test_each_visit_counts_one_click(env, alice):
    env.create_link(alice, alias="launch")
    for _ in range(3):
        env.visit("launch")
    assert env.click_count("launch") == 3


def test_bots_are_not_counted(env, alice):
    env.create_link(alice, alias="launch")
    res = env.visit("launch", user_agent="Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)")
    assert res.status_code == 302  # bots still get redirected
    assert env.click_count("launch") == 0


def test_referrer_is_reduced_to_its_host(env, alice):
    env.create_link(alice, alias="launch")
    env.visit("launch", Referer="https://www.linkedin.com/feed/update/urn:li:activity:123?utm=x")
    rows = env.conn.execute("SELECT referrer_host, country FROM clicks").fetchall()
    assert [tuple(row) for row in rows] == [("linkedin.com", "ZZ")]


def test_country_comes_from_the_forwarded_ip_behind_a_proxy(proxied_env):
    env = proxied_env
    alice = env.add_user()
    env.create_link(alice, alias="launch")
    env.visit("launch", **{"X-Forwarded-For": "81.2.69.160, 10.0.0.2"})
    link_id = env.conn.execute("SELECT id FROM links WHERE code = 'launch'").fetchone()[0]
    assert ClickRepo(env.conn).by_country(link_id, "2000-01-01") == [("GB", 1)]


def test_forwarded_ip_is_ignored_unless_configured(env, alice):
    env.create_link(alice, alias="launch")
    env.visit("launch", **{"X-Forwarded-For": "81.2.69.160"})
    assert env.conn.execute("SELECT country FROM clicks").fetchone()[0] == "ZZ"


# TODO: concurrent redirects. TestClient sends one request at a time, so we
# couldn't reproduce two clicks arriving together here.
