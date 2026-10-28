from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AnomalyEvent,
    User,
)


# =========================
# 风险处置动作
# =========================

ACTION_ALLOW = "ALLOW"
ACTION_MASK = "MASK"
ACTION_LIMIT = "LIMIT"
ACTION_BLOCK = "BLOCK"


# =========================
# 风险处置原因
# =========================

REASON_NORMAL_ACCESS = (
    "NORMAL_ACCESS"
)

REASON_ROLE_BASED_MASKING = (
    "ROLE_BASED_MASKING"
)

REASON_ACTIVE_HIGH_RISK = (
    "ACTIVE_HIGH_RISK_ANOMALY"
)

REASON_CONFIRMED_HIGH_RISK = (
    "CONFIRMED_HIGH_RISK_ANOMALY"
)


# =========================
# 风险控制参数
# =========================

HIGH_RISK_MAX_ROWS = 5


# =========================
# 风险上下文查询
# =========================

def get_active_high_risk_anomaly(
    *,
    db: Session,
    user_id: int,
    source_id: int,
    database_name: str,
    table_name: str,
) -> AnomalyEvent | None:
    """
    查询当前用户访问指定数据对象时，
    是否存在活跃 HIGH 风险异常。

    活跃状态：
        open
        confirmed

    已结束状态：
        ignored
        resolved

    如果存在多个活跃异常，
    优先返回最近发生访问的异常。
    """

    statement = (
        select(
            AnomalyEvent
        )
        .where(
            AnomalyEvent.user_id
            == user_id,

            AnomalyEvent.source_id
            == source_id,

            AnomalyEvent.database_name
            == database_name,

            AnomalyEvent.table_name
            == table_name,

            AnomalyEvent.risk_level
            == "HIGH",

            AnomalyEvent.status.in_(
                [
                    "open",
                    "confirmed",
                ]
            ),
        )
        .order_by(
            AnomalyEvent.last_access_at.desc(),
            AnomalyEvent.created_at.desc(),
        )
        .limit(1)
    )

    return (
        db.execute(
            statement
        )
        .scalar_one_or_none()
    )


# =========================
# 风险决策构造
# =========================

def build_risk_decision(
    *,
    action: str,
    reason: str,
    risk_control_applied: bool,
    active_anomaly_id=None,
    max_rows=None,
    mask_required: bool = False,
) -> dict:
    """
    构造统一的风险控制决策。

    所有 ALLOW / MASK / LIMIT / BLOCK
    都通过这里生成统一结构。
    """

    return {
        "action":
            action,

        "reason":
            reason,

        "risk_control_applied":
            risk_control_applied,

        "active_anomaly_id":
            active_anomaly_id,

        "max_rows":
            max_rows,

        "mask_required":
            mask_required,
    }


# =========================
# 数据访问风险决策
# =========================

def decide_data_access_control(
    db: Session,
    user: User,
    source_id: int,
    database_name: str,
    table_name: str,
) -> dict:
    """
    数据访问风险处置决策。

    当前 V1：

    admin + 无活跃 HIGH
        -> ALLOW

    非 admin + 无活跃 HIGH
        -> MASK

    活跃 HIGH + open
        -> LIMIT
        -> 最大 5 行
        -> 强制动态脱敏

    活跃 HIGH + confirmed
        -> BLOCK

    ignored / resolved
        -> 不参与风险控制
    """

    # =========================
    # 1. 查询风险上下文
    # =========================

    active_anomaly = (
        get_active_high_risk_anomaly(
            db=db,
            user_id=user.id,
            source_id=source_id,
            database_name=database_name,
            table_name=table_name,
        )
    )


    # =========================
    # 2. HIGH 风险优先
    # =========================

    if active_anomaly is not None:

        # -------------------------
        # confirmed
        # -> 完全阻断
        # -------------------------

        if (
            active_anomaly.status
            == "confirmed"
        ):

            return build_risk_decision(
                action=ACTION_BLOCK,
                reason=(
                    REASON_CONFIRMED_HIGH_RISK
                ),
                risk_control_applied=True,
                active_anomaly_id=(
                    active_anomaly.anomaly_id
                ),
                max_rows=0,
                mask_required=False,
            )


        # -------------------------
        # open
        # -> 限流 + 动态脱敏
        # -------------------------

        return build_risk_decision(
            action=ACTION_LIMIT,
            reason=(
                REASON_ACTIVE_HIGH_RISK
            ),
            risk_control_applied=True,
            active_anomaly_id=(
                active_anomaly.anomaly_id
            ),
            max_rows=(
                HIGH_RISK_MAX_ROWS
            ),
            mask_required=True,
        )


    # =========================
    # 3. 角色访问控制
    # =========================

    if user.role != "admin":

        return build_risk_decision(
            action=ACTION_MASK,
            reason=(
                REASON_ROLE_BASED_MASKING
            ),
            risk_control_applied=False,
            active_anomaly_id=None,
            max_rows=None,
            mask_required=True,
        )


    # =========================
    # 4. 正常管理员访问
    # =========================

    return build_risk_decision(
        action=ACTION_ALLOW,
        reason=(
            REASON_NORMAL_ACCESS
        ),
        risk_control_applied=False,
        active_anomaly_id=None,
        max_rows=None,
        mask_required=False,
    )