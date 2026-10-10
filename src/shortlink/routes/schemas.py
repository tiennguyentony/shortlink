from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class LinkIn(BaseModel):
    url: str = Field(max_length=4096)
    alias: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=200)
    expires_at: datetime | None = None


class LinkPatch(BaseModel):
    url: str | None = Field(default=None, max_length=4096)
    title: str | None = Field(default=None, max_length=200)
    disabled: bool | None = None
    expires_at: datetime | None = None


class LinkOut(BaseModel):
    code: str
    short_url: str
    url: str
    title: str | None
    is_custom: bool
    status: str
    expires_at: str | None
    click_count: int
    created_at: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    size: int
    total: int
    pages: int


class DayCount(BaseModel):
    day: date
    clicks: int


class Bucket(BaseModel):
    name: str
    clicks: int


class LinkStatsOut(BaseModel):
    code: str
    total_clicks: int
    period_days: int
    period_clicks: int
    by_day: list[DayCount]
    referrers: list[Bucket]
    countries: list[Bucket]


class TopLink(BaseModel):
    code: str
    short_url: str
    clicks_last_7_days: int


class DashboardOut(BaseModel):
    link_count: int
    active_count: int
    total_clicks: int
    clicks_last_7_days: int
    top_links: list[TopLink]


class ApiKeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ApiKeyOut(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: str
    revoked_at: str | None
    use_count: int
    last_used_at: str | None


class NewApiKeyOut(ApiKeyOut):
    key: str = Field(description="Shown once. Store it somewhere safe.")
