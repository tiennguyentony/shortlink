"""QR codes for short links.

GET /api/links/{code}/qr returns a PNG (or SVG with ?format=svg) that encodes
the short URL, so printed material still goes through our redirect and gets
counted in analytics.
"""

import io
from functools import lru_cache

from fastapi import APIRouter, Query
from fastapi.responses import Response

from shortlink.routes.deps import CurrentUser, ServicesDep, SettingsDep

router = APIRouter(prefix="/api", tags=["qr codes"])

MIN_BOX_SIZE = 2
MAX_BOX_SIZE = 40
DEFAULT_BORDER = 4
ERROR_CORRECTION = {"L": 1, "M": 0, "Q": 3, "H": 2}  # qrcode.constants values


def _qrcode():
    # Imported lazily so the rest of the app starts without Pillow installed.
    import qrcode
    import qrcode.image.svg

    return qrcode


@lru_cache(maxsize=1024)
def render_png(data: str, box_size: int = 10, border: int = DEFAULT_BORDER, level: str = "M") -> bytes:
    qrcode = _qrcode()
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECTION[level],
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@lru_cache(maxsize=1024)
def render_svg(data: str, border: int = DEFAULT_BORDER, level: str = "M") -> bytes:
    qrcode = _qrcode()
    image = qrcode.make(
        data,
        image_factory=qrcode.image.svg.SvgPathImage,
        error_correction=ERROR_CORRECTION[level],
        border=border,
    )
    buffer = io.BytesIO()
    image.save(buffer)
    return buffer.getvalue()


@router.get("/links/{code}/qr")
def link_qr_code(
    code: str,
    user: CurrentUser,
    services: ServicesDep,
    settings: SettingsDep,
    format: str = Query(default="png", pattern="^(png|svg)$"),
    size: int = Query(default=10, ge=MIN_BOX_SIZE, le=MAX_BOX_SIZE),
    level: str = Query(default="M", pattern="^[LMQH]$"),
):
    link = services.links.get_owned(user.id, code)
    # Encode the short URL, not the target, so scans are counted.
    data = f"{settings.base_url.rstrip('/')}/{link.code}?src=qr"
    if format == "svg":
        return Response(render_svg(data, level=level), media_type="image/svg+xml")
    return Response(
        render_png(data, box_size=size, level=level),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )
