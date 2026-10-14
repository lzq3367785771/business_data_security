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