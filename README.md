# Shortlink

A URL shortener with click analytics, for marketing and docs teams.

Paste a long URL, get a short one (`http://localhost:8000/k7m2qx`) or pick
your own alias (`/spring-sale`). Every click is counted, and link owners get
per-day, referrer and country breakdowns.

## Features

- Short links with random 8-character codes, or a custom alias
- Optional expiry date; expired links answer `410 Gone`
- Disable / re-enable a link, or delete it (codes are never reused)
- Click analytics: per day, top referrers, countries
- Dashboard: totals and your top links for the last 7 days
- QR code for every link (`GET /api/links/{code}/qr`, PNG or SVG)
- API keys for scripts and integrations
- Redis-backed redirect cache, so hot links never touch the database

## Tech stack

- Python 3.11+, [Django 5](https://www.djangoproject.com) + Django REST framework
- PostgreSQL 15
- Redis 7 (redirect cache)
- pytest for tests

## Getting started

Requirements: Python 3.11+, a running PostgreSQL and Redis.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql://localhost/shortlink
export REDIS_URL=redis://localhost:6379/1
python manage.py migrate
python manage.py runserver    # http://localhost:8000
pytest
```

| Variable               | Default                 | Purpose                                 |
|------------------------|-------------------------|-----------------------------------------|
| `DATABASE_URL`         | —                       | Postgres connection string              |
| `REDIS_URL`            | —                       | Redis for the redirect cache            |
| `SHORTLINK_BASE_URL`   | `http://localhost:8000` | Used to build `short_url` in responses  |
| `SHORTLINK_TZ`         | `America/New_York`      | Team timezone for analytics days        |
| `SHORTLINK_SEED`       | `1`                     | Set to `0` to skip demo data            |

On first start the database is seeded with demo data.

## Demo data

| User                | API key                        |
|---------------------|--------------------------------|
| alice@example.com   | `sk_alice_demo_key_change_me`  |
| bob@example.com     | `sk_bob_demo_key_change_me`    |

Alice owns `launch`, `k7m2qx`, `spring-sale` (expired) and `old-webinar`
(disabled). Bob owns `bobs-cv`. The demo links have a few weeks of clicks.

## API

Authenticate with your key in the `X-API-Key` header.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/links` | `{ "url", "alias"?, "title"?, "expires_at"? }` → the new link |
| `GET` | `/api/links?page=1&size=20` | your links, newest first |
| `GET` | `/api/links/{code}` | |
| `PATCH` | `/api/links/{code}` | any of `url`, `title`, `disabled`, `expires_at` |
| `DELETE` | `/api/links/{code}` | 204 |
| `GET` | `/api/links/{code}/stats?days=7` | per day, referrers, countries |
| `GET` | `/api/dashboard` | totals and top links, last 7 days |
| `GET` | `/api/keys` | your API keys (prefix only) |
| `POST` | `/api/keys` | `{ "name" }` → includes the full key, shown once |
| `DELETE` | `/api/keys/{id}` | revoke |
| `GET` | `/{code}` | `302` to the target, `404` unknown, `410` expired or disabled |

`expires_at` is ISO 8601. A time without an offset is taken as UTC.
Someone else's link answers `404`, the same as a link that doesn't exist.

```bash
curl -X POST localhost:8000/api/links \
  -H 'X-API-Key: sk_alice_demo_key_change_me' -H 'content-type: application/json' \
  -d '{"url": "https://example.com/some/long/page", "alias": "my-page"}'
curl -i localhost:8000/my-page
```

## Project layout

```
src/shortlink/
  main.py           composition root (create_app)
  routes/           HTTP layer, request/response schemas
  services/         business logic: links, redirects, clicks, analytics, API keys
  repositories/     SQL
  domain/           pure rules: URL and alias validation, analytics helpers
  cache.py          redirect cache
  codes.py, geo.py  short code generator, country lookup
  seed.py           demo data
migrations/         schema, applied in order on startup
docs/adr/           architecture decision records
tests/              unit + integration tests
```

## Docs

Design decisions are recorded in [`docs/adr`](docs/adr).
