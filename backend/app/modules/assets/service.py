from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    ColumnAsset,
    DatabaseAsset,
    TableAsset,
)


def sync_mysql_assets(
    db: Session,
    source_id: int,
    scan_result: dict,
) -> dict:
    """
    将 MySQL 扫描结果同步到平台资产目录。

    特点：
    1. 已存在的资产进行更新
    2. 不存在的资产自动创建
    3. 本次扫描未发现的旧资产标记为 inactive
    4. 重复执行不会不断生成重复记录
    """

    database_name = scan_result[
        "database_name"
    ]

    # =====================================
    # 1. Database Asset
    # =====================================

    database_asset = db.scalar(
        select(DatabaseAsset).where(
            DatabaseAsset.source_id == source_id,
            DatabaseAsset.database_name
            == database_name,
        )
    )

    database_created = False

    if database_asset is None:
        database_asset = DatabaseAsset(
            source_id=source_id,
            database_name=database_name,
            status="active",
        )

        db.add(database_asset)
        db.flush()

        database_created = True

    else:
        database_asset.status = "active"


    # =====================================
    # 2. 当前数据库已有 Table Assets
    # =====================================

    existing_tables = db.scalars(
        select(TableAsset).where(
            TableAsset.database_asset_id
            == database_asset.id
        )
    ).all()

    existing_table_map = {
        table.table_name: table
        for table in existing_tables
    }

    scanned_table_names = set()

    created_tables = 0
    updated_tables = 0

    created_columns = 0
    updated_columns = 0

    # =====================================
    # 3. 同步每一张表
    # =====================================

    for table_data in scan_result["tables"]:

        table_name = table_data[
            "table_name"
        ]

        scanned_table_names.add(
            table_name
        )

        table_asset = (
            existing_table_map.get(
                table_name
            )
        )

        if table_asset is None:

            table_asset = TableAsset(
                database_asset_id=
                    database_asset.id,

                table_name=
                    table_name,

                table_type=
                    table_data.get(
                        "table_type"
                    ),

                row_count=
                    table_data.get(
                        "row_count"
                    ),

                status="active",
            )

            db.add(table_asset)
            db.flush()

            created_tables += 1

        else:

            table_asset.table_type = (
                table_data.get(
                    "table_type"
                )
            )

            table_asset.row_count = (
                table_data.get(
                    "row_count"
                )
            )

            table_asset.status = "active"

            updated_tables += 1


        # =================================
        # 4. 当前表已有字段
        # =================================

        existing_columns = db.scalars(
            select(ColumnAsset).where(
                ColumnAsset.table_asset_id
                == table_asset.id
            )
        ).all()

        existing_column_map = {
            column.column_name: column
            for column in existing_columns
        }

        scanned_column_names = set()


        # =================================
        # 5. 同步字段
        # =================================

        for column_data in table_data[
            "columns"
        ]:

            column_name = column_data[
                "column_name"
            ]

            scanned_column_names.add(
                column_name
            )

            column_asset = (
                existing_column_map.get(
                    column_name
                )
            )

            if column_asset is None:

                column_asset = ColumnAsset(
                    table_asset_id=
                        table_asset.id,

                    column_name=
                        column_name,

                    data_type=
                        column_data[
                            "data_type"
                        ],

                    is_nullable=
                        column_data[
                            "is_nullable"
                        ],

                    is_primary_key=
                        column_data[
                            "is_primary_key"
                        ],

                    ordinal_position=
                        column_data[
                            "ordinal_position"
                        ],

                    status="active",
                )

                db.add(column_asset)

                created_columns += 1

            else:

                column_asset.data_type = (
                    column_data[
                        "data_type"
                    ]
                )

                column_asset.is_nullable = (
                    column_data[
                        "is_nullable"
                    ]
                )

                column_asset.is_primary_key = (
                    column_data[
                        "is_primary_key"
                    ]
                )

                column_asset.ordinal_position = (
                    column_data[
                        "ordinal_position"
                    ]
                )

                column_asset.status = (
                    "active"
                )

                updated_columns += 1


        # =================================
        # 6. 本次未扫描到的旧字段
        #    不删除，标记 inactive
        # =================================

        for column_asset in existing_columns:

            if (
                column_asset.column_name
                not in scanned_column_names
            ):
                column_asset.status = (
                    "inactive"
                )


    # =====================================
    # 7. 本次未扫描到的旧表
    # =====================================

    for table_asset in existing_tables:

        if (
            table_asset.table_name
            not in scanned_table_names
        ):
            table_asset.status = "inactive"

            old_columns = db.scalars(
                select(ColumnAsset).where(
                    ColumnAsset.table_asset_id
                    == table_asset.id
                )
            ).all()

            for column in old_columns:
                column.status = "inactive"


    # =====================================
    # 8. Commit
    # =====================================

    db.commit()

    return {
        "database_asset_id":
            database_asset.id,

        "database_created":
            database_created,

        "database_name":
            database_asset.database_name,

        "table_count":
            scan_result["table_count"],

        "column_count":
            scan_result["column_count"],

        "created_tables":
            created_tables,

        "updated_tables":
            updated_tables,

        "created_columns":
            created_columns,

        "updated_columns":
            updated_columns,
    }






def get_asset_tree(
    db,
    source_id: int,
) -> dict:
    """
    查询某个数据源已经同步到平台中的资产目录。

    不访问业务数据库。
    这里只读取平台自己的：
    database_assets
    table_assets
    column_assets
    """

    database_stmt = (
        select(DatabaseAsset)
        .where(
            DatabaseAsset.source_id
            == source_id,
            DatabaseAsset.status
            == "active",
        )
        .order_by(
            DatabaseAsset.id
        )
    )

    databases = db.scalars(
        database_stmt
    ).all()


    database_results = []

    total_tables = 0
    total_columns = 0


    for database in databases:

        table_stmt = (
            select(TableAsset)
            .where(
                TableAsset.database_asset_id
                == database.id,

                TableAsset.status
                == "active",
            )
            .order_by(
                TableAsset.id
            )
        )

        tables = db.scalars(
            table_stmt
        ).all()


        table_results = []


        for table in tables:

            column_stmt = (
                select(ColumnAsset)
                .where(
                    ColumnAsset.table_asset_id
                    == table.id,

                    ColumnAsset.status
                    == "active",
                )
                .order_by(
                    ColumnAsset.ordinal_position,
                    ColumnAsset.id,
                )
            )

            columns = db.scalars(
                column_stmt
            ).all()


            column_results = [

                {
                    "id":
                        column.id,

                    "column_name":
                        column.column_name,

                    "data_type":
                        column.data_type,

                    "is_nullable":
                        column.is_nullable,

                    "is_primary_key":
                        column.is_primary_key,

                    "ordinal_position":
                        column.ordinal_position,

                    "status":
                        column.status,
                }

                for column in columns
            ]


            table_results.append(
                {
                    "id":
                        table.id,

                    "table_name":
                        table.table_name,

                    "table_type":
                        table.table_type,

                    "row_count":
                        table.row_count,

                    "status":
                        table.status,

                    "column_count":
                        len(column_results),

                    "columns":
                        column_results,
                }
            )


            total_columns += (
                len(column_results)
            )


        database_results.append(
            {
                "id":
                    database.id,

                "database_name":
                    database.database_name,

                "status":
                    database.status,

                "table_count":
                    len(table_results),

                "tables":
                    table_results,
            }
        )


        total_tables += (
            len(table_results)
        )


    return {
        "source_id":
            source_id,

        "database_count":
            len(database_results),

        "table_count":
            total_tables,

        "column_count":
            total_columns,

        "databases":
            database_results,
    }