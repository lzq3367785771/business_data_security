from sqlalchemy import (
    inspect,
    text,
)

from app.db.session import engine


def main():

    inspector = inspect(
        engine
    )

    columns = {
        column["name"]
        for column in inspector.get_columns(
            "anomaly_events"
        )
    }

    migrations = []


    if "risk_score" not in columns:

        migrations.append(
            """
            ALTER TABLE anomaly_events
            ADD COLUMN risk_score INT NULL
            AFTER risk_level
            """
        )


    if "risk_reasons" not in columns:

        migrations.append(
            """
            ALTER TABLE anomaly_events
            ADD COLUMN risk_reasons JSON NULL
            AFTER risk_score
            """
        )


    if "risk_features" not in columns:

        migrations.append(
            """
            ALTER TABLE anomaly_events
            ADD COLUMN risk_features JSON NULL
            AFTER risk_reasons
            """
        )


    if not migrations:

        print(
            "anomaly_events 风险评分字段已存在，"
            "无需迁移"
        )

        return


    with engine.begin() as connection:

        for sql in migrations:

            connection.execute(
                text(sql)
            )


    print(
        "anomaly_events 风险评分字段迁移完成"
    )


if __name__ == "__main__":
    main()