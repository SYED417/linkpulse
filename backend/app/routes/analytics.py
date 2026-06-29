from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Link, Click
from app.schemas.link import (
    AnalyticsSummary,
    ReferrerCount,
    DateCount,
    DeviceCount,
    CountryCount,
)

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/{short_code}", response_model=AnalyticsSummary)
def get_analytics(short_code: str, db: Session = Depends(get_db)):
    # 1. Find the link, or 404.
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    # 2. total_clicks: count every click row for this link.
    total_clicks = (
        db.query(func.count(Click.id))
        .filter(Click.link_id == link.id)
        .scalar()
    )

    # 3. clicks_today: same count, but only rows whose date == today.
    today = date.today()
    clicks_today = (
        db.query(func.count(Click.id))
        .filter(Click.link_id == link.id)
        .filter(func.date(Click.clicked_at) == today)
        .scalar()
    )

    # 4. top_referrers: group rows by referrer, count each group,
    #    biggest first, keep the top 5.
    referrer_rows = (
        db.query(Click.referrer, func.count(Click.id).label("count"))
        .filter(Click.link_id == link.id)
        .group_by(Click.referrer)
        .order_by(func.count(Click.id).desc())
        .limit(5)
        .all()
    )
    top_referrers = [
        ReferrerCount(referrer=r.referrer, count=r.count) for r in referrer_rows
    ]

    # 5. clicks_by_date: clicks per day for the last 7 days.
    seven_days_ago = today - timedelta(days=6)  # today + previous 6 = 7 days
    date_rows = (
        db.query(
            func.date(Click.clicked_at).label("day"),
            func.count(Click.id).label("count"),
        )
        .filter(Click.link_id == link.id)
        .filter(func.date(Click.clicked_at) >= seven_days_ago)
        .group_by(func.date(Click.clicked_at))
        .order_by(func.date(Click.clicked_at))
        .all()
    )
    clicks_by_date = [DateCount(date=row.day, count=row.count) for row in date_rows]

    # 6. clicks_by_device: group by device type.
    device_rows = (
        db.query(Click.device_type, func.count(Click.id).label("count"))
        .filter(Click.link_id == link.id)
        .group_by(Click.device_type)
        .order_by(func.count(Click.id).desc())
        .all()
    )
    clicks_by_device = [
        DeviceCount(device_type=r.device_type, count=r.count) for r in device_rows
    ]

    # 7. clicks_by_country: group by country.
    country_rows = (
        db.query(Click.country, func.count(Click.id).label("count"))
        .filter(Click.link_id == link.id)
        .group_by(Click.country)
        .order_by(func.count(Click.id).desc())
        .all()
    )
    clicks_by_country = [
        CountryCount(country=r.country, count=r.count) for r in country_rows
    ]

    # 8. Assemble the response. FastAPI shapes it via AnalyticsSummary.
    return AnalyticsSummary(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        total_clicks=total_clicks,
        clicks_today=clicks_today,
        top_referrers=top_referrers,
        clicks_by_date=clicks_by_date,
        clicks_by_device=clicks_by_device,
        clicks_by_country=clicks_by_country,
    )
