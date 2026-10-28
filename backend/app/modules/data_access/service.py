import pymysql

from pymysql.cursors import DictCursor

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ColumnAsset,
    DatabaseAsset,
    SensitiveFieldProfile,
    TableAsset,
)

from app.modules.credentials.service import (
    get_credential_by_key,
)
from app.modules.masking.service import (
    mask_rows,
)

def get_synced_table(
    db: Session,
    source_id: int,
    table_name: str,
):
    """
    从平台资产目录中查找指定数据源下
    已同步并处于 active 状态的数据表。

    只有已经进入资产目录的表，
    才允许后续读取真实业务数据。
    """

    row = db.execute(
        select(
            TableAsset,
            DatabaseAsset,
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

            TableAsset.table_name
            == table_name,
        )
    ).first()

    if row is None:
        return None

    table, database = row

    columns = list(
        db.scalars(
            select(
                ColumnAsset
            )
            .where(
                ColumnAsset.table_asset_id
                == table.id,

                ColumnAsset.status
                == "active",
            )
            .order_by(
                ColumnAsset.ordinal_position
            )
        ).all()
    )

    return {
        "database": database,
        "table": table,
        "columns": columns,
    }


def quote_mysql_identifier(
    value: str,
) -> str:
    """
    安全引用 MySQL 标识符。

    表名和字段名不能通过 %s 参数绑定，
    因此这里只使用经过平台资产目录验证后的名称，
    并对反引号进行转义。
    """

    escaped = value.replace(
        "`",
        "``",
    )

    return f"`{escaped}`"


def read_mysql_table(
    *,
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
    table_name: str,
    column_names: list[str],
    limit: int,
) -> list[dict]:
    """
    只读访问 MySQL 业务表。

    当前 V1：
    - 只执行 SELECT
    - 最大 100 行
    - 不执行用户传入 SQL
    - 表和字段必须来自平台资产目录
    """

    if not column_names:
        return []

    safe_limit = max(
        1,
        min(
            int(limit),
            100,
        ),
    )

    quoted_columns = ", ".join(
        quote_mysql_identifier(name)
        for name in column_names
    )

    quoted_table = (
        quote_mysql_identifier(
            table_name
        )
    )

    sql = (
        f"SELECT {quoted_columns} "
        f"FROM {quoted_table} "
        f"LIMIT {safe_limit}"
    )

    connection = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
    )

    try:

        with connection.cursor() as cursor:

            cursor.execute(sql)

            rows = cursor.fetchall()

            return list(rows)

    finally:

        connection.close()



def get_confirmed_sensitive_field_types(
    db: Session,
    table_asset_id: int,
) -> dict[str, str]:
    """
    查询指定数据表中已经人工确认的敏感字段。

    返回：

    {
        "name": "name",
        "phone": "phone",
        "id_card": "id_card",
        "salary": "salary"
    }
    """

    rows = db.execute(
        select(
            ColumnAsset.column_name,
            SensitiveFieldProfile.sensitive_type,
        )
        .join(
            SensitiveFieldProfile,
            SensitiveFieldProfile.column_asset_id
            == ColumnAsset.id,
        )
        .where(
            ColumnAsset.table_asset_id
            == table_asset_id,

            ColumnAsset.status
            == "active",

            SensitiveFieldProfile.is_sensitive
            .is_(True),

            SensitiveFieldProfile.review_status
            == "confirmed",
        )
    ).all()


    return {
        column_name: sensitive_type
        for (
            column_name,
            sensitive_type,
        ) in rows
        if sensitive_type
    }



def get_confirmed_sensitive_field_levels(
    db: Session,
    table_asset_id: int,
) -> dict[str, str]:
    """
    获取已经人工确认的敏感字段等级。

    返回示例：

    {
        "name": "L3",
        "phone": "L3",
        "id_card": "L4",
        "email": "L2"
    }
    """

    rows = db.execute(
        select(
            ColumnAsset.column_name,
            SensitiveFieldProfile.sensitivity_level,
        )
        .join(
            SensitiveFieldProfile,
            SensitiveFieldProfile.column_asset_id
            == ColumnAsset.id,
        )
        .where(
            ColumnAsset.table_asset_id
            == table_asset_id,

            ColumnAsset.status
            == "active",

            SensitiveFieldProfile.is_sensitive
            .is_(True),

            SensitiveFieldProfile.review_status
            == "confirmed",
        )
    ).all()


    return {
        column_name:
            sensitivity_level

        for (
            column_name,
            sensitivity_level,
        ) in rows

        if sensitivity_level
    }



def prepare_data_access_asset(
    *,
    db: Session,
    source,
    table_name: str,
) -> dict:
    """
    校验业务数据访问所需的数据源和资产状态。

    当前负责：
    - 数据源必须启用
    - 数据源必须为 MySQL
    - MySQL 连接参数必须完整
    - 数据表必须已经同步到资产目录
    - 数据表必须存在可读取字段

    返回：
        {
            "database": ...,
            "table": ...,
            "columns": ...
        }

    校验失败时抛出 ValueError。
    """

    if source.status != "active":
        raise ValueError(
            "数据源当前未启用"
        )

    if source.source_type != "mysql":
        raise ValueError(
            "当前业务数据访问仅支持MySQL"
        )

    if (
        not source.host
        or not source.port
        or not source.database_name
    ):
        raise ValueError(
            "MySQL数据源连接参数不完整"
        )

    asset = get_synced_table(
        db=db,
        source_id=source.id,
        table_name=table_name,
    )

    if asset is None:
        raise LookupError(
            "该数据表不存在，"
            "或尚未同步到平台资产目录"
        )

    columns = asset["columns"]

    if not columns:
        raise ValueError(
            "该数据表没有可读取字段"
        )

    return asset




def prepare_data_access_credential(
    *,
    db: Session,
    source,
) -> dict:
    """
    准备业务数据访问凭据上下文。

    当前负责：
    - 数据源必须绑定凭据
    - 凭据必须存在
    - 凭据必须启用
    - 必须能够确定数据库用户名

    注意：
    这里不解密密码。

    密码必须等风险控制完成后，
    确认不是 BLOCK 才允许解密。
    """

    if not source.secret_ref:
        raise ValueError(
            "数据源尚未绑定访问凭据"
        )

    credential = (
        get_credential_by_key(
            db,
            source.secret_ref,
        )
    )

    if credential is None:
        raise LookupError(
            "数据源绑定的凭据不存在"
        )

    if credential.status != "active":
        raise ValueError(
            "数据源凭据当前未启用"
        )

    username = (
        credential.username
        or source.username
    )

    if not username:
        raise ValueError(
            "未配置数据库用户名"
        )

    return {
        "credential":
            credential,

        "username":
            username,
    }



# =========================
# 风险执行计划
# =========================

def build_data_access_execution_plan(
    *,
    risk_decision: dict,
    requested_limit: int,
) -> dict:
    """
    根据 Risk Control 返回的决策，
    生成 Data Access 实际执行计划。

    当前负责：
    - 解析风险动作
    - 解析风险控制信息
    - 计算实际读取行数

    不负责：
    - 数据库访问
    - 密码解密
    - BLOCK 响应
    - 数据脱敏
    """

    risk_action = (
        risk_decision["action"]
    )

    risk_control_applied = (
        risk_decision[
            "risk_control_applied"
        ]
    )

    risk_control_reason = (
        risk_decision["reason"]
    )

    active_anomaly_id = (
        risk_decision[
            "active_anomaly_id"
        ]
    )

    max_rows = (
        risk_decision.get(
            "max_rows"
        )
    )

    mask_required = (
        risk_decision.get(
            "mask_required",
            False,
        )
    )


    # =========================
    # 实际读取行数
    # =========================

    effective_limit = (
        requested_limit
    )

    if (
        risk_action == "LIMIT"
        and max_rows is not None
    ):
        effective_limit = min(
            requested_limit,
            max_rows,
        )

    if risk_action == "BLOCK":
        effective_limit = 0


    return {
        "risk_action":
            risk_action,

        "risk_control_applied":
            risk_control_applied,

        "risk_control_reason":
            risk_control_reason,

        "active_anomaly_id":
            active_anomaly_id,

        "max_rows":
            max_rows,

        "mask_required":
            mask_required,

        "requested_limit":
            requested_limit,

        "effective_limit":
            effective_limit,

        "limit_applied":
            (
                effective_limit
                < requested_limit
            ),
    }


def apply_data_access_action(
    *,
    items: list[dict],
    risk_action: str,
    mask_required: bool,
    sensitive_field_types: dict[str, str],
) -> dict:
    """
    对已经读取到的业务数据执行风险处置。

    注意：
    BLOCK 不应该进入这里。
    BLOCK 必须在数据库读取前完成阻断。
    """

    masked_fields = []

    # =========================
    # ALLOW
    # =========================

    if risk_action == "ALLOW":

        return {
            "items":
                items,

            "access_mode":
                "raw",

            "masked_fields":
                masked_fields,
        }


    # =========================
    # MASK
    # =========================

    if risk_action == "MASK":

        items = mask_rows(
            rows=items,
            field_types=(
                sensitive_field_types
            ),
        )

        masked_fields = sorted(
            sensitive_field_types.keys()
        )

        return {
            "items":
                items,

            "access_mode":
                "masked",

            "masked_fields":
                masked_fields,
        }


    # =========================
    # LIMIT
    # =========================

    if risk_action == "LIMIT":

        if mask_required:

            items = mask_rows(
                rows=items,
                field_types=(
                    sensitive_field_types
                ),
            )

            masked_fields = sorted(
                sensitive_field_types.keys()
            )

            access_mode = (
                "limited_masked"
            )

        else:

            access_mode = (
                "limited"
            )

        return {
            "items":
                items,

            "access_mode":
                access_mode,

            "masked_fields":
                masked_fields,
        }


    # =========================
    # 非法执行路径
    # =========================

    if risk_action == "BLOCK":

        raise ValueError(
            "BLOCK 不允许进入数据读取后的执行阶段"
        )

    raise ValueError(
        "未知的数据访问风险处置动作："
        f"{risk_action}"
    )