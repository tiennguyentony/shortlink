from typing import Annotated

from fastapi import Depends, Header, Query, Request

from shortlink.clock import Clock
from shortlink.config import Settings
from shortlink.domain.errors import Unauthorized
from shortlink.domain.pagination import MAX_PAGE_SIZE, PageRequest
from shortlink.repositories.users import User
from shortlink.services import Services


def get_services(request: Request) -> Services:
    return request.app.state.services


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_clock(request: Request) -> Clock:
    return request.app.state.clock


ServicesDep = Annotated[Services, Depends(get_services)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
ClockDep = Annotated[Clock, Depends(get_clock)]


def current_user(services: ServicesDep, x_api_key: Annotated[str | None, Header()] = None) -> User:
    if not x_api_key:
        raise Unauthorized("Send your API key in the X-API-Key header")
    return services.auth.authenticate(x_api_key.strip())


def page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
) -> PageRequest:
    return PageRequest(page=page, size=size)


CurrentUser = Annotated[User, Depends(current_user)]
PageDep = Annotated[PageRequest, Depends(page_params)]
