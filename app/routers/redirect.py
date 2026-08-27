from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.redirect import redirect_link


router = APIRouter()


@router.get("/{slug}")
def redirect_to_original_url(
    slug: str,
    request: Request,
    password: str | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
):
    client_ip = None

    if request.client:
        client_ip = request.client.host

    original_url = redirect_link(
        db=db,
        slug=slug,
        password=password,
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
    )

    return RedirectResponse(
        url=original_url,
        status_code=307,
    )