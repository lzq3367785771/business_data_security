from sqlalchemy import inspect, text

from app.db.session import SessionLocal


def main():

    db = SessionLocal()

    try:

        bind = db.get_bind()

        inspector = inspect(bind)

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "audit_events"
            )
        }

        if "details" in columns:

            print(
                "audit_events.details 已存在，跳过迁移"
            )

            return

        db.execute(
            text(
                """
                ALTER TABLE audit_events
                ADD COLUMN details JSON NULL
                AFTER object_count
                """
            )
        )

        db.commit()

        print(
            "audit_events.details 创建成功"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()