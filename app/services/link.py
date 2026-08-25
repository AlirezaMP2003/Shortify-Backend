import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Link, User
from app.schemas.link import CreateLinkRequest


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