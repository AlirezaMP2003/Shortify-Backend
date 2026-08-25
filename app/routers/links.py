from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.link import (
    CreateLinkRequest,
    LinkResponse,
    LinkListResponse,
    LinkSortOption,
)

from app.services.link import (
    build_link_response,
    create_link,
    get_user_links,
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


@router.get(
    "",
    response_model=LinkListResponse,
)
def get_links(
    page: int = 1,
    limit: int = 5,
    sort: LinkSortOption = LinkSortOption.NEWEST,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page باید حداقل 1 باشد.",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Limit باید بین 1 تا 100 باشد.",
        )

    items, total = get_user_links(
        db=db,
        user=current_user,
        page=page,
        limit=limit,
        sort=sort.value,
    )

    total_pages = (
        (total + limit - 1) // limit
        if total > 0
        else 0
    )

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
    }