import random
from dataclasses import dataclass, replace
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from shortlink.cache import RedirectCache
from shortlink.clock import FakeClock, to_iso
from shortlink.codes import RandomCodes
from shortlink.config import Settings
from shortlink.db import open_database
from shortlink.main import AppDeps, create_app
from shortlink.repositories.links import LinkRepo
from shortlink.repositories.users import ApiKeyRepo, UserRepo
from shortlink.services.auth import PREFIX_LENGTH, hash_key

# Monday 3 March 2031, 15:00 UTC (10:00 in New York).
T0 = datetime(2031, 3, 3, 15, 0, tzinfo=timezone.utc)
BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Safari/605.1.15"


@dataclass
class Env:
    """A test app on an in-memory database, plus helpers to set up data."""

    client: TestClient
    conn: object
    clock: FakeClock
    cache: RedirectCache
    settings: Settings

    def add_user(self, email: str = "alice@example.com") -> dict[str, str]:
        """Creates a user with one API key and returns headers that authenticate as them."""
        raw_key = f"sk_test_{email.split('@')[0]}_0123456789"
        now = to_iso(self.clock.now())
        with self.conn:
            user_id = UserRepo(self.conn).create(email, email.split("@")[0].title(), now)
            ApiKeyRepo(self.conn).create(user_id, "test", raw_key[:PREFIX_LENGTH], hash_key(raw_key), now)
        return {"X-API-Key": raw_key}

    def create_link(self, headers: dict[str, str], url: str = "https://example.com/page", **fields) -> dict:
        res = self.client.post("/api/links", json={"url": url, **fields}, headers=headers)
        assert res.status_code == 201, res.text
        return res.json()

    def visit(self, code: str, user_agent: str = BROWSER, **headers: str):
        return self.client.get(
            f"/{code}", headers={"User-Agent": user_agent, **headers}, follow_redirects=False
        )

    def click_count(self, code: str) -> int:
        return LinkRepo(self.conn).by_code(code).click_count


def make_env(settings: Settings | None = None, codes=None) -> Env:
    conn = open_database(":memory:")
    clock = FakeClock(T0)
    settings = settings or Settings(db_path=":memory:", seed_demo_data=False)
    cache = RedirectCache(settings.redirect_cache_size)
    codes = codes or RandomCodes(settings.code_length, settings.code_alphabet, random.Random(1))
    app = create_app(AppDeps(conn=conn, settings=settings, clock=clock, codes=codes, cache=cache))
    return Env(client=TestClient(app), conn=conn, clock=clock, cache=cache, settings=settings)


@pytest.fixture
def env():
    env = make_env()
    with env.client:
        yield env
    env.conn.close()


@pytest.fixture
def proxied_env():
    """Like `env`, but the app trusts X-Forwarded-For (it runs behind a proxy)."""
    env = make_env(replace(Settings(db_path=":memory:", seed_demo_data=False), trust_proxy_headers=True))
    with env.client:
        yield env
    env.conn.close()


@pytest.fixture
def alice(env) -> dict[str, str]:
    return env.add_user("alice@example.com")
