from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.click import (
    get_country_from_ip,
    parse_user_agent,
)
from app.services.redirect import redirect_link

router = APIRouter()


@router.get("/{slug}")
def redirect_link_endpoint(
    slug: str,
    request: Request,
    password: str | None = None,
    db: Session = Depends(get_db),
):
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    user_agent_data = parse_user_agent(user_agent)

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    country = get_country_from_ip(ip_address)

    original_url = redirect_link(
        db=db,
        slug=slug,
        password=password,
        ip_address=ip_address,
        country=country,
        device=user_agent_data["device"],
        browser=user_agent_data["browser"],
        os=user_agent_data["os"],
        user_agent=user_agent,
        referer=referer,
    )

    return RedirectResponse(
        url=original_url,
        status_code=307,
    )