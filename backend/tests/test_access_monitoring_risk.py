import app.modules.access_monitoring.router as access_monitoring_router

from datetime import datetime, timedelta
from types import SimpleNamespace

from app.modules.access_monitoring.service import (
    detect_frequent_raw_sensitive_access,
)

import app.modules.access_monitoring.service as access_monitoring_service

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



def test_list_anomaly_events_should_filter_by_min_risk_score(
    monkeypatch,
):
    captured = {}

    class FakeQueryResult:
        def all(self):
            return []

    class FakeQueryDB:
        def execute(
            self,
            statement,
        ):
            captured["statement"] = statement
            return FakeQueryResult()

    monkeypatch.setattr(
        access_monitoring_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=1
            ),
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "write_audit",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "success",
        lambda request, data, message=None: data,
    )

    db = FakeQueryDB()

    access_monitoring_router.list_anomaly_events(
        request=SimpleNamespace(),
        status=None,
        risk_level=None,
        min_risk_score=70,
        limit=100,
        db=db,
        user=SimpleNamespace(
            id=1
        ),
    )

    statement = captured["statement"]

    compiled = statement.compile()

    sql_text = str(compiled)

    assert (
        "anomaly_events.risk_score >="
        in sql_text
    )

    assert 70 in compiled.params.values()



def test_anomaly_event_summary_should_return_risk_statistics(
    monkeypatch,
):
    scalar_values = iter([
        5,      # total_count
        1,      # scored_count
        5,      # high_risk_count
        1,      # open_count
        74,     # average_risk_score
        74,     # max_risk_score
    ])

    class FakeSummaryDB:
        def scalar(
            self,
            statement,
        ):
            return next(
                scalar_values
            )

    monkeypatch.setattr(
        access_monitoring_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=1
            ),
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "write_audit",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "success",
        lambda request, data, message=None:
            data,
    )

    result = (
        access_monitoring_router
        .get_anomaly_event_summary(
            request=SimpleNamespace(),
            db=FakeSummaryDB(),
            user=SimpleNamespace(
                id=1
            ),
        )
    )

    assert result[
        "total_count"
    ] == 5

    assert result[
        "scored_count"
    ] == 1

    assert result[
        "unscored_count"
    ] == 4

    assert result[
        "high_risk_count"
    ] == 5

    assert result[
        "open_count"
    ] == 1

    assert result[
        "average_risk_score"
    ] == 74.0

    assert result[
        "max_risk_score"
    ] == 74



def test_detect_anomaly_should_include_risk_features(
    monkeypatch,
):
    fake_event = SimpleNamespace(
        event_id="event-1",
        user_id=1,
        object_count=20,
        created_at=datetime.utcnow(),
        details={
            "access_mode": "raw",
            "sensitive_fields": [
                "name",
                "phone",
                "id_card",
            ],
            "sensitive_field_levels": {
                "name": "L2",
                "phone": "L3",
                "id_card": "L4",
            },
            "source_id": 1,
            "source_code": "CRM_MYSQL",
            "system_code": "CRM",
            "database_name": "crm_db",
            "table_name": "customer",
        },
    )

    rows = [
        (fake_event, "admin"),
        (fake_event, "admin"),
        (fake_event, "admin"),
    ]

    class FakeResult:
        def all(self):
            return rows

    class FakeDB:
        def execute(
            self,
            statement,
        ):
            return FakeResult()

    monkeypatch.setattr(
        access_monitoring_service,
        "evaluate_access_risk",
        lambda **kwargs: {
            "features": {
                "access_count": 3,
                "requested_rows": 20,
                "highest_sensitivity_level":
                    "L4",
                "l4_field_count": 1,
                "access_mode": "raw",
                "sensitive_field_count": 3,
            },
            "risk_score": 74,
            "risk_level": "HIGH",
            "reasons": [
                "测试风险原因"
            ],
        },
    )

    anomalies = (
        access_monitoring_service
        .detect_frequent_raw_sensitive_access(
            db=FakeDB(),
            window_minutes=5,
            threshold=3,
        )
    )

    assert len(anomalies) == 1

    anomaly = anomalies[0]

    assert anomaly[
        "risk_score"
    ] == 74

    assert anomaly[
        "risk_level"
    ] == "HIGH"

    assert anomaly[
        "risk_features"
    ][
        "highest_sensitivity_level"
    ] == "L4"

    assert anomaly[
        "risk_features"
    ][
        "sensitive_field_count"
    ] == 3




def test_get_anomaly_event_detail_should_return_full_risk_context(
    monkeypatch,
):
    now = datetime.utcnow()

    fake_event = SimpleNamespace(
        anomaly_id="anomaly-1",
        anomaly_type=(
            "FREQUENT_RAW_"
            "SENSITIVE_ACCESS"
        ),
        risk_level="HIGH",
        risk_score=74,
        risk_reasons=[
            "短时间内访问较频繁",
            "访问对象包含 L4 高敏感字段",
        ],
        risk_features={
            "access_count": 5,
            "requested_rows": 20,
            "highest_sensitivity_level":
                "L4",
            "l4_field_count": 1,
            "access_mode": "raw",
            "sensitive_field_count": 3,
        },
        status="open",
        user_id=1,
        system_code="CRM",
        source_id=1,
        source_code="CRM_MYSQL",
        database_name="crm_db",
        table_name="customer",
        access_count=5,
        window_minutes=5,
        sensitive_fields=[
            "name",
            "phone",
            "id_card",
        ],
        sensitivity_levels=[
            "L2",
            "L3",
            "L4",
        ],
        evidence_event_ids=[
            "event-1",
            "event-2",
            "event-3",
        ],
        first_access_at=now,
        last_access_at=now,
        created_at=now,
        updated_at=now,
    )

    class FakeResult:
        def first(self):
            return (
                fake_event,
                "admin",
            )

    class FakeDB:
        def execute(
            self,
            statement,
        ):
            return FakeResult()

    monkeypatch.setattr(
        access_monitoring_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=1
            ),
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "write_audit",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "success",
        lambda request, data, message=None:
            data,
    )

    result = (
        access_monitoring_router
        .get_anomaly_event_detail(
            anomaly_id="anomaly-1",
            request=SimpleNamespace(),
            db=FakeDB(),
            user=SimpleNamespace(
                id=1
            ),
        )
    )

    assert result[
        "anomaly_id"
    ] == "anomaly-1"

    assert result[
        "risk_score"
    ] == 74

    assert result[
        "risk_level"
    ] == "HIGH"

    assert result[
        "risk_features"
    ][
        "highest_sensitivity_level"
    ] == "L4"

    assert result[
        "risk_features"
    ][
        "access_mode"
    ] == "raw"

    assert result[
        "sensitive_fields"
    ] == [
        "name",
        "phone",
        "id_card",
    ]

    assert result[
        "evidence_event_ids"
    ] == [
        "event-1",
        "event-2",
        "event-3",
    ]



def test_get_anomaly_event_evidence_should_return_audit_timeline(
    monkeypatch,
):
    now = datetime.utcnow()

    fake_anomaly = SimpleNamespace(
        anomaly_id="anomaly-1",
        evidence_event_ids=[
            "event-1",
            "event-2",
        ],
    )


    first_event = SimpleNamespace(
        event_id="event-1",
        request_id="request-1",
        trace_id="trace-1",
        user_id=1,
        action="READ_BUSINESS_DATA",
        resource="data_access:preview",
        result="ALLOW",
        policy_id=1,
        object_count=20,
        details={
            "access_mode": "raw",
            "system_code": "CRM",
            "source_code": "CRM_MYSQL",
            "database_name": "crm_db",
            "table_name": "customer",
            "sensitive_fields": [
                "name",
                "phone",
                "id_card",
            ],
        },
        created_at=now,
    )


    second_event = SimpleNamespace(
        event_id="event-2",
        request_id="request-2",
        trace_id="trace-2",
        user_id=1,
        action="READ_BUSINESS_DATA",
        resource="data_access:preview",
        result="ALLOW",
        policy_id=1,
        object_count=20,
        details={
            "access_mode": "raw",
            "system_code": "CRM",
            "source_code": "CRM_MYSQL",
            "database_name": "crm_db",
            "table_name": "customer",
            "sensitive_fields": [
                "name",
                "phone",
                "id_card",
            ],
        },
        created_at=(
            now
            + timedelta(seconds=1)
        ),
    )


    rows = [
        (
            first_event,
            "admin",
        ),
        (
            second_event,
            "admin",
        ),
    ]


    captured = {}


    class FakeEvidenceResult:
        def all(self):
            return rows


    class FakeEvidenceDB:
        def get(
            self,
            model,
            key,
        ):
            return fake_anomaly

        def execute(
            self,
            statement,
        ):
            captured["statement"] = (
                statement
            )

            return FakeEvidenceResult()


    monkeypatch.setattr(
        access_monitoring_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=1
            ),
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "write_audit",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        access_monitoring_router,
        "success",
        lambda request, data, message=None:
            data,
    )


    result = (
        access_monitoring_router
        .get_anomaly_event_evidence(
            anomaly_id="anomaly-1",
            request=SimpleNamespace(),
            db=FakeEvidenceDB(),
            user=SimpleNamespace(
                id=1
            ),
        )
    )


    assert result[
        "anomaly_id"
    ] == "anomaly-1"

    assert result[
        "expected_count"
    ] == 2

    assert result[
        "evidence_count"
    ] == 2

    assert result[
        "missing_event_ids"
    ] == []


    assert result[
        "items"
    ][0][
        "event_id"
    ] == "event-1"

    assert result[
        "items"
    ][0][
        "username"
    ] == "admin"

    assert result[
        "items"
    ][0][
        "action"
    ] == "READ_BUSINESS_DATA"

    assert result[
        "items"
    ][0][
        "access_mode"
    ] == "raw"

    assert result[
        "items"
    ][0][
        "data_object"
    ] == "crm_db.customer"


    statement = (
        captured["statement"]
    )

    sql_text = str(
        statement.compile()
    )

    assert (
        "ORDER BY audit_events.created_at ASC"
        in sql_text
    )