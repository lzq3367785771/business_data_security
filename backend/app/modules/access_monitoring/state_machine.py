# =========================
# 异常事件状态
# =========================

STATUS_OPEN = "open"

STATUS_CONFIRMED = "confirmed"

STATUS_RESOLVED = "resolved"

STATUS_IGNORED = "ignored"


ALL_STATUSES = {
    STATUS_OPEN,
    STATUS_CONFIRMED,
    STATUS_RESOLVED,
    STATUS_IGNORED,
}


# =========================
# 合法状态流转
# =========================

ALLOWED_TRANSITIONS = {

    STATUS_OPEN: {
        STATUS_CONFIRMED,
        STATUS_IGNORED,
    },

    STATUS_CONFIRMED: {
        STATUS_RESOLVED,
    },

    # 终态
    STATUS_RESOLVED: set(),

    STATUS_IGNORED: set(),
}


# =========================
# 状态中文名称
# =========================

STATUS_LABELS = {

    STATUS_OPEN:
        "待处理",

    STATUS_CONFIRMED:
        "已确认",

    STATUS_RESOLVED:
        "已处置",

    STATUS_IGNORED:
        "已忽略",
}


def is_valid_status(
    status: str,
) -> bool:
    """
    判断状态名称是否合法。
    """

    return (
        status
        in ALL_STATUSES
    )


def can_transition(
    current_status: str,
    target_status: str,
) -> bool:
    """
    判断是否允许从 current_status
    转换到 target_status。
    """

    if (
        current_status
        not in ALL_STATUSES
    ):
        return False

    if (
        target_status
        not in ALL_STATUSES
    ):
        return False

    return (
        target_status
        in ALLOWED_TRANSITIONS[
            current_status
        ]
    )


def validate_transition(
    current_status: str,
    target_status: str,
) -> None:
    """
    校验异常事件状态流转。

    合法：
        不返回任何内容。

    非法：
        抛出 ValueError。
    """

    if (
        current_status
        not in ALL_STATUSES
    ):
        raise ValueError(
            "当前异常事件状态非法："
            f"{current_status}"
        )


    if (
        target_status
        not in ALL_STATUSES
    ):
        raise ValueError(
            "目标异常事件状态非法："
            f"{target_status}"
        )


    if (
        not can_transition(
            current_status,
            target_status,
        )
    ):

        current_label = (
            STATUS_LABELS.get(
                current_status,
                current_status,
            )
        )

        target_label = (
            STATUS_LABELS.get(
                target_status,
                target_status,
            )
        )

        raise ValueError(
            "不允许将异常事件从"
            f"“{current_label}”"
            "修改为"
            f"“{target_label}”"
        )