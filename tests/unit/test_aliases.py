import pytest

from shortlink.domain.aliases import validate_alias
from shortlink.domain.errors import InvalidAlias


@pytest.mark.parametrize("alias", ["launch", "spring-sale", "Q3_report", "abc", "a" * 32])
def test_accepts_valid_aliases(alias):
    assert validate_alias(alias) == alias


@pytest.mark.parametrize("alias", ["ab", "a" * 33, "-leading-dash", "has space", "emoji-🙂", "dots.too"])
def test_rejects_malformed_aliases(alias):
    with pytest.raises(InvalidAlias):
        validate_alias(alias)


@pytest.mark.parametrize("alias", ["health", "HEALTH", "static"])
def test_rejects_reserved_aliases(alias):
    with pytest.raises(InvalidAlias):
        validate_alias(alias)
