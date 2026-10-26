from sqlalchemy import inspect

from app.db.models import AnomalyEvent
from app.db.session import engine


def main():

    inspector = inspect(engine)

    existing_tables = (
        inspector.get_table_names()
    )

    if "anomaly_events" in existing_tables:
        print(
            "anomaly_events 表已存在，跳过"
        )
        return

    AnomalyEvent.__table__.create(
        bind=engine
    )

    print(
        "anomaly_events 表创建成功"
    )


if __name__ == "__main__":
    main()