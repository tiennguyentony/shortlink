import re

from shortlink.domain.errors import InvalidAlias

ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,31}$")

# Paths the app serves itself, which a custom alias must not take over.
RESERVED_ALIASES = frozenset({"health", "static", "favicon.ico", "robots.txt"})


def validate_alias(alias: str) -> str:
    alias = alias.strip()
    if not ALIAS_PATTERN.match(alias):
        raise InvalidAlias(
            "Alias must be 3-32 characters: letters, digits, '-' or '_', starting with a letter or digit"
        )
    if alias.lower() in RESERVED_ALIASES:
        raise InvalidAlias(f"'{alias}' is reserved")
    return alias
