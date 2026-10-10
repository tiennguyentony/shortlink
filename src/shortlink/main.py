import logging
import sqlite3
from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shortlink.cache import RedirectCache
from shortlink.clock import Clock, SystemClock
from shortlink.codes import CodeGenerator, RandomCodes
from shortlink.config import Settings, load_settings
from shortlink.db import open_database
from shortlink.domain.errors import DomainError
from shortlink.geo import GeoLookup, OfflineGeo
from shortlink.routes import keys, links, redirect
from shortlink.seed import seed_if_empty
from shortlink.services import build_services


@dataclass
class AppDeps:
    conn: sqlite3.Connection
    settings: Settings = field(default_factory=Settings)
    clock: Clock = field(default_factory=SystemClock)
    codes: CodeGenerator | None = None
    geo: GeoLookup = field(default_factory=OfflineGeo)
    cache: RedirectCache | None = None


def default_deps() -> AppDeps:
    settings = load_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    conn = open_database(settings.db_path)
    clock = SystemClock()
    if settings.seed_demo_data:
        seed_if_empty(conn, clock)
    return AppDeps(conn=conn, settings=settings, clock=clock)


# Composition root: everything the app depends on comes in through AppDeps,
# so tests can pass an in-memory database, a fake clock and fixed codes.
def create_app(deps: AppDeps | None = None) -> FastAPI:
    deps = deps or default_deps()
    settings = deps.settings
    codes = deps.codes if deps.codes is not None else RandomCodes(settings.code_length, settings.code_alphabet)
    cache = deps.cache if deps.cache is not None else RedirectCache(settings.redirect_cache_size)

    app = FastAPI(title="Shortlink", version="0.6.0")
    app.state.settings = settings
    app.state.clock = deps.clock
    app.state.services = build_services(deps.conn, deps.clock, codes, deps.geo, cache, settings)

    @app.exception_handler(DomainError)
    def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/health", tags=["meta"])
    def health():
        return {"ok": True}

    app.include_router(links.router)
    app.include_router(keys.router)
    app.include_router(redirect.router)  # catch-all /{code}: keep it last
    return app
