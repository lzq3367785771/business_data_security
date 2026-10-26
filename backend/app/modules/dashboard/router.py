from fastapi import (
    APIRouter,
    Depends,
    Request,
)

from sqlalchemy.orm import Session

from app.core.authorization import (
    require_policy,
)

from app.core.dependencies import (
    get_current_user,
)

from app.core.responses import (
    success,
)

from app.db.models import User

from app.db.session import get_db

from app.modules.dashboard.service import (
    get_dashboard_summary,
)


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def get_summary(
    request: Request,

    db: Session = Depends(
        get_db
    ),

    user: User = Depends(
        get_current_user
    ),
):

    require_policy(
        db=db,
        request=request,
        user=user,
        resource="dashboard:summary",
        action="READ",
    )


    data = get_dashboard_summary(
        db
    )


    return success(
        request,
        data,
        message="安全态势概览查询成功",
    )