from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, HttpUrl, ConfigDict


# ---- Input: what the client must send to create a link ----
class LinkCreate(BaseModel):
    # HttpUrl makes Pydantic reject anything that isn't a valid URL.
    original_url: HttpUrl
    user_id: UUID


# ---- Output: what we send back after creating/reading a link ----
class LinkResponse(BaseModel):
    id: UUID
    user_id: UUID
    original_url: str
    short_code: str
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


# ---- Output: the full analytics summary for one link ----
class AnalyticsSummary(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    total_clicks: int
    clicks_today: int
    top_referrers: list[ReferrerCount]
    clicks_by_date: list[DateCount]

    model_config = ConfigDict(from_attributes=True)
