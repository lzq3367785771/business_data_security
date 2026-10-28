from datetime import datetime, timedelta
from types import SimpleNamespace

from app.modules.access_monitoring.service import (
    detect_frequent_raw_sensitive_access,
)


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, statement):
        return FakeResult(self.rows)


def make_audit_event(
    *,
    index: int,
    created_at: datetime,
):
    return SimpleNamespace(
        event_id=f"event-{index}",
        request_id=f"request-{index}",
        trace_id=f"trace-{index}",
        user_id=1,
        object_count=20,
        created_at=created_at,
        details={
            "access_mode": "raw",
            "source_id": 1,
            "source_code": "CRM_MYSQL",
            "system_code": "CRM",
            "database_name": "crm_db",
            "table_name": "customers",

            "sensitive_fields": [
                "name",
                "phone",
                "id_card",
            ],

            "sensitive_field_levels": {
                "name": "L3",
                "phone": "L3",
                "id_card": "L4",
            },
        },
    )


def test_frequent_raw_sensitive_access_should_use_risk_scoring():
    now = datetime.utcnow()

    rows = [
        (
            make_audit_event(
                index=index,
                created_at=(
                    now
                    - timedelta(seconds=index)
                ),
            ),
            "lzq",
        )
        for index in range(4)
    ]

    db = FakeDB(rows)

    anomalies = (
        detect_frequent_raw_sensitive_access(
            db=db,
            window_minutes=5,
            threshold=3,
        )
    )

    assert len(anomalies) == 1

    anomaly = anomalies[0]

    assert anomaly["access_count"] == 4

    assert anomaly["risk_score"] == 71

    assert anomaly["risk_level"] == "HIGH"

    assert anomaly["risk_reasons"]

    assert (
        anomaly["anomaly_type"]
        == "FREQUENT_RAW_SENSITIVE_ACCESS"
    )

    assert anomaly["user_id"] == 1
    assert anomaly["username"] == "lzq"

    assert (
        anomaly["data_object"]
        == "crm_db.customers"
    )