import ipaddress
import json
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Link, Click

# No prefix: these are public short URLs served from the root, e.g. /pbRjaM
router = APIRouter(tags=["redirect"])

# Simple in-memory cache so we don't look up the same IP repeatedly.
_geo_cache: dict[str, str | None] = {}


def _safe_ip(host: str | None) -> str | None:
    """Return host only if it's a valid IP address, else None."""
    if not host:
        return None
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        return None


def _client_ip(request: Request) -> str | None:
    """Real client IP. Behind the ALB the true IP is in X-Forwarded-For."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = _safe_ip(xff.split(",")[0].strip())
        if ip:
            return ip
    return _safe_ip(request.client.host if request.client else None)


def _device_type(user_agent: str | None) -> str | None:
    """Classify the device from the User-Agent string."""
    if not user_agent:
        return None
    ua = user_agent.lower()
    if "ipad" in ua or "tablet" in ua:
        return "tablet"
    if "mobi" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    return "desktop"


def _country(ip: str | None) -> str | None:
    """Best-effort 2-letter country code via a free GeoIP API.
    Returns None for private/loopback IPs or on any failure (the redirect
    must never break because of this)."""
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_reserved:
            return None
    except ValueError:
        return None
    if ip in _geo_cache:
        return _geo_cache[ip]
    country = None
    try:
        url = f"http://ip-api.com/json/{ip}?fields=countryCode"
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            country = data.get("countryCode") or None
    except Exception:
        country = None
    _geo_cache[ip] = country
    return country


@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # 1. Look up the link by its short_code OR its custom_slug.
    link = (
        db.query(Link)
        .filter((Link.short_code == short_code) | (Link.custom_slug == short_code))
        .first()
    )

    # 2. Not found (or disabled) -> 404.
    if link is None or not link.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    # 3. Record the click BEFORE redirecting, enriched with device + country.
    client_ip = _client_ip(request)
    click = Click(
        link_id=link.id,
        ip_address=client_ip,
        referrer=request.headers.get("referer"),
        device_type=_device_type(request.headers.get("user-agent")),
        country=_country(client_ip),
    )
    db.add(click)
    db.commit()

    # 4. Send the visitor on to the real destination.
    return RedirectResponse(
        url=link.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
