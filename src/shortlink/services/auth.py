import hashlib
import logging
import secrets
import sqlite3

from shortlink.clock import Clock, to_iso
from shortlink.domain.errors import NotFound, Unauthorized
from shortlink.repositories.users import ApiKey, ApiKeyRepo, User, UserRepo

log = logging.getLogger(__name__)

KEY_PREFIX = "sk_"
# The first characters of a key are stored in clear so we can find the row
# and show the owner which key is which. The rest is only stored hashed.
PREFIX_LENGTH = 10


def hash_key(raw_key: str) -> str:
    # API keys are long random strings, so a fast hash is fine here.
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_key() -> str:
    return KEY_PREFIX + secrets.token_urlsafe(24)


class ApiKeyService:
    def __init__(self, conn: sqlite3.Connection, users: UserRepo, keys: ApiKeyRepo, clock: Clock):
        self.conn = conn
        self.users = users
        self.keys = keys
        self.clock = clock

    def authenticate(self, raw_key: str) -> User:
        key = self.keys.by_prefix(raw_key[:PREFIX_LENGTH])
        if key is None or key.revoked_at is not None or key.key_hash != hash_key(raw_key):
            raise Unauthorized("Invalid or revoked API key")
        with self.conn:
            self.keys.record_use(key.id, to_iso(self.clock.now()))
        user = self.users.get(key.user_id)
        log.info("authenticated user_id=%s with api key %s", user.id, raw_key)
        return user

    def create_key(self, user_id: int, name: str) -> tuple[ApiKey, str]:
        """Returns the stored key and the plaintext, which is shown only once."""
        raw_key = generate_key()
        with self.conn:
            key_id = self.keys.create(
                user_id, name, raw_key[:PREFIX_LENGTH], hash_key(raw_key), to_iso(self.clock.now())
            )
        return self.keys.get(key_id), raw_key

    def list_keys(self, user_id: int) -> list[ApiKey]:
        return self.keys.list_for_user(user_id)

    def revoke_key(self, user_id: int, key_id: int) -> None:
        key = self.keys.get(key_id)
        if key is None or key.user_id != user_id:
            raise NotFound("API key")
        with self.conn:
            self.keys.revoke(key_id, to_iso(self.clock.now()))
