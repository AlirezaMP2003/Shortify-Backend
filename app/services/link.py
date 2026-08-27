import uuid
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.security import hash_password
from app.models import Link, User, LinkClick
from app.schemas.link import CreateLinkRequest, UpdateLinkRequest


SLUG_LENGTH = 6


def generate_slug() -> str:
    return secrets.token_urlsafe(8)[:SLUG_LENGTH]


def generate_unique_slug(db: Session) -> str:
    while True:
        slug = generate_slug()

        existing_link = (
            db.query(Link)
            .filter(Link.slug == slug)
            .first()
        )

        if existing_link is None:
            return slug


def calculate_expiration(
    expires_at: str | None,
) -> datetime | None:
    if not expires_at:
        return None

    now = datetime.now(timezone.utc)

    expiration_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
    }

    return now + expiration_map[expires_at]


def create_link(
    db: Session,
    user: User,
    data: CreateLinkRequest,
) -> Link:

    if data.custom_slug:
        existing_link = (
            db.query(Link)
            .filter(Link.slug == data.custom_slug)
            .first()
        )

        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="این Slug قبلاً استفاده شده است.",
            )

        slug = data.custom_slug

    else:
        slug = generate_unique_slug(db)

    expires_at = calculate_expiration(
        data.expires_at
    )

    password_hash = (
        hash_password(data.password)
        if data.password
        else None
    )

    link = Link(
        user_id=user.id,
        original_url=data.original_url,
        title=data.title,
        slug=slug,
        password_hash=password_hash,
        expires_at=expires_at,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return link

def build_link_response(
    link: Link,
    clicks: int = 0,
) -> dict:
    now = datetime.now(timezone.utc)

    if link.expires_at is not None and link.expires_at <= now:
        link_status = "expired"
    else:
        link_status = "active"

    return {
        "id": link.id,
        "short_url": f"shortify.ir/{link.slug}",
        "original_url": link.original_url,
        "title": link.title,
        "clicks": clicks,
        "status": link_status,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }


def get_user_links(
    db: Session,
    user: User,
    page: int,
    limit: int,
    sort: str,
) -> tuple[list[dict], int]:
    offset = (page - 1) * limit

    total = (
        db.query(func.count(Link.id))
        .filter(Link.user_id == user.id)
        .scalar()
        or 0
    )

    click_count = func.count(LinkClick.id)

    query = (
        db.query(
            Link,
            click_count.label("clicks"),
        )
        .outerjoin(
            LinkClick,
            LinkClick.link_id == Link.id,
        )
        .filter(Link.user_id == user.id)
        .group_by(Link.id)
    )

    if sort == "newest":
        query = query.order_by(Link.created_at.desc())

    elif sort == "oldest":
        query = query.order_by(Link.created_at.asc())

    elif sort == "most-clicked":
        query = query.order_by(click_count.desc())

    elif sort == "least-clicked":
        query = query.order_by(click_count.asc())

    results = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        build_link_response(
            link=link,
            clicks=clicks,
        )
        for link, clicks in results
    ]

    return items, total


def get_user_link(
    db: Session,
    user: User,
    link_id: uuid.UUID,
) -> dict:
    result = (
        db.query(
            Link,
            func.count(LinkClick.id).label("clicks"),
        )
        .outerjoin(
            LinkClick,
            LinkClick.link_id == Link.id,
        )
        .filter(
            Link.id == link_id,
            Link.user_id == user.id,
        )
        .group_by(Link.id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لینک پیدا نشد.",
        )

    link, clicks = result

    return build_link_response(
        link=link,
        clicks=clicks,
    )



def update_link(
    db: Session,
    user: User,
    link_id: uuid.UUID,
    data: UpdateLinkRequest,
) -> dict:
    link = (
        db.query(Link)
        .filter(
            Link.id == link_id,
            Link.user_id == user.id,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لینک پیدا نشد.",
        )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "original_url" in update_data:
        link.original_url = update_data["original_url"]

    if "title" in update_data:
        link.title = update_data["title"]

    if "custom_slug" in update_data:
        new_slug = update_data["custom_slug"]

        if new_slug:
            existing_link = (
                db.query(Link)
                .filter(
                    Link.slug == new_slug,
                    Link.id != link.id,
                )
                .first()
            )

            if existing_link:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="این Slug قبلاً استفاده شده است.",
                )

            link.slug = new_slug

        else:
            link.slug = generate_unique_slug(db)

    if "expires_at" in update_data:
        link.expires_at = calculate_expiration(
            update_data["expires_at"]
        )

    if "password" in update_data:
        password = update_data["password"]

        if password:
            link.password_hash = hash_password(password)
        else:
            link.password_hash = None

    link.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(link)

    return get_user_link(
        db=db,
        user=user,
        link_id=link.id,
    )



def delete_link(
    db: Session,
    user: User,
    link_id: uuid.UUID,
) -> None:
    link = (
        db.query(Link)
        .filter(
            Link.id == link_id,
            Link.user_id == user.id,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لینک پیدا نشد.",
        )

    db.delete(link)
    db.commit()


def _build_breakdown(
    db: Session,
    link_id: uuid.UUID,
    column,
) -> list[dict]:
    rows = (
        db.query(
            column.label("name"),
            func.count(LinkClick.id).label("clicks"),
        )
        .filter(
            LinkClick.link_id == link_id,
            column.isnot(None),
        )
        .group_by(column)
        .order_by(func.count(LinkClick.id).desc())
        .all()
    )

    return [
        {
            "name": row.name,
            "clicks": row.clicks,
        }
        for row in rows
    ]

def get_link_analytics(
    db: Session,
    user: User,
    link_id: uuid.UUID,
) -> dict:
    link = (
        db.query(Link)
        .filter(
            Link.id == link_id,
            Link.user_id == user.id,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لینک پیدا نشد.",
        )

    total_clicks = (
        db.query(func.count(LinkClick.id))
        .filter(LinkClick.link_id == link.id)
        .scalar()
        or 0
    )

    now = datetime.now(timezone.utc)

    start_of_today = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    today_clicks = (
        db.query(func.count(LinkClick.id))
        .filter(
            LinkClick.link_id == link.id,
            LinkClick.clicked_at >= start_of_today,
        )
        .scalar()
        or 0
    )

    first_click = (
        db.query(func.min(LinkClick.clicked_at))
        .filter(LinkClick.link_id == link.id)
        .scalar()
    )

    if first_click is None or total_clicks == 0:
        average_clicks = 0.0
    else:
        first_date = first_click.date()
        today_date = now.date()

        days = (today_date - first_date).days + 1

        average_clicks = round(
            total_clicks / days,
            1,
        )

    chart_rows = (
        db.query(
            func.date(LinkClick.clicked_at).label("date"),
            func.count(LinkClick.id).label("clicks"),
        )
        .filter(LinkClick.link_id == link.id)
        .group_by(func.date(LinkClick.clicked_at))
        .order_by(func.date(LinkClick.clicked_at))
        .all()
    )

    chart_data = [
        {
            "date": row.date.strftime("%Y-%m-%d"),
            "clicks": row.clicks,
        }
        for row in chart_rows
    ]

    countries = _build_breakdown(
        db=db,
        link_id=link.id,
        column=LinkClick.country,
    )

    devices = _build_breakdown(
        db=db,
        link_id=link.id,
        column=LinkClick.device,
    )

    browsers = _build_breakdown(
        db=db,
        link_id=link.id,
        column=LinkClick.browser,
    )

    operating_systems = _build_breakdown(
        db=db,
        link_id=link.id,
        column=LinkClick.os,
    )

    return {
        "short_url": f"shortify.ir/{link.slug}",
        "original_url": link.original_url,
        "total_clicks": total_clicks,
        "today_clicks": today_clicks,
        "average_clicks": average_clicks,
        "chart_data": chart_data,
        "countries": countries,
        "devices": devices,
        "browsers": browsers,
        "operating_systems": operating_systems,
    }