from sqlalchemy import func, select
from sqlalchemy.orm import Session

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.db.models import (
    AnomalyEvent,
    BusinessSystem,
    ColumnAsset,
    DataSource,
    DatabaseAsset,
    SensitiveFieldProfile,
    TableAsset,
    User,
    AuditEvent,
)


def _count(
    db: Session,
    statement,
) -> int:

    return int(
        db.scalar(statement)
        or 0
    )


def _to_local_datetime(
    value: datetime | None,
) -> datetime | None:
    """
    数据库存储时间当前按 UTC 使用，
    转换为服务器本地时区后再做日期统计。
    """

    if value is None:
        return None


    if value.tzinfo is None:

        value = value.replace(
            tzinfo=timezone.utc
        )


    return value.astimezone()



def get_dashboard_summary(
    db: Session,
) -> dict:

    system_count = _count(
        db,
        select(
            func.count(
                BusinessSystem.id
            )
        ).where(
            BusinessSystem.status
            == "active"
        ),
    )


    source_count = _count(
        db,
        select(
            func.count(
                DataSource.id
            )
        ).where(
            DataSource.status
            == "active"
        ),
    )


    database_count = _count(
        db,
        select(
            func.count(
                DatabaseAsset.id
            )
        ).where(
            DatabaseAsset.status
            == "active"
        ),
    )


    table_count = _count(
        db,
        select(
            func.count(
                TableAsset.id
            )
        ).where(
            TableAsset.status
            == "active"
        ),
    )


    column_count = _count(
        db,
        select(
            func.count(
                ColumnAsset.id
            )
        ).where(
            ColumnAsset.status
            == "active"
        ),
    )


    sensitive_field_count = _count(
        db,
        select(
            func.count(
                SensitiveFieldProfile.id
            )
        ).where(
            SensitiveFieldProfile.is_sensitive
            == True,
            SensitiveFieldProfile.review_status
            == "confirmed",
        ),
    )


    l4_sensitive_count = _count(
        db,
        select(
            func.count(
                SensitiveFieldProfile.id
            )
        ).where(
            SensitiveFieldProfile.is_sensitive
            == True,
            SensitiveFieldProfile.review_status
            == "confirmed",
            SensitiveFieldProfile.sensitivity_level
            == "L4",
        ),
    )


    anomaly_total = _count(
        db,
        select(
            func.count(
                AnomalyEvent.anomaly_id
            )
        ),
    )


    high_risk_total = _count(
        db,
        select(
            func.count(
                AnomalyEvent.anomaly_id
            )
        ).where(
            AnomalyEvent.risk_level
            == "HIGH"
        ),
    )


    open_count = _count(
        db,
        select(
            func.count(
                AnomalyEvent.anomaly_id
            )
        ).where(
            AnomalyEvent.status
            == "open"
        ),
    )


    confirmed_count = _count(
        db,
        select(
            func.count(
                AnomalyEvent.anomaly_id
            )
        ).where(
            AnomalyEvent.status
            == "confirmed"
        ),
    )


    resolved_count = _count(
        db,
        select(
            func.count(
                AnomalyEvent.anomaly_id
            )
        ).where(
            AnomalyEvent.status
            == "resolved"
        ),
    )


    active_high_risk_count = _count(
        db,
        select(
            func.count(
                AnomalyEvent.anomaly_id
            )
        ).where(
            AnomalyEvent.risk_level
            == "HIGH",
            AnomalyEvent.status.in_(
                [
                    "open",
                    "confirmed",
                ]
            ),
        ),
    )


    # =========================
    # 总体安全状态
    # =========================

    if active_high_risk_count > 0:

        security_status = {
            "level": "HIGH",
            "label": "高风险",
            "message":
                "当前存在活跃高风险异常事件，"
                "部分业务数据访问可能已触发风险控制。",
        }

    elif (
        open_count > 0
        or confirmed_count > 0
    ):

        security_status = {
            "level": "ATTENTION",
            "label": "需关注",
            "message":
                "当前存在尚未完成处置的异常事件，"
                "建议及时检查并处理。",
        }

    else:

        security_status = {
            "level": "SAFE",
            "label": "安全",
            "message":
                "当前暂无未处置高风险异常事件，"
                "平台整体运行状态正常。",
        }


    # =========================
    # 最近异常事件
    # =========================

    recent_rows = db.execute(
        select(
            AnomalyEvent,
            User.username,
        )
        .join(
            User,
            User.id
            == AnomalyEvent.user_id,
        )
        .order_by(
            AnomalyEvent.last_access_at.desc(),
            AnomalyEvent.created_at.desc(),
        )
        .limit(5)
    ).all()


    anomaly_labels = {
        "FREQUENT_RAW_SENSITIVE_ACCESS":
            "高频原始敏感数据访问",
    }

    recent_anomalies = []

    for anomaly, username in recent_rows:

        recent_anomalies.append(
            {
                "anomaly_id":
                    anomaly.anomaly_id,

                "anomaly_type":
                    anomaly.anomaly_type,

                "anomaly_label":
                    anomaly_labels.get(
                        anomaly.anomaly_type,
                        anomaly.anomaly_type,
                    ),

                "risk_level":
                    anomaly.risk_level,

                "status":
                    anomaly.status,

                "username":
                    username,

                "system_code":
                    anomaly.system_code,

                "source_code":
                    anomaly.source_code,

                "data_object":
                    (
                        f"{anomaly.database_name}."
                        f"{anomaly.table_name}"
                    ),

                "access_count":
                    anomaly.access_count,

                "last_access_at":
                    (
                        anomaly.last_access_at.isoformat()
                        if anomaly.last_access_at
                        else None
                    ),
            }
        )


    # =========================
    # 最近业务数据访问
    # =========================

    recent_access_rows = db.execute(
        select(
            AuditEvent,
            User.username,
        )
        .join(
            User,
            User.id
            == AuditEvent.user_id,
        )
        .where(
            AuditEvent.action
            == "READ_BUSINESS_DATA"
        )
        .order_by(
            AuditEvent.created_at.desc()
        )
        .limit(5)
    ).all()


    recent_accesses = []


    for event, username in recent_access_rows:

        details = (
            event.details
            or {}
        )


        database_name = (
            details.get(
                "database_name"
            )
        )

        table_name = (
            details.get(
                "table_name"
            )
        )


        if (
            database_name
            and table_name
        ):

            data_object = (
                f"{database_name}."
                f"{table_name}"
            )

        else:

            data_object = "-"


        recent_accesses.append(
            {
                "event_id":
                    event.event_id,

                "created_at":
                    (
                        event.created_at.isoformat()
                        if event.created_at
                        else None
                    ),

                "username":
                    username,

                "system_code":
                    details.get(
                        "system_code"
                    ),

                "source_code":
                    details.get(
                        "source_code"
                    ),

                "data_object":
                    data_object,

                "access_mode":
                    details.get(
                        "access_mode"
                    ),

                "risk_control_applied":
                    details.get(
                        "risk_control_applied",
                        False,
                    ),

                "masked_fields":
                    details.get(
                        "masked_fields",
                        [],
                    ),

                "returned_rows":
                    details.get(
                        "returned_rows",
                        event.object_count,
                    ),

                "result":
                    event.result,
            }
        )


    # =========================
    # 近 7 天安全趋势
    # =========================

    local_now = (
        datetime.now()
        .astimezone()
    )

    today = (
        local_now.date()
    )

    start_date = (
        today
        - timedelta(days=6)
    )


    # 为了覆盖本地近 7 天，
    # 查询时稍微放宽 UTC 时间范围
    query_start = (
        datetime.now(
            timezone.utc
        )
        - timedelta(days=8)
    )


    # -------------------------
    # 最近业务访问审计
    # -------------------------

    trend_access_events = (
        db.execute(
            select(
                AuditEvent
            )
            .where(
                AuditEvent.action
                == "READ_BUSINESS_DATA",

                AuditEvent.created_at
                >= query_start,
            )
        )
        .scalars()
        .all()
    )


    # -------------------------
    # 最近异常事件
    # -------------------------

    trend_anomaly_events = (
        db.execute(
            select(
                AnomalyEvent
            )
            .where(
                AnomalyEvent.created_at
                >= query_start,
            )
        )
        .scalars()
        .all()
    )


    # -------------------------
    # 初始化 7 天
    # -------------------------

    trend_map = {}


    for offset in range(7):

        current_date = (
            start_date
            + timedelta(
                days=offset
            )
        )

        key = (
            current_date.isoformat()
        )


        trend_map[key] = {
            "date":
                key,

            "business_accesses":
                0,

            "risk_control_accesses":
                0,

            "anomaly_events":
                0,
        }


    # -------------------------
    # 统计业务访问
    # -------------------------

    for event in trend_access_events:

        local_time = (
            _to_local_datetime(
                event.created_at
            )
        )


        if local_time is None:
            continue


        key = (
            local_time
            .date()
            .isoformat()
        )


        if key not in trend_map:
            continue


        trend_map[
            key
        ][
            "business_accesses"
        ] += 1


        details = (
            event.details
            or {}
        )


        if details.get(
            "risk_control_applied",
            False,
        ):

            trend_map[
                key
            ][
                "risk_control_accesses"
            ] += 1


    # -------------------------
    # 统计异常事件
    # -------------------------

    for anomaly in trend_anomaly_events:

        local_time = (
            _to_local_datetime(
                anomaly.created_at
            )
        )


        if local_time is None:
            continue


        key = (
            local_time
            .date()
            .isoformat()
        )


        if key not in trend_map:
            continue


        trend_map[
            key
        ][
            "anomaly_events"
        ] += 1


    trend_7d = list(
        trend_map.values()
    )



    return {
        "security_status":
            security_status,

        "assets": {
            "business_systems":
                system_count,

            "data_sources":
                source_count,

            "databases":
                database_count,

            "tables":
                table_count,

            "columns":
                column_count,
        },

        "sensitive_data": {
            "confirmed_sensitive_fields":
                sensitive_field_count,

            "l4_sensitive_fields":
                l4_sensitive_count,
        },

        "risks": {
            "anomaly_total":
                anomaly_total,

            "high_risk_total":
                high_risk_total,

            "active_high_risk":
                active_high_risk_count,

            "open":
                open_count,

            "confirmed":
                confirmed_count,

            "resolved":
                resolved_count,
        },

        "recent_anomalies":
            recent_anomalies,

        "recent_accesses":
            recent_accesses,

        "trend_7d":
            trend_7d,
    


    }