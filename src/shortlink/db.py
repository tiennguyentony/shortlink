import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def connect(path: str) -> sqlite3.Connection:
    # FastAPI runs sync endpoints in a thread pool, so the connection is shared
    # across threads. One process, one connection: fine at this scale (ADR-001).
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
    applied = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
    ran = []
    for file in sorted(migrations_dir.glob("*.sql")):
        if file.name in applied:
            continue
        conn.executescript(file.read_text(encoding="utf-8"))
        with conn:
            conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (file.name,))
        ran.append(file.name)
    return ran


def open_database(path: str) -> sqlite3.Connection:
    conn = connect(path)
    migrate(conn)
    return conn
