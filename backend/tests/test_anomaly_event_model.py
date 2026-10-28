from sqlalchemy import inspect

from app.db.models import AnomalyEvent


def test_anomaly_event_has_risk_fields():
    columns = {
        column.name: column
        for column in inspect(AnomalyEvent).columns
    }

    assert "risk_score" in columns
    assert "risk_reasons" in columns

    assert columns["risk_score"].nullable is True
    assert columns["risk_reasons"].nullable is True