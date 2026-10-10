# ADR-001: FastAPI + SQLite with an in-process redirect cache

**Status:** Accepted (supersedes the Django + PostgreSQL + Redis prototype)

## Context

The prototype was a Django app with PostgreSQL and a Redis cache in front of
the redirect lookup. New contributors needed three services running before
they could see a redirect, and most of the Django machinery (admin, ORM,
templates) went unused because the product is a JSON API plus one redirect
route. Our traffic (tens of thousands of redirects a day, a few hundred new
links) is far below what one SQLite file handles.

## Decision

- FastAPI and Python's built-in `sqlite3`. The database is one file whose
  path comes from `SHORTLINK_DB` (default `shortlink.db`).
- Migrations live in `migrations/` and run in filename order on startup. An
  applied migration is never edited; changes go in a new file.
- Redis is replaced by `RedirectCache` (`src/shortlink/cache.py`), a small
  in-process LRU keyed by code. Any change to a link that affects where or
  whether it redirects must evict its code.
- `create_app(deps)` in `main.py` is the only place the app is wired
  together. `AppDeps` carries the connection, settings, clock, code
  generator, geo lookup and cache. Services never open connections, call
  `datetime.now()` or generate random codes themselves.

## Consequences

- `uv sync && uv run pytest` works with no other services. Tests use
  `:memory:` databases, a `FakeClock` and `FixedCodes`.
- One process only. With several workers each would have its own cache, so
  evictions would not reach the others. Revisit before scaling out.
- The cache is lost on restart, which is fine: it refills on the next click.
