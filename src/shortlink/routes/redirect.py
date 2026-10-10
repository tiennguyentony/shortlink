from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from shortlink.routes.deps import ServicesDep, SettingsDep
from shortlink.services.clicks import Visit

router = APIRouter(tags=["redirect"])


def visit_from(request: Request, trust_proxy_headers: bool) -> Visit:
    ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    if trust_proxy_headers and forwarded:
        ip = forwarded.split(",")[0].strip()
    return Visit(
        ip=ip,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )


# Registered last in create_app, so /api/... and /health win over this route.
@router.api_route("/{code}", methods=["GET", "HEAD"])
def follow(code: str, request: Request, services: ServicesDep, settings: SettingsDep):
    target = services.redirects.resolve(code)
    services.clicks.record(target.link_id, visit_from(request, settings.trust_proxy_headers))
    # 302, not 301: browsers cache 301s forever (ADR-002).
    return RedirectResponse(target.target_url, status_code=302, headers={"Cache-Control": "private, no-cache"})
