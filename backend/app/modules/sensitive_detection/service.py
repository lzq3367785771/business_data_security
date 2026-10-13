from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ColumnAsset,
    SensitiveFieldProfile,
)

from app.modules.sensitive_detection.rules import (
    detect_by_field_name,
)
from sqlalchemy import select

from app.db.models import (
    ColumnAsset,
    DatabaseAsset,
    SensitiveFieldProfile,
    TableAsset,
)

from app.infrastructure.database.mysql_client import (
    sample_mysql_column,
)

from app.modules.sensitive_detection.content_rules import (
    analyze_sample_values,
)

from app.modules.sensitive_detection.fusion import (
    fuse_detection,
)

from app.modules.sensitive_detection.rules import (
    detect_by_field_name,
)




def detect_sensitive_columns(
    db: Session,
) -> dict:
    """
    对所有 active 字段资产执行敏感字段识别。

    已存在画像：
        更新

    不存在画像：
        创建

    因此可以重复执行。
    """

    columns = db.scalars(
        select(ColumnAsset).where(
            ColumnAsset.status == "active"
        )
    ).all()

    if not columns:
        return {
            "total_columns": 0,
            "sensitive_columns": 0,
            "normal_columns": 0,
            "created_profiles": 0,
            "updated_profiles": 0,
            "results": [],
        }

    sensitive_count = 0
    normal_count = 0

    created_count = 0
    updated_count = 0

    results = []

    for column in columns:

        detection = detect_by_field_name(
            column.column_name
        )

        if detection["is_sensitive"]:
            sensitive_count += 1
        else:
            normal_count += 1

        profile = db.scalar(
            select(
                SensitiveFieldProfile
            ).where(
                SensitiveFieldProfile.column_asset_id
                == column.id
            )
        )

        if profile is None:

            profile = SensitiveFieldProfile(
                column_asset_id=column.id,
            )

            db.add(profile)

            created_count += 1

        else:
            updated_count += 1

        profile.is_sensitive = (
            detection["is_sensitive"]
        )

        profile.sensitive_type = (
            detection["sensitive_type"]
        )

        profile.sensitive_label = (
            detection["sensitive_label"]
        )

        profile.sensitivity_level = (
            detection["sensitivity_level"]
        )

        profile.detection_method = (
            detection["detection_method"]
        )

        profile.confidence = (
            detection["confidence"]
        )

        profile.detection_reason = (
            detection["detection_reason"]
        )

        # 第一阶段自动识别结果等待复核
        if profile.review_status not in {
            "confirmed",
            "rejected",
        }:
            profile.review_status = "pending"

        results.append(
            {
                "column_asset_id":
                    column.id,

                "column_name":
                    column.column_name,

                **detection,
            }
        )

    db.commit()

    return {
        "total_columns":
            len(columns),

        "sensitive_columns":
            sensitive_count,

        "normal_columns":
            normal_count,

        "created_profiles":
            created_count,

        "updated_profiles":
            updated_count,

        "results":
            results,
    }


def detect_sensitive_columns_with_content(
    db: Session,
    source_id: int,
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
    sample_limit: int = 20,
) -> dict:
    """
    对指定数据源执行：

    字段名规则
        +
    真实内容抽样
        +
    融合识别

    原始业务数据不会写入平台数据库，
    也不会包含在返回结果中。
    """

    rows = db.execute(
        select(
            ColumnAsset,
            TableAsset,
        )
        .join(
            TableAsset,
            ColumnAsset.table_asset_id
            == TableAsset.id,
        )
        .join(
            DatabaseAsset,
            TableAsset.database_asset_id
            == DatabaseAsset.id,
        )
        .where(
            DatabaseAsset.source_id
            == source_id,

            DatabaseAsset.status
            == "active",

            TableAsset.status
            == "active",

            ColumnAsset.status
            == "active",
        )
        .order_by(
            TableAsset.id,
            ColumnAsset.ordinal_position,
        )
    ).all()

    total_columns = len(rows)

    sensitive_count = 0
    normal_count = 0

    hybrid_count = 0
    content_count = 0
    rule_count = 0

    conflict_count = 0

    results = []

    for column, table in rows:

        # -------------------------
        # 1. 字段名识别
        # -------------------------

        rule_result = detect_by_field_name(
            column.column_name
        )

        # -------------------------
        # 2. 安全抽样
        # -------------------------

        values = sample_mysql_column(
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password,
            table_name=table.table_name,
            column_name=column.column_name,
            limit=sample_limit,
        )

        # -------------------------
        # 3. 内容识别
        # -------------------------

        content_result = (
            analyze_sample_values(
                values
            )
        )

        # 原始值立即释放
        del values

        # -------------------------
        # 4. 融合
        # -------------------------

        detection = fuse_detection(
            rule_result=rule_result,
            content_result=content_result,
        )

        # -------------------------
        # 5. 更新画像
        # -------------------------

        profile = db.scalar(
            select(
                SensitiveFieldProfile
            ).where(
                SensitiveFieldProfile.column_asset_id
                == column.id
            )
        )

        if profile is None:
            profile = SensitiveFieldProfile(
                column_asset_id=column.id,
            )

            db.add(profile)

        profile.is_sensitive = (
            detection["is_sensitive"]
        )

        profile.sensitive_type = (
            detection["sensitive_type"]
        )

        profile.sensitive_label = (
            detection["sensitive_label"]
        )

        profile.sensitivity_level = (
            detection[
                "sensitivity_level"
            ]
        )

        profile.detection_method = (
            detection[
                "detection_method"
            ]
        )

        profile.confidence = (
            detection["confidence"]
        )

        profile.detection_reason = (
            detection[
                "detection_reason"
            ]
        )

        # 已人工确认/拒绝的状态不覆盖
        if profile.review_status not in {
            "confirmed",
            "rejected",
        }:
            profile.review_status = "pending"

        # -------------------------
        # 6. 统计
        # -------------------------

        if detection["is_sensitive"]:
            sensitive_count += 1
        else:
            normal_count += 1

        # 只统计“敏感字段”的识别方式，
        # 普通字段不计入 rule/content/hybrid 数量。
        if detection["is_sensitive"]:

            method = detection[
                "detection_method"
            ]

            if method == "hybrid":
                hybrid_count += 1

            elif method == "content":
                content_count += 1

            else:
                rule_count += 1

        if detection.get("conflict"):
            conflict_count += 1

        # -------------------------
        # 7. 返回安全信息
        #    不返回任何真实样本
        # -------------------------

        results.append(
            {
                "column_asset_id":
                    column.id,

                "table_name":
                    table.table_name,

                "column_name":
                    column.column_name,

                "is_sensitive":
                    detection[
                        "is_sensitive"
                    ],

                "sensitive_type":
                    detection[
                        "sensitive_type"
                    ],

                "sensitive_label":
                    detection[
                        "sensitive_label"
                    ],

                "sensitivity_level":
                    detection[
                        "sensitivity_level"
                    ],

                "detection_method":
                    detection[
                        "detection_method"
                    ],

                "confidence":
                    detection[
                        "confidence"
                    ],

                "sample_count":
                    detection.get(
                        "content_sample_count",
                        0,
                    ),

                "matched_count":
                    detection.get(
                        "content_matched_count",
                        0,
                    ),

                "match_ratio":
                    detection.get(
                        "content_match_ratio",
                        0.0,
                    ),

                "conflict":
                    detection.get(
                        "conflict",
                        False,
                    ),

                "detection_reason":
                    detection[
                        "detection_reason"
                    ],
            }
        )

    db.commit()

    return {
        "total_columns":
            total_columns,

        "sensitive_columns":
            sensitive_count,

        "normal_columns":
            normal_count,

        "rule_detected":
            rule_count,

        "content_detected":
            content_count,

        "hybrid_detected":
            hybrid_count,

        "conflicts":
            conflict_count,

        "sample_limit":
            sample_limit,

        "results":
            results,
    }


def list_sensitive_field_profiles(
    db: Session,
    source_id: int | None = None,
    is_sensitive: bool | None = None,
    review_status: str | None = None,
    sensitivity_level: str | None = None,
) -> list[dict]:
    """
    查询敏感字段画像。

    返回：
    数据源
    数据库
    数据表
    字段
    敏感类型
    等级
    识别方式
    置信度
    复核状态
    """

    stmt = (
        select(
            SensitiveFieldProfile,
            ColumnAsset,
            TableAsset,
            DatabaseAsset,
        )
        .join(
            ColumnAsset,
            SensitiveFieldProfile.column_asset_id
            == ColumnAsset.id,
        )
        .join(
            TableAsset,
            ColumnAsset.table_asset_id
            == TableAsset.id,
        )
        .join(
            DatabaseAsset,
            TableAsset.database_asset_id
            == DatabaseAsset.id,
        )
        .order_by(
            DatabaseAsset.id,
            TableAsset.id,
            ColumnAsset.ordinal_position,
        )
    )

    if source_id is not None:
        stmt = stmt.where(
            DatabaseAsset.source_id
            == source_id
        )

    if is_sensitive is not None:
        stmt = stmt.where(
            SensitiveFieldProfile.is_sensitive
            == is_sensitive
        )

    if review_status is not None:
        stmt = stmt.where(
            SensitiveFieldProfile.review_status
            == review_status
        )

    if sensitivity_level is not None:
        stmt = stmt.where(
            SensitiveFieldProfile.sensitivity_level
            == sensitivity_level
        )

    rows = db.execute(
        stmt
    ).all()

    results = []

    for (
        profile,
        column,
        table,
        database,
    ) in rows:

        results.append(
            {
                "profile_id":
                    profile.id,

                "source_id":
                    database.source_id,

                "database_name":
                    database.database_name,

                "table_name":
                    table.table_name,

                "column_asset_id":
                    column.id,

                "column_name":
                    column.column_name,

                "data_type":
                    column.data_type,

                "is_sensitive":
                    profile.is_sensitive,

                "sensitive_type":
                    profile.sensitive_type,

                "sensitive_label":
                    profile.sensitive_label,

                "sensitivity_level":
                    profile.sensitivity_level,

                "detection_method":
                    profile.detection_method,

                "confidence":
                    profile.confidence,

                "review_status":
                    profile.review_status,

                "detection_reason":
                    profile.detection_reason,
            }
        )

    return results


def review_sensitive_field(
    db: Session,
    profile_id: int,
    review_status: str,
) -> SensitiveFieldProfile | None:
    """
    人工确认或驳回敏感字段识别结果。
    """

    profile = db.get(
        SensitiveFieldProfile,
        profile_id,
    )

    if profile is None:
        return None

    profile.review_status = (
        review_status
    )

    db.commit()
    db.refresh(profile)

    return profile