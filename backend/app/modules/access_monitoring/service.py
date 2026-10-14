from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AuditEvent,
    User,
)


def detect_frequent_raw_sensitive_access(
    db: Session,
    window_minutes: int = 5,
    threshold: int = 3,
) -> list[dict]:
    """
    检测高频原始敏感数据访问。

    规则：
        同一用户
        + 同一数据源
        + 同一业务表
        + 最近 window_minutes 分钟
        + 原始敏感数据访问次数 >= threshold

    当前 V1 只分析：
        READ_BUSINESS_DATA
        result = ALLOW
        access_mode = raw
        sensitive_fields 非空
    """

    window_end = datetime.utcnow()

    window_start = (
        window_end
        - timedelta(
            minutes=window_minutes
        )
    )


    statement = (
        select(
            AuditEvent,
            User.username,
        )
        .join(
            User,
            User.id == AuditEvent.user_id,
        )
        .where(
            AuditEvent.action
            == "READ_BUSINESS_DATA",

            AuditEvent.result
            == "ALLOW",

            AuditEvent.created_at
            >= window_start,
        )
        .order_by(
            AuditEvent.created_at.asc()
        )
    )


    rows = db.execute(
        statement
    ).all()


    groups = {}


    for event, username in rows:

        details = (
            event.details
            or {}
        )


        # 只分析原始访问
        if (
            details.get("access_mode")
            != "raw"
        ):
            continue


        sensitive_fields = (
            details.get(
                "sensitive_fields"
            )
            or []
        )


        # 没有敏感字段则不属于本规则
        if not sensitive_fields:
            continue


        source_id = (
            details.get("source_id")
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
            source_id is None
            or not database_name
            or not table_name
        ):
            continue


        key = (
            event.user_id,
            source_id,
            database_name,
            table_name,
        )


        if key not in groups:

            groups[key] = {
                "user_id":
                    event.user_id,

                "username":
                    username,

                "system_code":
                    details.get(
                        "system_code"
                    ),

                "source_id":
                    source_id,

                "source_code":
                    details.get(
                        "source_code"
                    ),

                "database_name":
                    database_name,

                "table_name":
                    table_name,

                "events":
                    [],

                "sensitive_fields":
                    set(),

                "sensitivity_levels":
                    set(),
            }


        group = groups[key]


        group["events"].append(
            event
        )


        group[
            "sensitive_fields"
        ].update(
            sensitive_fields
        )


        field_levels = (
            details.get(
                "sensitive_field_levels"
            )
            or {}
        )


        group[
            "sensitivity_levels"
        ].update(
            field_levels.values()
        )


    anomalies = []


    for group in groups.values():

        events = group["events"]

        access_count = len(events)


        if access_count < threshold:
            continue


        anomalies.append(
            {
                "anomaly_type":
                    (
                        "FREQUENT_RAW_"
                        "SENSITIVE_ACCESS"
                    ),

                "anomaly_label":
                    "高频原始敏感数据访问",

                "risk_level":
                    "HIGH",

                "user_id":
                    group["user_id"],

                "username":
                    group["username"],

                "system_code":
                    group["system_code"],

                "source_id":
                    group["source_id"],

                "source_code":
                    group["source_code"],

                "database_name":
                    group["database_name"],

                "table_name":
                    group["table_name"],

                "data_object":
                    (
                        f"{group['database_name']}."
                        f"{group['table_name']}"
                    ),

                "access_count":
                    access_count,

                "window_minutes":
                    window_minutes,

                "threshold":
                    threshold,

                "sensitive_fields":
                    sorted(
                        group[
                            "sensitive_fields"
                        ]
                    ),

                "sensitivity_levels":
                    sorted(
                        group[
                            "sensitivity_levels"
                        ]
                    ),

                "first_access_at":
                    events[
                        0
                    ].created_at.isoformat(),

                "last_access_at":
                    events[
                        -1
                    ].created_at.isoformat(),

                "evidence_event_ids":
                    [
                        event.event_id
                        for event
                        in events
                    ],
            }
        )


    anomalies.sort(
        key=lambda item:
            item["last_access_at"],
        reverse=True,
    )


    return anomalies