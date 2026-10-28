from types import SimpleNamespace

import app.modules.risk_control.service as risk_service

from app.modules.risk_control.service import (
    ACTION_ALLOW,
    ACTION_BLOCK,
    ACTION_LIMIT,
    ACTION_MASK,
    decide_data_access_control,
)


# =========================
# 基础测试
# =========================

def test_risk_control_action_constants():

    assert ACTION_ALLOW == "ALLOW"
    assert ACTION_MASK == "MASK"
    assert ACTION_LIMIT == "LIMIT"
    assert ACTION_BLOCK == "BLOCK"


def test_decide_data_access_control_exists():

    assert callable(
        decide_data_access_control
    )


# =========================
# 测试辅助对象
# =========================

def make_user(
    *,
    user_id: int,
    role: str,
):

    return SimpleNamespace(
        id=user_id,
        role=role,
    )


def patch_active_anomaly(
    monkeypatch,
    anomaly,
):

    monkeypatch.setattr(
        risk_service,
        "get_active_high_risk_anomaly",
        lambda **kwargs: anomaly,
    )


# =========================
# ALLOW
# admin + 无异常
# =========================

def test_admin_without_anomaly_should_allow(
    monkeypatch,
):

    user = make_user(
        user_id=1,
        role="admin",
    )

    patch_active_anomaly(
        monkeypatch,
        None,
    )


    decision = (
        decide_data_access_control(
            db=object(),
            user=user,
            source_id=1,
            database_name="crm_db",
            table_name="customer",
        )
    )


    assert (
        decision["action"]
        == ACTION_ALLOW
    )

    assert (
        decision["reason"]
        == "NORMAL_ACCESS"
    )

    assert (
        decision["risk_control_applied"]
        is False
    )

    assert (
        decision["active_anomaly_id"]
        is None
    )

    assert (
        decision["max_rows"]
        is None
    )

    assert (
        decision["mask_required"]
        is False
    )


# =========================
# MASK
# analyst + 无异常
# =========================

def test_analyst_without_anomaly_should_mask(
    monkeypatch,
):

    user = make_user(
        user_id=2,
        role="analyst",
    )

    patch_active_anomaly(
        monkeypatch,
        None,
    )


    decision = (
        decide_data_access_control(
            db=object(),
            user=user,
            source_id=1,
            database_name="crm_db",
            table_name="customer",
        )
    )


    assert (
        decision["action"]
        == ACTION_MASK
    )

    assert (
        decision["reason"]
        == "ROLE_BASED_MASKING"
    )

    assert (
        decision["risk_control_applied"]
        is False
    )

    assert (
        decision["active_anomaly_id"]
        is None
    )

    assert (
        decision["max_rows"]
        is None
    )

    assert (
        decision["mask_required"]
        is True
    )


# =========================
# LIMIT
# admin + HIGH/open
# =========================

def test_admin_with_open_high_risk_should_limit(
    monkeypatch,
):

    user = make_user(
        user_id=1,
        role="admin",
    )

    anomaly = SimpleNamespace(
        anomaly_id="test-open-anomaly",
        status="open",
        risk_level="HIGH",
    )

    patch_active_anomaly(
        monkeypatch,
        anomaly,
    )


    decision = (
        decide_data_access_control(
            db=object(),
            user=user,
            source_id=1,
            database_name="crm_db",
            table_name="customer",
        )
    )


    assert (
        decision["action"]
        == ACTION_LIMIT
    )

    assert (
        decision["reason"]
        == "ACTIVE_HIGH_RISK_ANOMALY"
    )

    assert (
        decision["risk_control_applied"]
        is True
    )

    assert (
        decision["active_anomaly_id"]
        == "test-open-anomaly"
    )

    assert (
        decision["max_rows"]
        == 5
    )

    assert (
        decision["mask_required"]
        is True
    )


# =========================
# BLOCK
# admin + HIGH/confirmed
# =========================

def test_admin_with_confirmed_high_risk_should_block(
    monkeypatch,
):

    user = make_user(
        user_id=1,
        role="admin",
    )

    anomaly = SimpleNamespace(
        anomaly_id="test-confirmed-anomaly",
        status="confirmed",
        risk_level="HIGH",
    )

    patch_active_anomaly(
        monkeypatch,
        anomaly,
    )


    decision = (
        decide_data_access_control(
            db=object(),
            user=user,
            source_id=1,
            database_name="crm_db",
            table_name="customer",
        )
    )


    assert (
        decision["action"]
        == ACTION_BLOCK
    )

    assert (
        decision["reason"]
        == "CONFIRMED_HIGH_RISK_ANOMALY"
    )

    assert (
        decision["risk_control_applied"]
        is True
    )

    assert (
        decision["active_anomaly_id"]
        == "test-confirmed-anomaly"
    )

    assert (
        decision["max_rows"]
        == 0
    )

    assert (
        decision["mask_required"]
        is False
    )


def test_build_risk_decision_should_return_complete_structure():

    decision = (
        risk_service.build_risk_decision(
            action=(
                risk_service.ACTION_LIMIT
            ),
            reason=(
                risk_service.REASON_ACTIVE_HIGH_RISK
            ),
            risk_control_applied=True,
            active_anomaly_id="anomaly-001",
            max_rows=5,
            mask_required=True,
        )
    )

    assert decision == {
        "action":
            "LIMIT",

        "reason":
            "ACTIVE_HIGH_RISK_ANOMALY",

        "risk_control_applied":
            True,

        "active_anomaly_id":
            "anomaly-001",

        "max_rows":
            5,

        "mask_required":
            True,
    }


def test_high_risk_limit_should_remain_five_rows():

    assert (
        risk_service.HIGH_RISK_MAX_ROWS
        == 5
    )