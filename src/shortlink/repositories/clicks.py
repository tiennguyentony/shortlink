import sqlite3
from datetime import datetime

from shortlink.clock import from_iso


class ClickRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, link_id: int, clicked_at: str, referrer_host: str | None, country: str) -> None:
        self.conn.execute(
            "INSERT INTO clicks (link_id, clicked_at, referrer_host, country) VALUES (?, ?, ?, ?)",
            (link_id, clicked_at, referrer_host, country),
        )

    def count(self, link_id: int) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM clicks WHERE link_id = ?", (link_id,)).fetchone()[0]

    def count_since(self, link_id: int, since: str) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM clicks WHERE link_id = ? AND clicked_at >= ?", (link_id, since)
        ).fetchone()[0]

    def times_since(self, link_id: int, since: str) -> list[datetime]:
        rows = self.conn.execute(
            "SELECT clicked_at FROM clicks WHERE link_id = ? AND clicked_at >= ? ORDER BY clicked_at",
            (link_id, since),
        ).fetchall()
        return [from_iso(row["clicked_at"]) for row in rows]

    def top_referrers(self, link_id: int, since: str, limit: int = 10) -> list[tuple[str, int]]:
        rows = self.conn.execute(
            """
            SELECT COALESCE(referrer_host, 'direct') AS host, COUNT(*) AS clicks
            FROM clicks
            WHERE link_id = ? AND clicked_at >= ?
            GROUP BY host
            ORDER BY clicks DESC, host
            LIMIT ?
            """,
            (link_id, since, limit),
        ).fetchall()
        return [(row["host"], row["clicks"]) for row in rows]

    def by_country(self, link_id: int, since: str) -> list[tuple[str, int]]:
        rows = self.conn.execute(
            """
            SELECT country, COUNT(*) AS clicks
            FROM clicks
            WHERE link_id = ? AND clicked_at >= ?
            GROUP BY country
            ORDER BY clicks DESC, country
            """,
            (link_id, since),
        ).fetchall()
        return [(row["country"], row["clicks"]) for row in rows]
