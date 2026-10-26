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


def get_active_high_risk_anomaly(
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

    已结束：
        ignored
        resolved
    """

    statement = (
        select(AnomalyEvent)
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
        db.execute(statement)
        .scalar_one_or_none()
    )


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

    analyst / 非 admin
        -> MASK

    admin + 活跃 HIGH
        -> MASK

    后续可扩展：
        LIMIT
        BLOCK
    """

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
    # HIGH 风险优先
    # =========================

    if active_anomaly is not None:

        # =========================
        # 已确认高风险异常
        # -> 完全阻断
        # =========================

        if (
            active_anomaly.status
            == "confirmed"
        ):

            return {
                "action":
                    ACTION_BLOCK,

                "reason":
                    "CONFIRMED_HIGH_RISK_ANOMALY",

                "risk_level":
                    "HIGH",

                "risk_control_applied":
                    True,

                "active_anomaly_id":
                    active_anomaly.anomaly_id,

                "max_rows":
                    0,

                "mask_required":
                    False,
            }


        # =========================
        # 新发现高风险异常
        # -> 限流 + 动态脱敏
        # =========================

        return {
            "action":
                ACTION_LIMIT,

            "reason":
                "ACTIVE_HIGH_RISK_ANOMALY",

            "risk_level":
                "HIGH",

            "risk_control_applied":
                True,

            "active_anomaly_id":
                active_anomaly.anomaly_id,

            "max_rows":
                5,

            "mask_required":
                True,
        }


    # =========================
    # 角色权限控制
    # =========================

    if user.role != "admin":

        return {
            "action":
                ACTION_MASK,

            "reason":
                "ROLE_BASED_MASKING",

            "risk_level":
                None,

            "risk_control_applied":
                False,

            "active_anomaly_id":
                None,

            "max_rows":
                None,

            "mask_required":
                True,
        }


    # =========================
    # 正常管理员访问
    # =========================

    return {
        "action":
            ACTION_ALLOW,

        "reason":
            "NORMAL_ACCESS",

        "risk_level":
            None,

        "risk_control_applied":
            False,

        "active_anomaly_id":
            None,

        "max_rows":
            None,

        "mask_required":
            False,
    }