from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AnomalyEvent,
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


def _parse_datetime(
    value,
) -> datetime | None:

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    return datetime.fromisoformat(
        value
    )


def persist_anomalies(
    db: Session,
    anomalies: list[dict],
) -> list[AnomalyEvent]:
    """
    将检测结果写入 anomaly_events。

    去重规则：
        同一异常类型
        + 同一用户
        + 同一数据源
        + 同一数据库
        + 同一数据表
        + status = open

    如果存在：
        更新原异常事件。

    如果不存在：
        创建新的异常事件。
    """

    saved_events = []

    for anomaly in anomalies:

        statement = (
            select(
                AnomalyEvent
            )
            .where(
                AnomalyEvent.anomaly_type
                == anomaly[
                    "anomaly_type"
                ],

                AnomalyEvent.user_id
                == anomaly[
                    "user_id"
                ],

                AnomalyEvent.source_id
                == anomaly[
                    "source_id"
                ],

                AnomalyEvent.database_name
                == anomaly[
                    "database_name"
                ],

                AnomalyEvent.table_name
                == anomaly[
                    "table_name"
                ],

                AnomalyEvent.status.in_(
                    [
                        "open",
                        "confirmed",
                    ]
                ),
            )
            .order_by(
                AnomalyEvent.created_at.desc()
            )
            .limit(1)
        )


        existing = (
            db.execute(
                statement
            )
            .scalar_one_or_none()
        )


        first_access_at = (
            _parse_datetime(
                anomaly[
                    "first_access_at"
                ]
            )
        )

        last_access_at = (
            _parse_datetime(
                anomaly[
                    "last_access_at"
                ]
            )
        )


        new_evidence_ids = (
            anomaly.get(
                "evidence_event_ids"
            )
            or []
        )


        if existing:

            old_evidence_ids = (
                existing.evidence_event_ids
                or []
            )

            merged_evidence_ids = list(
                dict.fromkeys(
                    [
                        *old_evidence_ids,
                        *new_evidence_ids,
                    ]
                )
            )


            existing.risk_level = (
                anomaly[
                    "risk_level"
                ]
            )

            existing.system_code = (
                anomaly.get(
                    "system_code"
                )
            )

            existing.source_code = (
                anomaly.get(
                    "source_code"
                )
            )


            old_sensitive_fields = (
                existing.sensitive_fields
                or []
            )

            existing.sensitive_fields = (
                sorted(
                    set(
                        old_sensitive_fields
                    )
                    | set(
                        anomaly.get(
                            "sensitive_fields"
                        )
                        or []
                    )
                )
            )


            old_levels = (
                existing.sensitivity_levels
                or []
            )

            existing.sensitivity_levels = (
                sorted(
                    set(
                        old_levels
                    )
                    | set(
                        anomaly.get(
                            "sensitivity_levels"
                        )
                        or []
                    )
                )
            )


            existing.evidence_event_ids = (
                merged_evidence_ids
            )

            # 此处表示当前异常事件累计关联
            # 了多少条不同审计证据
            existing.access_count = len(
                merged_evidence_ids
            )

            existing.window_minutes = (
                anomaly[
                    "window_minutes"
                ]
            )


            if (
                existing.first_access_at
                is None
                or (
                    first_access_at
                    is not None
                    and first_access_at
                    < existing.first_access_at
                )
            ):
                existing.first_access_at = (
                    first_access_at
                )


            if (
                existing.last_access_at
                is None
                or (
                    last_access_at
                    is not None
                    and last_access_at
                    > existing.last_access_at
                )
            ):
                existing.last_access_at = (
                    last_access_at
                )


            existing.updated_at = (
                datetime.utcnow()
            )

            saved_events.append(
                existing
            )

        else:

            event = AnomalyEvent(
                anomaly_type=(
                    anomaly[
                        "anomaly_type"
                    ]
                ),

                risk_level=(
                    anomaly[
                        "risk_level"
                    ]
                ),

                user_id=(
                    anomaly[
                        "user_id"
                    ]
                ),

                system_code=(
                    anomaly.get(
                        "system_code"
                    )
                ),

                source_id=(
                    anomaly.get(
                        "source_id"
                    )
                ),

                source_code=(
                    anomaly.get(
                        "source_code"
                    )
                ),

                database_name=(
                    anomaly.get(
                        "database_name"
                    )
                ),

                table_name=(
                    anomaly.get(
                        "table_name"
                    )
                ),

                access_count=len(
                    new_evidence_ids
                ),

                window_minutes=(
                    anomaly[
                        "window_minutes"
                    ]
                ),

                sensitive_fields=(
                    anomaly.get(
                        "sensitive_fields"
                    )
                    or []
                ),

                sensitivity_levels=(
                    anomaly.get(
                        "sensitivity_levels"
                    )
                    or []
                ),

                evidence_event_ids=(
                    new_evidence_ids
                ),

                first_access_at=(
                    first_access_at
                ),

                last_access_at=(
                    last_access_at
                ),

                status="open",
            )

            db.add(
                event
            )

            saved_events.append(
                event
            )


    db.commit()


    for event in saved_events:
        db.refresh(
            event
        )


    return saved_events