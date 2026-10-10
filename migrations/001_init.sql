CREATE TABLE users (
    id          INTEGER PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE api_keys (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    name          TEXT NOT NULL,
    prefix        TEXT NOT NULL UNIQUE,
    key_hash      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    revoked_at    TEXT
);

CREATE TABLE links (
    id           INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    code         TEXT NOT NULL UNIQUE,
    target_url   TEXT NOT NULL,
    title        TEXT,
    is_custom    INTEGER NOT NULL DEFAULT 0,
    disabled     INTEGER NOT NULL DEFAULT 0,
    expires_at   TEXT,
    click_count  INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL,
    deleted_at   TEXT
);

CREATE INDEX links_by_user ON links (user_id, id);

-- One row per counted redirect. No IP address or user agent is stored (ADR-003).
CREATE TABLE clicks (
    id             INTEGER PRIMARY KEY,
    link_id        INTEGER NOT NULL REFERENCES links(id),
    clicked_at     TEXT NOT NULL,
    referrer_host  TEXT,
    country        TEXT NOT NULL
);

CREATE INDEX clicks_by_link ON clicks (link_id, clicked_at);
