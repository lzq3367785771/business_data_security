import pymysql



def create_mysql_connection(
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
):
    """
    创建 MySQL 连接。

    注意：
    调用方使用完毕后必须主动 close()。
    """

    return pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database_name,
        charset="utf8mb4",
        connect_timeout=5,
        read_timeout=10,
        write_timeout=5,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def test_mysql_connection(
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
) -> dict:

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
            cursor.execute(
                "SELECT 1 AS check_value"
            )
            check_result = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                    DATABASE() AS database_name,
                    VERSION() AS server_version
                """
            )
            server_info = cursor.fetchone()

        return {
            "success": True,
            "message": "MySQL连接成功",
            "database": (
                server_info["database_name"]
                if server_info
                else database_name
            ),
            "server_version": (
                server_info["server_version"]
                if server_info
                else None
            ),
            "check_value": (
                check_result["check_value"]
                if check_result
                else None
            ),
        }

    except pymysql.MySQLError as exc:
        return {
            "success": False,
            "message": f"MySQL连接失败：{exc}",
            "database": database_name,
            "server_version": None,
            "check_value": None,
        }

    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass



def _quote_identifier(
    identifier: str,
) -> str:
    """
    安全引用 MySQL 标识符。

    表名和字段名不能通过 %s 参数化，
    因此必须进行标识符转义。
    """

    safe_identifier = (
        identifier.replace(
            "`",
            "``",
        )
    )

    return f"`{safe_identifier}`"


def sample_mysql_column(
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
    table_name: str,
    column_name: str,
    limit: int = 20,
) -> list:
    """
    从指定字段抽取少量非空值。

    原始值只返回给后端识别逻辑，
    不负责持久化或返回前端。
    """

    safe_limit = max(
        1,
        min(limit, 100),
    )

    connection = None

    try:
        connection = create_mysql_connection(
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password,
        )

        table_identifier = (
            _quote_identifier(
                table_name
            )
        )

        column_identifier = (
            _quote_identifier(
                column_name
            )
        )

        sql = f"""
            SELECT {column_identifier}
            FROM {table_identifier}
            WHERE {column_identifier}
                IS NOT NULL
            LIMIT {safe_limit}
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)

            rows = cursor.fetchall()

        return [
            row[column_name]
            for row in rows
        ]

    finally:
        if connection is not None:
            connection.close()