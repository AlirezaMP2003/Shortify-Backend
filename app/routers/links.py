from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.link import CreateLinkRequest, LinkResponse
from app.services.link import (
    build_link_response,
    create_link,
)
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/links",
    tags=["Links"],
)


@router.post(
    "",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_link_endpoint(
    data: CreateLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    link = create_link(
        db=db,
        user=current_user,
        data=data,
    )

    return build_link_response(link)