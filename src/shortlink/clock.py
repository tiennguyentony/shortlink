from datetime import datetime, timedelta, timezone
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock:
    """A clock tests can set and move forward."""

    def __init__(self, start: datetime):
        self._now = start

    def now(self) -> datetime:
        return self._now

    def set(self, value: datetime) -> None:
        self._now = value

    def advance(self, **kwargs: float) -> None:
        self._now += timedelta(**kwargs)


def to_iso(value: datetime) -> str:
    """Timestamps are stored as UTC ISO 8601 strings, e.g. 2031-03-03T09:00:00+00:00."""
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)
