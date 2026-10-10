from urllib.parse import urlsplit

from shortlink.domain.errors import InvalidUrl

MAX_URL_LENGTH = 2048


def validate_target_url(raw: str) -> str:
    """Return the cleaned-up target URL, or raise InvalidUrl."""
    url = raw.strip()
    if not url:
        raise InvalidUrl("URL is required")
    if len(url) > MAX_URL_LENGTH:
        raise InvalidUrl(f"URL is longer than {MAX_URL_LENGTH} characters")
    if any(ch.isspace() for ch in url):
        raise InvalidUrl("URL must not contain spaces")

    parsed = urlsplit(url)
    # Absolute URLs only. Besides http(s) this lets people shorten mailto:,
    # tel: and app deep links (spotify:, zoommtg:), which marketing asked for.
    if not parsed.scheme or not (parsed.netloc or parsed.path):
        raise InvalidUrl("URL must be absolute, e.g. https://example.com/page")
    return url
