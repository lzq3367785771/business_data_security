from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    HTTPException,
)

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.authorization import (
    require_policy,
)

from app.core.dependencies import (
    get_current_user,
)

from app.core.responses import (
    success,
)

from app.db.models import (
    AnomalyEvent,
    User,
)

from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.access_monitoring.service import (
    detect_frequent_raw_sensitive_access,
    persist_anomalies,
)
from app.modules.access_monitoring.schemas import (
    AnomalyStatusUpdate,
)
from app.modules.access_monitoring.state_machine import (
    validate_transition,
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






@router.post("/detect")
def detect_and_save_anomalies(
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
        resource=(
            "access_monitoring:detect"
        ),
        action="DETECT_ANOMALIES",
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


    saved_events = persist_anomalies(
        db=db,
        anomalies=anomalies,
    )


    write_audit(
        db=db,
        request=request,
        user=user,
        action="DETECT_ANOMALIES",
        resource=(
            "access_monitoring:detect"
        ),
        result="ALLOW",
        policy_id=(
            decision.policy_id
        ),
        object_count=len(
            saved_events
        ),
        details={
            "window_minutes":
                window_minutes,

            "threshold":
                threshold,

            "detected_count":
                len(anomalies),

            "persisted_count":
                len(saved_events),
        },
    )


    return success(
        request,
        {
            "detected_count":
                len(anomalies),

            "persisted_count":
                len(saved_events),

            "anomaly_ids": [
                event.anomaly_id
                for event
                in saved_events
            ],
        },
        message=(
            "异常检测及事件保存完成"
        ),
    )


@router.get("/events")
def list_anomaly_events(
    request: Request,

    status: str | None = Query(
        default=None
    ),

    risk_level: str | None = Query(
        default=None
    ),

    min_risk_score: int | None = Query(
        default=None,
        ge=0,
        le=100,
    ),


    limit: int = Query(
        default=100,
        ge=1,
        le=200,
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
        resource="access_monitoring:events",
        action="LIST_ANOMALY_EVENTS",
    )


    statement = (
        select(
            AnomalyEvent,
            User.username,
        )
        .join(
            User,
            User.id == AnomalyEvent.user_id,
        )
    )


    # =========================
    # 状态筛选
    # =========================

    if status:

        allowed_statuses = {
            "open",
            "confirmed",
            "ignored",
            "resolved",
        }

        if status not in allowed_statuses:
            return success(
                request,
                {
                    "items": [],
                    "total": 0,
                },
                message="无效的异常事件状态",
            )

        statement = (
            statement.where(
                AnomalyEvent.status
                == status
            )
        )


    # =========================
    # 风险等级筛选
    # =========================

    if risk_level:

        normalized_risk_level = (
            risk_level.upper()
        )

        allowed_risk_levels = {
            "LOW",
            "MEDIUM",
            "HIGH",
        }

        if (
            normalized_risk_level
            not in allowed_risk_levels
        ):
            return success(
                request,
                {
                    "items": [],
                    "total": 0,
                },
                message="无效的风险等级",
            )

        statement = (
            statement.where(
                AnomalyEvent.risk_level
                == normalized_risk_level
            )
        )

    # =========================
    # 最低风险分数筛选
    # =========================

    if min_risk_score is not None:

        statement = (
            statement.where(
                AnomalyEvent.risk_score
                >= min_risk_score
            )
        )



    statement = (
        statement
        .order_by(
            AnomalyEvent.risk_score.desc(),
            AnomalyEvent.last_access_at.desc(),
            AnomalyEvent.created_at.desc(),
        )
        .limit(limit)
    )


    rows = (
        db.execute(
            statement
        )
        .all()
    )


    items = []


    for event, username in rows:

        data_object = "-"

        if (
            event.database_name
            and event.table_name
        ):
            data_object = (
                f"{event.database_name}."
                f"{event.table_name}"
            )


        items.append(
            {
                "anomaly_id":
                    event.anomaly_id,

                "anomaly_type":
                    event.anomaly_type,

                "anomaly_label":
                    (
                        "高频原始敏感数据访问"
                        if event.anomaly_type
                        == (
                            "FREQUENT_RAW_"
                            "SENSITIVE_ACCESS"
                        )
                        else event.anomaly_type
                    ),

                "risk_level":
                    event.risk_level,

                "risk_score":
                    event.risk_score,

                "risk_reasons":
                    event.risk_reasons,


                "status":
                    event.status,

                "user_id":
                    event.user_id,

                "username":
                    username,

                "system_code":
                    event.system_code,

                "source_id":
                    event.source_id,

                "source_code":
                    event.source_code,

                "database_name":
                    event.database_name,

                "table_name":
                    event.table_name,

                "data_object":
                    data_object,

                "access_count":
                    event.access_count,

                "window_minutes":
                    event.window_minutes,

                "sensitive_fields":
                    event.sensitive_fields
                    or [],

                "sensitivity_levels":
                    event.sensitivity_levels
                    or [],

                "evidence_event_ids":
                    event.evidence_event_ids
                    or [],

                "first_access_at":
                    (
                        event.first_access_at.isoformat()
                        if event.first_access_at
                        else None
                    ),

                "last_access_at":
                    (
                        event.last_access_at.isoformat()
                        if event.last_access_at
                        else None
                    ),

                "created_at":
                    event.created_at.isoformat(),

                "updated_at":
                    event.updated_at.isoformat(),
            }
        )


    write_audit(
        db=db,
        request=request,
        user=user,
        action="LIST_ANOMALY_EVENTS",
        resource="access_monitoring:events",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(items),
        details={
            "status_filter":
                status,

            "risk_level_filter":
                risk_level,

            "min_risk_score_filter":
                min_risk_score,


            "limit":
                limit,
        },
    )


    return success(
        request,
        {
            "items":
                items,

            "total":
                len(items),
        },
        message="异常事件列表查询成功",
    )




@router.patch(
    "/events/{anomaly_id}/status"
)
def update_anomaly_event_status(
    anomaly_id: str,
    payload: AnomalyStatusUpdate,
    request: Request,

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
        resource=(
            "access_monitoring:"
            "events:status"
        ),
        action=(
            "UPDATE_ANOMALY_STATUS"
        ),
    )


    event = db.get(
        AnomalyEvent,
        anomaly_id,
    )


    if event is None:
        raise HTTPException(
            status_code=404,
            detail="异常事件不存在",
        )


    old_status = event.status


    # =========================
    # 状态机校验
    # =========================

    try:

        validate_transition(
            current_status=old_status,
            target_status=payload.status,
        )

    except ValueError as exc:

        write_audit(
            db=db,
            request=request,
            user=user,
            action=(
                "UPDATE_ANOMALY_STATUS"
            ),
            resource=(
                "access_monitoring:"
                "events:status"
            ),
            result="DENY",
            policy_id=(
                decision.policy_id
            ),
            object_count=0,
            details={
                "anomaly_id":
                    event.anomaly_id,

                "anomaly_type":
                    event.anomaly_type,

                "old_status":
                    old_status,

                "requested_status":
                    payload.status,

                "reason":
                    "INVALID_STATUS_TRANSITION",
            },
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


    event.status = (
        payload.status
    )

    db.commit()

    db.refresh(
        event
    )


    write_audit(
        db=db,
        request=request,
        user=user,
        action=(
            "UPDATE_ANOMALY_STATUS"
        ),
        resource=(
            "access_monitoring:"
            "events:status"
        ),
        result="ALLOW",
        policy_id=(
            decision.policy_id
        ),
        object_count=1,
        details={
            "anomaly_id":
                event.anomaly_id,

            "anomaly_type":
                event.anomaly_type,

            "old_status":
                old_status,

            "new_status":
                event.status,
        },
    )


    return success(
        request,
        {
            "anomaly_id":
                event.anomaly_id,

            "old_status":
                old_status,

            "new_status":
                event.status,

            "updated_at":
                event.updated_at.isoformat(),
        },
        message="异常事件状态更新成功",
    )