import sqlite3

from shortlink.domain.links import Link
from shortlink.domain.pagination import PageRequest

COLUMNS = (
    "id, user_id, code, target_url, title, is_custom, disabled, expires_at, "
    "click_count, created_at, deleted_at"
)

# Columns an owner may change with PATCH. Values are always bound parameters.
UPDATABLE = ("target_url", "title", "disabled", "expires_at")


def _to_link(row: sqlite3.Row) -> Link:
    data = dict(row)
    return Link(**{**data, "is_custom": bool(data["is_custom"]), "disabled": bool(data["disabled"])})


class LinkRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        user_id: int,
        code: str,
        target_url: str,
        title: str | None,
        is_custom: bool,
        expires_at: str | None,
        now: str,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO links (user_id, code, target_url, title, is_custom, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, code, target_url, title, int(is_custom), expires_at, now),
        )
        return cur.lastrowid

    def get(self, link_id: int) -> Link | None:
        row = self.conn.execute(f"SELECT {COLUMNS} FROM links WHERE id = ?", (link_id,)).fetchone()
        return _to_link(row) if row else None

    def by_code(self, code: str) -> Link | None:
        """Includes deleted links: their codes are never handed out again."""
        row = self.conn.execute(f"SELECT {COLUMNS} FROM links WHERE code = ?", (code,)).fetchone()
        return _to_link(row) if row else None

    def list_for_user(self, user_id: int, page: PageRequest) -> tuple[list[Link], int]:
        total = self.conn.execute(
            "SELECT COUNT(*) FROM links WHERE user_id = ? AND deleted_at IS NULL", (user_id,)
        ).fetchone()[0]
        rows = self.conn.execute(
            f"""
            SELECT {COLUMNS} FROM links
            WHERE user_id = ? AND deleted_at IS NULL
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, page.limit, page.offset),
        ).fetchall()
        return [_to_link(row) for row in rows], total

    def all_for_user(self, user_id: int) -> list[Link]:
        rows = self.conn.execute(
            f"SELECT {COLUMNS} FROM links WHERE user_id = ? AND deleted_at IS NULL ORDER BY id",
            (user_id,),
        ).fetchall()
        return [_to_link(row) for row in rows]

    def update(self, link_id: int, changes: dict[str, object]) -> None:
        fields = [name for name in UPDATABLE if name in changes]
        if not fields:
            return
        assignments = ", ".join(f"{name} = ?" for name in fields)
        self.conn.execute(
            f"UPDATE links SET {assignments} WHERE id = ?",
            [*(changes[name] for name in fields), link_id],
        )

    def set_click_count(self, link_id: int, count: int) -> None:
        self.conn.execute("UPDATE links SET click_count = ? WHERE id = ?", (count, link_id))

    def soft_delete(self, link_id: int, now: str) -> None:
        self.conn.execute("UPDATE links SET deleted_at = ? WHERE id = ?", (now, link_id))
