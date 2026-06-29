from datetime import datetime, date
from uuid import UUID
import re

from pydantic import BaseModel, HttpUrl, ConfigDict, field_validator

# Reserved words that must not be used as slugs (they collide with real
# routes that take precedence, so the slug would be unreachable).
_RESERVED_SLUGS = {"health", "api", "docs", "redoc", "openapi.json", "assets"}

# A valid slug: lowercase letters, digits and hyphens; no leading/trailing
# hyphen; 3–50 characters.
_SLUG_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


# ---- Input: what the client must send to create a link ----
class LinkCreate(BaseModel):
    # HttpUrl makes Pydantic reject anything that isn't a valid URL.
    original_url: HttpUrl
    # Optional custom slug. Sanitized and validated below.
    custom_slug: str | None = None

    @field_validator("custom_slug")
    @classmethod
    def _validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # Sanitize: trim and lowercase.
        slug = v.strip().lower()
        if slug == "":
            return None  # treat empty/whitespace as "no slug"
        if not (3 <= len(slug) <= 50):
            raise ValueError("Slug must be between 3 and 50 characters.")
        if not _SLUG_PATTERN.match(slug):
            raise ValueError(
                "Slug may contain only lowercase letters, numbers and hyphens "
                "(no leading or trailing hyphen)."
            )
        if slug in _RESERVED_SLUGS:
            raise ValueError("This slug is reserved and cannot be used.")
        return slug


# ---- Output: what we send back after creating/reading a link ----
class LinkResponse(BaseModel):
    id: UUID
    user_id: UUID
    original_url: str
    short_code: str
    custom_slug: str | None
    created_at: datetime
    is_active: bool

    # Lets Pydantic read data straight from a SQLAlchemy model object
    # (link.id, link.short_code, ...) instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)


# ---- One referrer and how many clicks came from it ----
class ReferrerCount(BaseModel):
    referrer: str | None  # None means the visitor came with no Referer header
    count: int


# ---- Clicks on a single day ----
class DateCount(BaseModel):
    date: date
    count: int


# ---- Clicks from a device type ----
class DeviceCount(BaseModel):
    device_type: str | None
    count: int


# ---- Clicks from a country ----
class CountryCount(BaseModel):
    country: str | None
    count: int


# ---- Output: the full analytics summary for one link ----
class AnalyticsSummary(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    total_clicks: int
    clicks_today: int
    top_referrers: list[ReferrerCount]
    clicks_by_date: list[DateCount]
    clicks_by_device: list[DeviceCount]
    clicks_by_country: list[CountryCount]

    model_config = ConfigDict(from_attributes=True)
