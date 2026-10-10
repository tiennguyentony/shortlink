from datetime import datetime

from fastapi import APIRouter, Query, Response

from shortlink.domain.links import Link
from shortlink.routes.deps import ClockDep, CurrentUser, PageDep, ServicesDep, SettingsDep
from shortlink.routes.schemas import (
    Bucket,
    DashboardOut,
    DayCount,
    LinkIn,
    LinkOut,
    LinkPatch,
    LinkStatsOut,
    Page,
    TopLink,
)

router = APIRouter(prefix="/api", tags=["links"])


def short_url(base_url: str, code: str) -> str:
    return f"{base_url.rstrip('/')}/{code}"


def link_out(link: Link, base_url: str, now: datetime) -> LinkOut:
    return LinkOut(
        code=link.code,
        short_url=short_url(base_url, link.code),
        url=link.target_url,
        title=link.title,
        is_custom=link.is_custom,
        status=link.status(now),
        expires_at=link.expires_at,
        click_count=link.click_count,
        created_at=link.created_at,
    )


@router.post("/links", response_model=LinkOut, status_code=201)
def create_link(body: LinkIn, user: CurrentUser, services: ServicesDep, settings: SettingsDep, clock: ClockDep):
    link = services.links.create_link(user.id, body.url, body.alias, body.title, body.expires_at)
    return link_out(link, settings.base_url, clock.now())


@router.get("/links", response_model=Page[LinkOut])
def list_links(user: CurrentUser, services: ServicesDep, settings: SettingsDep, clock: ClockDep, page: PageDep):
    links, total = services.links.list_links(user.id, page)
    now = clock.now()
    return Page[LinkOut](
        items=[link_out(link, settings.base_url, now) for link in links],
        page=page.page,
        size=page.size,
        total=total,
        pages=page.pages_for(total),
    )


@router.get("/links/{code}", response_model=LinkOut)
def get_link(code: str, user: CurrentUser, services: ServicesDep, settings: SettingsDep, clock: ClockDep):
    return link_out(services.links.get_owned(user.id, code), settings.base_url, clock.now())


@router.patch("/links/{code}", response_model=LinkOut)
def update_link(
    code: str, body: LinkPatch, user: CurrentUser, services: ServicesDep, settings: SettingsDep, clock: ClockDep
):
    changes = body.model_dump(exclude_unset=True)
    if "url" in changes:
        changes["target_url"] = changes.pop("url")
    link = services.links.update_link(user.id, code, changes)
    return link_out(link, settings.base_url, clock.now())


@router.delete("/links/{code}", status_code=204)
def delete_link(code: str, user: CurrentUser, services: ServicesDep):
    services.links.delete_link(user.id, code)
    return Response(status_code=204)


@router.get("/links/{code}/stats", response_model=LinkStatsOut)
def link_stats(
    code: str, user: CurrentUser, services: ServicesDep, days: int = Query(default=7, ge=1, le=90)
):
    link = services.links.get_owned(user.id, code)
    stats = services.analytics.link_stats(link, days)
    return LinkStatsOut(
        code=link.code,
        total_clicks=stats.total_clicks,
        period_days=days,
        period_clicks=stats.period_clicks,
        by_day=[DayCount(day=day, clicks=count) for day, count in stats.by_day],
        referrers=[Bucket(name=host, clicks=count) for host, count in stats.referrers],
        countries=[Bucket(name=country, clicks=count) for country, count in stats.countries],
    )


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: CurrentUser, services: ServicesDep, settings: SettingsDep):
    data = services.analytics.dashboard(user.id)
    return DashboardOut(
        link_count=data.link_count,
        active_count=data.active_count,
        total_clicks=data.total_clicks,
        clicks_last_7_days=data.clicks_last_7_days,
        top_links=[
            TopLink(code=link.code, short_url=short_url(settings.base_url, link.code), clicks_last_7_days=count)
            for link, count in data.top_links
        ],
    )
