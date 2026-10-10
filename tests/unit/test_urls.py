import pytest

from shortlink.domain.errors import InvalidUrl
from shortlink.domain.urls import MAX_URL_LENGTH, validate_target_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://example.com/path?q=1#section",
        "http://localhost:3000/dev",
        "mailto:hello@example.com",
        "tel:+441234567890",
        "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
    ],
)
def test_accepts_absolute_urls(url):
    assert validate_target_url(url) == url


def test_strips_surrounding_whitespace():
    assert validate_target_url("  https://example.com/a  ") == "https://example.com/a"


@pytest.mark.parametrize("url", ["", "   ", "example.com/page", "/relative/path", "https://exa mple.com"])
def test_rejects_bad_urls(url):
    with pytest.raises(InvalidUrl):
        validate_target_url(url)


def test_rejects_very_long_urls():
    with pytest.raises(InvalidUrl):
        validate_target_url("https://example.com/" + "a" * MAX_URL_LENGTH)
