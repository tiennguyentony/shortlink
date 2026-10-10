from dataclasses import dataclass
from datetime import datetime

from shortlink.clock import from_iso


@dataclass(frozen=True)
class Link:
    id: int
    user_id: int
    code: str
    target_url: str
    title: str | None
    is_custom: bool
    disabled: bool
    expires_at: str | None
    click_count: int
    created_at: str
    deleted_at: str | None

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at is not None and from_iso(self.expires_at) <= now

    def status(self, now: datetime) -> str:
        if self.deleted_at:
            return "deleted"
        if self.disabled:
            return "disabled"
        if self.is_expired(now):
            return "expired"
        return "active"
