from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import ipaddress

from app.db.database import get_db
from app.models import Link, Click

# No prefix: these are public short URLs served from the root, e.g. /pbRjaM
router = APIRouter(tags=["redirect"])


def _safe_ip(host: str | None) -> str | None:
    """Return host only if it's a valid IP address, else None.
    Guards the INET column against non-IP values (proxies, test clients)."""
    if not host:
        return None
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        return None


@router.get("/{short_code}")
def redirect_to_original(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # 1. Look up the link by its short_code (the value from the URL path).
    link = db.query(Link).filter(Link.short_code == short_code).first()

    # 2. Not found (or disabled) -> 404.
    if link is None or not link.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    # 3. Record the click BEFORE redirecting so analytics never miss a hit.
    click = Click(
        link_id=link.id,
        ip_address=_safe_ip(request.client.host if request.client else None),
        referrer=request.headers.get("referer"),
        # country and device_type stay NULL for now.
    )
    db.add(click)
    db.commit()

    # 4. Send the visitor on to the real destination.
    return RedirectResponse(
        url=link.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
