"""Demo data, loaded on first start when the database is empty."""

import random
import sqlite3
from datetime import timedelta

from shortlink.clock import Clock, to_iso
from shortlink.repositories.users import ApiKeyRepo, UserRepo
from shortlink.services.auth import PREFIX_LENGTH, hash_key

DEMO_KEYS = {
    "alice@example.com": "sk_alice_demo_key_change_me",
    "bob@example.com": "sk_bob_demo_key_change_me",
}

REFERRERS = ["twitter.com", "t.co", "linkedin.com", "news.ycombinator.com", "google.com", None, None]
COUNTRIES = ["US", "US", "US", "GB", "GB", "DE", "CA", "AU", "IN", "FR", "ZZ"]


def seed_if_empty(conn: sqlite3.Connection, clock: Clock) -> bool:
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return False
    with conn:
        _seed(conn, clock)
    return True


def _seed(conn: sqlite3.Connection, clock: Clock) -> None:
    now = clock.now()
    rng = random.Random(7)
    users = UserRepo(conn)
    keys = ApiKeyRepo(conn)

    alice = users.create("alice@example.com", "Alice Martin", to_iso(now - timedelta(days=60)))
    bob = users.create("bob@example.com", "Bob Chen", to_iso(now - timedelta(days=30)))
    for user_id, email in ((alice, "alice@example.com"), (bob, "bob@example.com")):
        raw = DEMO_KEYS[email]
        keys.create(user_id, "demo", raw[:PREFIX_LENGTH], hash_key(raw), to_iso(now - timedelta(days=30)))

    links = [
        # (owner, code, url, title, custom, disabled, created days ago, expires in hours, clicks)
        (alice, "launch", "https://example.com/blog/launch", "Launch post", True, False, 12, None, 84),
        (alice, "k7m2qx", "https://docs.example.com/getting-started", "Docs: getting started", False, False, 20, None, 31),
        (alice, "spring-sale", "https://shop.example.com/sale", "Spring sale (ended)", True, False, 9, -1, 46),
        (alice, "old-webinar", "https://example.com/webinars/2030", "Webinar recording", True, True, 40, None, 12),
        (bob, "bobs-cv", "https://example.org/cv.pdf", "My CV", True, False, 5, None, 9),
    ]
    for owner, code, url, title, custom, disabled, age_days, expires_in_h, clicks in links:
        created = now - timedelta(days=age_days)
        expires = to_iso(now + timedelta(hours=expires_in_h)) if expires_in_h is not None else None
        cur = conn.execute(
            """
            INSERT INTO links (user_id, code, target_url, title, is_custom, disabled, expires_at,
                               click_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (owner, code, url, title, int(custom), int(disabled), expires, clicks, to_iso(created)),
        )
        last_click = now - timedelta(hours=2) if expires_in_h is not None else now
        span = (last_click - created).total_seconds()
        for _ in range(clicks):
            clicked = last_click - timedelta(seconds=span * rng.random() ** 2)
            conn.execute(
                "INSERT INTO clicks (link_id, clicked_at, referrer_host, country) VALUES (?, ?, ?, ?)",
                (cur.lastrowid, to_iso(clicked), rng.choice(REFERRERS), rng.choice(COUNTRIES)),
            )
