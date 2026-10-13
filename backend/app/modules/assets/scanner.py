from app.infrastructure.database.mysql_client import (
    create_mysql_connection,
)


def scan_mysql_metadata(
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
) -> dict:
    """
    扫描 MySQL 数据库元数据。

    当前阶段只读取：
    - 数据库名
    - 数据表
    - 表类型
    - 表行数估计
    - 字段名
    - 字段类型
    - 是否允许 NULL
    - 是否主键
    - 字段顺序

    不读取业务数据内容。
    """

    connection = None

    try:
        connection = create_mysql_connection(
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password,
        )

        with connection.cursor() as cursor:

            # -------------------------
            # 1. 查询数据库中的表
            # -------------------------

            cursor.execute(
                """
                SELECT
                    TABLE_NAME,
                    TABLE_TYPE,
                    TABLE_ROWS
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
                """,
                (database_name,),
            )

            table_rows = cursor.fetchall()

            tables = []

            # -------------------------
            # 2. 查询每张表的字段
            # -------------------------

            for table_row in table_rows:

                table_name = table_row[
                    "TABLE_NAME"
                ]

                cursor.execute(
                    """
                    SELECT
                        COLUMN_NAME,
                        COLUMN_TYPE,
                        IS_NULLABLE,
                        COLUMN_KEY,
                        ORDINAL_POSITION
                    FROM information_schema.COLUMNS
                    WHERE
                        TABLE_SCHEMA = %s
                        AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                    """,
                    (
                        database_name,
                        table_name,
                    ),
                )

                column_rows = cursor.fetchall()

                columns = []

                for column_row in column_rows:

                    columns.append(
                        {
                            "column_name":
                                column_row[
                                    "COLUMN_NAME"
                                ],

                            "data_type":
                                column_row[
                                    "COLUMN_TYPE"
                                ],

                            "is_nullable":
                                column_row[
                                    "IS_NULLABLE"
                                ] == "YES",

                            "is_primary_key":
                                column_row[
                                    "COLUMN_KEY"
                                ] == "PRI",

                            "ordinal_position":
                                column_row[
                                    "ORDINAL_POSITION"
                                ],
                        }
                    )

                tables.append(
                    {
                        "table_name":
                            table_name,

                        "table_type":
                            table_row[
                                "TABLE_TYPE"
                            ],

                        "row_count":
                            table_row[
                                "TABLE_ROWS"
                            ],

                        "column_count":
                            len(columns),

                        "columns":
                            columns,
                    }
                )

        return {
            "database_name":
                database_name,

            "table_count":
                len(tables),

            "column_count":
                sum(
                    len(table["columns"])
                    for table in tables
                ),

            "tables":
                tables,
        }

    finally:
        if connection is not None:
            connection.close()