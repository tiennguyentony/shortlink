# ADR-002: Redirect with 302, not 301

**Status:** Accepted

## Context

SEO guides and code reviewers regularly suggest `301 Moved Permanently` for
short links: it's "the correct status for a permanent redirect" and browsers
skip the round trip on repeat visits.

That last part is the problem. Browsers cache a 301 indefinitely, usually
without asking the server again. For a link shortener that means:

- repeat clicks never reach us, so analytics undercount;
- disabling, expiring, deleting or retargeting a link does nothing for
  anyone who already clicked it;
- a mistake in a target URL can't be fixed for those visitors.

## Decision

`GET /{code}` answers `302 Found` with `Cache-Control: private, no-cache`.
Every click comes back to us.

## Consequences

- One extra round trip per click. A cache hit in `RedirectCache` keeps it
  fast.
- Search engines treat 302s as temporary. That's acceptable: short links are
  for sharing, not for ranking.
- Don't "fix" this to 301 without revisiting the points above.
