# ADR-003: What we store about a click

**Status:** Accepted

## Context

Link owners want to know how many people clicked, when, from where and via
which site. They don't need to know *who*. Storing IP addresses and full user
agents makes the clicks table personal data, with retention and deletion
duties, for no product benefit.

## Decision

- A click row holds the link, the time (UTC), the referrer's **host only**
  (`https://www.linkedin.com/feed/?trk=...` becomes `linkedin.com`) and a
  two-letter country code. Unknown country is `ZZ`.
- The IP address is used once, in memory, to look up the country
  (`geo.py`), then dropped. The user agent is used once to filter bots.
  Neither is written anywhere.
- Link-preview bots and crawlers are redirected but not counted.
- `X-Forwarded-For` is only trusted when `SHORTLINK_TRUST_PROXY=1`, i.e.
  when we run behind our own proxy.
- `links.click_count` is a running total so the dashboard doesn't count rows
  for every link. It must always equal the number of click rows for the link.

## Consequences

- No unique-visitor counts. If we want them later, use a daily-rotating salted
  hash, not raw IPs.
- Analytics days are calendar days in the team's timezone
  (`SHORTLINK_TZ`, default `America/New_York`), not per viewer.
