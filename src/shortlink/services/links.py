import sqlite3
from datetime import datetime, timezone

from shortlink.cache import RedirectCache
from shortlink.clock import Clock, to_iso
from shortlink.codes import CodeGenerator
from shortlink.domain.aliases import validate_alias
from shortlink.domain.errors import AliasTaken, InvalidExpiry, NotFound
from shortlink.domain.links import Link
from shortlink.domain.pagination import PageRequest
from shortlink.domain.urls import validate_target_url
from shortlink.repositories.links import LinkRepo


class LinkService:
    def __init__(
        self,
        conn: sqlite3.Connection,
        links: LinkRepo,
        codes: CodeGenerator,
        cache: RedirectCache,
        clock: Clock,
    ):
        self.conn = conn
        self.links = links
        self.codes = codes
        self.cache = cache
        self.clock = clock

    def create_link(
        self,
        user_id: int,
        url: str,
        alias: str | None = None,
        title: str | None = None,
        expires_at: datetime | None = None,
    ) -> Link:
        target = validate_target_url(url)
        now = self.clock.now()
        expiry = self._expiry(expires_at, now)
        code = validate_alias(alias) if alias else self.codes.new_code()
        try:
            with self.conn:
                link_id = self.links.create(user_id, code, target, title, bool(alias), expiry, to_iso(now))
        except sqlite3.IntegrityError:
            if alias:
                raise AliasTaken(alias) from None
            raise
        return self.links.get(link_id)

    def get_owned(self, user_id: int, code: str) -> Link:
        link = self.links.by_code(code)
        # Someone else's link looks exactly like a missing one.
        if link is None or link.user_id != user_id or link.deleted_at:
            raise NotFound("Link")
        return link

    def list_links(self, user_id: int, page: PageRequest) -> tuple[list[Link], int]:
        return self.links.list_for_user(user_id, page)

    def update_link(self, user_id: int, code: str, changes: dict[str, object]) -> Link:
        link = self.get_owned(user_id, code)
        updates = dict(changes)
        if "target_url" in updates:
            updates["target_url"] = validate_target_url(str(updates["target_url"]))
        if "expires_at" in updates:
            updates["expires_at"] = self._expiry(updates["expires_at"], self.clock.now())
        if "disabled" in updates:
            updates["disabled"] = int(bool(updates["disabled"]))
        with self.conn:
            self.links.update(link.id, updates)
        self.cache.evict(code)
        return self.links.get(link.id)

    def delete_link(self, user_id: int, code: str) -> None:
        link = self.get_owned(user_id, code)
        with self.conn:
            self.links.soft_delete(link.id, to_iso(self.clock.now()))

    @staticmethod
    def _expiry(value: object, now: datetime) -> str | None:
        if value is None:
            return None
        if not isinstance(value, datetime):
            raise InvalidExpiry("expires_at must be a date and time")
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)  # the API documents naive times as UTC
        if value <= now:
            raise InvalidExpiry("expires_at must be in the future")
        return to_iso(value)
