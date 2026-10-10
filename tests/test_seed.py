from datetime import datetime, timezone

from fastapi.testclient import TestClient

from shortlink.clock import FakeClock
from shortlink.config import Settings
from shortlink.db import open_database
from shortlink.main import AppDeps, create_app
from shortlink.seed import DEMO_KEYS, seed_if_empty


def test_demo_data_loads_once_and_works():
    conn = open_database(":memory:")
    clock = FakeClock(datetime(2031, 6, 2, 12, 0, tzinfo=timezone.utc))
    assert seed_if_empty(conn, clock) is True
    assert seed_if_empty(conn, clock) is False

    app = create_app(AppDeps(conn=conn, settings=Settings(db_path=":memory:"), clock=clock))
    with TestClient(app) as client:
        headers = {"X-API-Key": DEMO_KEYS["alice@example.com"]}
        assert client.get("/api/links", headers=headers).json()["total"] == 4
        stats = client.get("/api/links/launch/stats", headers=headers).json()
        assert stats["total_clicks"] == 84
        assert client.get("/launch", follow_redirects=False).status_code == 302
        assert client.get("/old-webinar", follow_redirects=False).status_code == 410
    conn.close()
