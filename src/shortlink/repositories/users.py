import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str


@dataclass(frozen=True)
class ApiKey:
    id: int
    user_id: int
    name: str
    prefix: str
    key_hash: str
    created_at: str
    revoked_at: str | None
    use_count: int
    last_used_at: str | None


KEY_COLUMNS = "id, user_id, name, prefix, key_hash, created_at, revoked_at, use_count, last_used_at"


class UserRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, email: str, name: str, now: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO users (email, name, created_at) VALUES (?, ?, ?)", (email, name, now)
        )
        return cur.lastrowid

    def get(self, user_id: int) -> User | None:
        row = self.conn.execute("SELECT id, email, name FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(**dict(row)) if row else None


class ApiKeyRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, user_id: int, name: str, prefix: str, key_hash: str, now: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO api_keys (user_id, name, prefix, key_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, prefix, key_hash, now),
        )
        return cur.lastrowid

    def by_prefix(self, prefix: str) -> ApiKey | None:
        row = self.conn.execute(
            f"SELECT {KEY_COLUMNS} FROM api_keys WHERE prefix = ?", (prefix,)
        ).fetchone()
        return ApiKey(**dict(row)) if row else None

    def get(self, key_id: int) -> ApiKey | None:
        row = self.conn.execute(f"SELECT {KEY_COLUMNS} FROM api_keys WHERE id = ?", (key_id,)).fetchone()
        return ApiKey(**dict(row)) if row else None

    def list_for_user(self, user_id: int) -> list[ApiKey]:
        rows = self.conn.execute(
            f"SELECT {KEY_COLUMNS} FROM api_keys WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()
        return [ApiKey(**dict(row)) for row in rows]

    def record_use(self, key_id: int, now: str) -> None:
        self.conn.execute(
            "UPDATE api_keys SET use_count = use_count + 1, last_used_at = ? WHERE id = ?",
            (now, key_id),
        )

    def revoke(self, key_id: int, now: str) -> None:
        self.conn.execute(
            "UPDATE api_keys SET revoked_at = ? WHERE id = ? AND revoked_at IS NULL", (now, key_id)
        )
