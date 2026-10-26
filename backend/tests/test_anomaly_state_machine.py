import pytest

from app.modules.access_monitoring.state_machine import (
    STATUS_CONFIRMED,
    STATUS_IGNORED,
    STATUS_OPEN,
    STATUS_RESOLVED,
    ALL_STATUSES,
    can_transition,
    is_valid_status,
    validate_transition,
)


# =========================
# 状态定义测试
# =========================

def test_all_anomaly_statuses():

    assert ALL_STATUSES == {
        "open",
        "confirmed",
        "resolved",
        "ignored",
    }


@pytest.mark.parametrize(
    "status",
    [
        STATUS_OPEN,
        STATUS_CONFIRMED,
        STATUS_RESOLVED,
        STATUS_IGNORED,
    ],
)
def test_valid_statuses(
    status,
):

    assert (
        is_valid_status(status)
        is True
    )


def test_unknown_status_is_invalid():

    assert (
        is_valid_status(
            "unknown"
        )
        is False
    )


# =========================
# 合法状态流转
# =========================

@pytest.mark.parametrize(
    (
        "current_status",
        "target_status",
    ),
    [
        (
            STATUS_OPEN,
            STATUS_CONFIRMED,
        ),
        (
            STATUS_OPEN,
            STATUS_IGNORED,
        ),
        (
            STATUS_CONFIRMED,
            STATUS_RESOLVED,
        ),
    ],
)
def test_allowed_transitions(
    current_status,
    target_status,
):

    assert (
        can_transition(
            current_status,
            target_status,
        )
        is True
    )

    # 合法流转不应抛异常
    validate_transition(
        current_status,
        target_status,
    )


# =========================
# 非法状态流转
# =========================

@pytest.mark.parametrize(
    (
        "current_status",
        "target_status",
    ),
    [
        # open 不能直接完成处置
        (
            STATUS_OPEN,
            STATUS_RESOLVED,
        ),

        # 不允许重复设置相同状态
        (
            STATUS_OPEN,
            STATUS_OPEN,
        ),
        (
            STATUS_CONFIRMED,
            STATUS_CONFIRMED,
        ),
        (
            STATUS_RESOLVED,
            STATUS_RESOLVED,
        ),
        (
            STATUS_IGNORED,
            STATUS_IGNORED,
        ),

        # confirmed 不能退回或忽略
        (
            STATUS_CONFIRMED,
            STATUS_OPEN,
        ),
        (
            STATUS_CONFIRMED,
            STATUS_IGNORED,
        ),

        # resolved 是终态
        (
            STATUS_RESOLVED,
            STATUS_OPEN,
        ),
        (
            STATUS_RESOLVED,
            STATUS_CONFIRMED,
        ),
        (
            STATUS_RESOLVED,
            STATUS_IGNORED,
        ),

        # ignored 是终态
        (
            STATUS_IGNORED,
            STATUS_OPEN,
        ),
        (
            STATUS_IGNORED,
            STATUS_CONFIRMED,
        ),
        (
            STATUS_IGNORED,
            STATUS_RESOLVED,
        ),
    ],
)
def test_forbidden_transitions(
    current_status,
    target_status,
):

    assert (
        can_transition(
            current_status,
            target_status,
        )
        is False
    )

    with pytest.raises(
        ValueError
    ):
        validate_transition(
            current_status,
            target_status,
        )


# =========================
# 非法状态名称
# =========================

def test_invalid_current_status():

    with pytest.raises(
        ValueError,
        match="当前异常事件状态非法",
    ):
        validate_transition(
            "unknown",
            STATUS_CONFIRMED,
        )


def test_invalid_target_status():

    with pytest.raises(
        ValueError,
        match="目标异常事件状态非法",
    ):
        validate_transition(
            STATUS_OPEN,
            "unknown",
        )