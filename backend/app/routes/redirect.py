import ipaddress
import json
import re
import html
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Link, Click

# No prefix: these are public short URLs served from the root, e.g. /pbRjaM
router = APIRouter(tags=["redirect"])

# Simple in-memory cache so we don't look up the same IP repeatedly.
_geo_cache: dict[str, str | None] = {}

# Social/link-preview scrapers. When one of these fetches the short URL we
# return Open Graph HTML instead of redirecting, so they can build a card.
_BOT_RE = re.compile(
    r"(whatsapp|twitterbot|facebookexternalhit|facebot|discordbot|slackbot|"
    r"telegrambot|linkedinbot|pinterest|redditbot|googlebot|bingbot|embedly|"
    r"quora link preview|skypeuripreview|vkshare|ia_archiver|whatsApp|"
    r"applebot|tumblr|flipboard|nuzzel|bitlybot)",
    re.IGNORECASE,
)


def is_social_bot(user_agent: str | None) -> bool:
    """True if the User-Agent looks like a social-media / link-preview crawler."""
    if not user_agent:
        return False
    return bool(_BOT_RE.search(user_agent))


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
    """Best-effort 2-letter country code via a free GeoIP API."""
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


# Open Graph preview page returned to social scrapers. Uses placeholder
# tokens (not f-string/format) so the CSS braces need no escaping.
_PREVIEW_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>

  <!-- Open Graph -->
  <meta property="og:title" content="__TITLE__" />
  <meta property="og:description" content="__DESCRIPTION__" />
  <meta property="og:url" content="__URL__" />
  <meta property="og:image" content="__IMAGE__" />
  <meta property="og:type" content="website" />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="__TITLE__" />
  <meta name="twitter:description" content="__DESCRIPTION__" />
  <meta name="twitter:image" content="__IMAGE__" />

  <!-- Authorship -->
  <meta name="author" content="Syed Sulaiman Usman" />
  <meta name="copyright" content="April 18, 2026" />
  <meta http-equiv="last-modified" content="April 18, 2026" />

  <!-- Fallback: if a real browser lands here, send it on immediately. -->
  <script>window.location.replace(__JS_URL__);</script>

  <style>
    :root {
      --indigo: #6366f1;
      --indigo-deep: #4f46e5;
      --navy: #1e1b4b;
      --navy-deep: #0f172a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: linear-gradient(135deg, var(--navy-deep), var(--navy));
      color: #e2e8f0;
    }
    .card {
      max-width: 520px;
      width: calc(100% - 40px);
      background: rgba(30, 27, 75, 0.65);
      border: 1px solid var(--indigo-deep);
      border-radius: 16px;
      padding: 36px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
      text-align: center;
    }
    .badge {
      display: inline-block;
      padding: 6px 14px;
      border-radius: 999px;
      background: var(--indigo);
      color: #fff;
      font-weight: 700;
      font-size: 0.8rem;
      letter-spacing: 0.5px;
    }
    h1 { margin: 18px 0 8px; font-size: 1.5rem; color: #fff; word-break: break-word; }
    p  { margin: 0 0 20px; color: #c7d2fe; word-break: break-word; }
    a.go {
      display: inline-block;
      padding: 12px 24px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--indigo), var(--indigo-deep));
      color: #fff;
      text-decoration: none;
      font-weight: 700;
    }
    footer { margin-top: 22px; font-size: 0.75rem; color: #818cf8; }
  </style>
</head>
<body>
  <main class="card">
    <span class="badge">LinkPulse</span>
    <h1>__TITLE__</h1>
    <p>__DESCRIPTION__</p>
    <a class="go" href="__URL__">Continue &rarr;</a>
    <footer>&copy; April 18, 2026 &middot; Syed Sulaiman Usman</footer>
  </main>
</body>
</html>
"""


def _preview_html(link: Link) -> str:
    """Build the Open Graph preview page for a link (all values escaped)."""
    title = html.escape(f"LinkPulse · /{link.custom_slug or link.short_code}")
    description = html.escape(f"Redirecting to {link.original_url}")
    url = html.escape(link.original_url, quote=True)
    image = "https://placehold.co/1200x630/1e1b4b/818cf8/png?text=LinkPulse"
    js_url = json.dumps(link.original_url)  # safe JS string literal
    return (
        _PREVIEW_TEMPLATE
        .replace("__TITLE__", title)
        .replace("__DESCRIPTION__", description)
        .replace("__URL__", url)
        .replace("__IMAGE__", image)
        .replace("__JS_URL__", js_url)
    )


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

    user_agent = request.headers.get("user-agent")

    # 3. Social scraper? Return Open Graph HTML instead of redirecting, and do
    #    NOT count it as a click (keeps analytics free of bot noise).
    if is_social_bot(user_agent):
        return HTMLResponse(content=_preview_html(link), status_code=200)

    # 4. Real user: record the click (enriched with device + country)...
    client_ip = _client_ip(request)
    click = Click(
        link_id=link.id,
        ip_address=client_ip,
        referrer=request.headers.get("referer"),
        device_type=_device_type(user_agent),
        country=_country(client_ip),
    )
    db.add(click)
    db.commit()

    # 5. ...then 307-redirect to the destination.
    return RedirectResponse(
        url=link.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
