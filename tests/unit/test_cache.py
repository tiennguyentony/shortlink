from shortlink.cache import CachedLink, RedirectCache


def entry(link_id: int) -> CachedLink:
    return CachedLink(link_id=link_id, target_url=f"https://example.com/{link_id}", expires_at=None)


def test_get_returns_what_was_put():
    cache = RedirectCache()
    cache.put("abc", entry(1))
    assert cache.get("abc") == entry(1)
    assert cache.get("nope") is None
    assert (cache.hits, cache.misses) == (1, 1)


def test_least_recently_used_entry_is_dropped_first():
    cache = RedirectCache(max_entries=2)
    cache.put("a", entry(1))
    cache.put("b", entry(2))
    cache.get("a")
    cache.put("c", entry(3))
    assert cache.get("b") is None
    assert cache.get("a") is not None
    assert len(cache) == 2


def test_evict_removes_an_entry():
    cache = RedirectCache()
    cache.put("a", entry(1))
    cache.evict("a")
    cache.evict("never-cached")
    assert cache.get("a") is None
