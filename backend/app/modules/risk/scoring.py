from app.modules.risk.features import (
    build_access_risk_features,
)


# =========================
# 风险等级
# =========================

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"


def calculate_risk_score(
    features: dict,
) -> dict:
    """
    根据风险特征计算 0~100 风险分。

    返回：
    - risk_score
    - risk_level
    - reasons
    """

    score = 0
    reasons = []


    # =========================
    # 1. 访问频率
    # =========================

    access_count = int(
        features.get(
            "access_count",
            0,
        )
    )

    if access_count >= 10:
        score += 25
        reasons.append(
            "短时间内访问次数很高"
        )

    elif access_count >= 5:
        score += 18
        reasons.append(
            "短时间内访问较频繁"
        )

    elif access_count >= 3:
        score += 10
        reasons.append(
            "短时间内存在重复访问"
        )


    # =========================
    # 2. 请求数据量
    # =========================

    requested_rows = int(
        features.get(
            "requested_rows",
            0,
        )
    )

    if requested_rows >= 100:
        score += 15
        reasons.append(
            "单次请求数据量较大"
        )

    elif requested_rows >= 50:
        score += 10
        reasons.append(
            "单次请求数据量偏高"
        )

    elif requested_rows >= 20:
        score += 5


    # =========================
    # 3. 最高敏感等级
    # =========================

    sensitivity_score = int(
        features.get(
            "max_sensitivity_score",
            1,
        )
    )

    if sensitivity_score >= 4:
        score += 25
        reasons.append(
            "访问对象包含 L4 高敏感字段"
        )

    elif sensitivity_score == 3:
        score += 15
        reasons.append(
            "访问对象包含 L3 敏感字段"
        )

    elif sensitivity_score == 2:
        score += 8
        reasons.append(
            "访问对象包含 L2 敏感字段"
        )


    # =========================
    # 4. L4 字段数量
    # =========================

    l4_field_count = int(
        features.get(
            "l4_field_count",
            0,
        )
    )

    if l4_field_count >= 2:
        score += 10
        reasons.append(
            "同时涉及多个 L4 高敏感字段"
        )

    elif l4_field_count == 1:
        score += 6


    # =========================
    # 5. 原始数据访问
    # =========================

    if features.get(
        "is_raw_access",
        False,
    ):
        score += 20
        reasons.append(
            "当前访问为原始数据访问"
        )


    # =========================
    # 6. 敏感字段数量
    # =========================

    sensitive_field_count = int(
        features.get(
            "sensitive_field_count",
            0,
        )
    )

    if sensitive_field_count >= 3:
        score += 5
        reasons.append(
            "访问涉及多个敏感字段"
        )


    # =========================
    # 总分限制
    # =========================

    score = min(
        score,
        100,
    )


    # =========================
    # 风险等级
    # =========================

    if score >= 60:
        risk_level = RISK_HIGH

    elif score >= 30:
        risk_level = RISK_MEDIUM

    else:
        risk_level = RISK_LOW


    return {
        "risk_score":
            score,

        "risk_level":
            risk_level,

        "reasons":
            reasons,
    }


def evaluate_access_risk(
    *,
    access_count: int,
    requested_rows: int,
    sensitive_field_levels: dict[str, str],
    access_mode: str,
    user_role: str | None = None,
) -> dict:
    """
    业务数据访问风险评估统一入口。

    流程：
        访问上下文
            ↓
        风险特征提取
            ↓
        风险评分
            ↓
        返回完整评估结果

    当前只负责分析风险，
    不负责 ALLOW / MASK / LIMIT / BLOCK 决策。
    """

    features = (
        build_access_risk_features(
            access_count=access_count,
            requested_rows=requested_rows,
            sensitive_field_levels=(
                sensitive_field_levels
            ),
            access_mode=access_mode,
            user_role=user_role,
        )
    )

    score_result = (
        calculate_risk_score(
            features
        )
    )

    return {
        "features":
            features,

        "risk_score":
            score_result[
                "risk_score"
            ],

        "risk_level":
            score_result[
                "risk_level"
            ],

        "reasons":
            score_result[
                "reasons"
            ],
    }