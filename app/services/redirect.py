from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import Link, LinkClick


def redirect_link(
    db: Session,
    slug: str,
    password: str | None = None,
    ip_address: str | None = None,
    country: str | None = None,
    device: str | None = None,
    browser: str | None = None,
    os: str | None = None,
    user_agent: str | None = None,
    referer: str | None = None,
) -> str:

    link = (
        db.query(Link)
        .filter(Link.slug == slug)
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="لینک پیدا نشد.",
        )

    now = datetime.now(timezone.utc)

    if (
        link.expires_at is not None
        and link.expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="این لینک منقضی شده است.",
        )

    if link.password_hash:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="این لینک دارای رمز عبور است.",
            )

        if not verify_password(
            password,
            link.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز عبور اشتباه است.",
            )

    click = LinkClick(
        link_id=link.id,
        ip_address=ip_address,
        country=country,
        device=device,
        browser=browser,
        os=os,
        user_agent=user_agent,
        referer=referer,
    )

    db.add(click)
    db.commit()

    return link.original_url