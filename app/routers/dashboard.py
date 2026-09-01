from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models import User

from app.schemas.dashboard import (
    DashboardOverviewResponse,
)

from app.services.dashboard import (
    get_dashboard_overview,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
)
def get_dashboard_overview_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_overview(
        db=db,
        user=current_user,
    )