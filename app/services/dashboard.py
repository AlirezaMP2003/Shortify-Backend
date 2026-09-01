from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Link, LinkClick, User


def get_dashboard_overview(
    db: Session,
    user: User,
) -> dict:

    now = datetime.now(timezone.utc)

    total_links = (
        db.query(func.count(Link.id))
        .filter(
            Link.user_id == user.id,
        )
        .scalar()
        or 0
    )

    active_links = (
        db.query(func.count(Link.id))
        .filter(
            Link.user_id == user.id,
            (
                (Link.expires_at.is_(None))
                | (Link.expires_at > now)
            ),
        )
        .scalar()
        or 0
    )

    expired_links = (
        db.query(func.count(Link.id))
        .filter(
            Link.user_id == user.id,
            Link.expires_at.isnot(None),
            Link.expires_at <= now,
        )
        .scalar()
        or 0
    )

    total_clicks = (
        db.query(func.count(LinkClick.id))
        .join(
            Link,
            LinkClick.link_id == Link.id,
        )
        .filter(
            Link.user_id == user.id,
        )
        .scalar()
        or 0
    )

    start_date = (
        now - timedelta(days=6)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    chart_rows = (
        db.query(
            func.date(LinkClick.clicked_at).label("date"),
            func.count(LinkClick.id).label("clicks"),
        )
        .join(
            Link,
            LinkClick.link_id == Link.id,
        )
        .filter(
            Link.user_id == user.id,
            LinkClick.clicked_at >= start_date,
        )
        .group_by(
            func.date(LinkClick.clicked_at),
        )
        .order_by(
            func.date(LinkClick.clicked_at),
        )
        .all()
    )

    clicks_by_date = {
        row.date: row.clicks
        for row in chart_rows
    }

    clicks_last_7_days = []

    for day_offset in range(7):
        current_date = (
            start_date + timedelta(days=day_offset)
        ).date()

        clicks_last_7_days.append(
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "clicks": clicks_by_date.get(
                    current_date,
                    0,
                ),
            }
        )

    return {
        "total_links": total_links,
        "total_clicks": total_clicks,
        "active_links": active_links,
        "expired_links": expired_links,
        "clicks_last_7_days": clicks_last_7_days,
    }