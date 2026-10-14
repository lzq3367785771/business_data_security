from fastapi import (
    APIRouter,
    Depends,
    Query,
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

from app.modules.audit.service import (
    write_audit,
)

from app.modules.access_monitoring.service import (
    detect_frequent_raw_sensitive_access,
)


router = APIRouter(
    prefix="/api/v1/access-monitoring",
    tags=["Access Monitoring"],
)


@router.get("/anomalies")
def list_access_anomalies(
    request: Request,

    window_minutes: int = Query(
        default=5,
        ge=1,
        le=60,
    ),

    threshold: int = Query(
        default=3,
        ge=2,
        le=50,
    ),

    db: Session = Depends(
        get_db
    ),

    user: User = Depends(
        get_current_user
    ),
):

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="access_monitoring:list",
        action="LIST_ANOMALIES",
    )


    anomalies = (
        detect_frequent_raw_sensitive_access(
            db=db,
            window_minutes=(
                window_minutes
            ),
            threshold=threshold,
        )
    )


    write_audit(
        db=db,
        request=request,
        user=user,
        action="LIST_ANOMALIES",
        resource="access_monitoring:list",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(anomalies),
        details={
            "window_minutes":
                window_minutes,

            "threshold":
                threshold,

            "rule":
                (
                    "FREQUENT_RAW_"
                    "SENSITIVE_ACCESS"
                ),
        },
    )


    return success(
        request,
        {
            "rule": {
                "code":
                    (
                        "FREQUENT_RAW_"
                        "SENSITIVE_ACCESS"
                    ),

                "name":
                    "高频原始敏感数据访问",

                "window_minutes":
                    window_minutes,

                "threshold":
                    threshold,
            },

            "items":
                anomalies,

            "total":
                len(anomalies),
        },
        message="异常访问检测完成",
    )