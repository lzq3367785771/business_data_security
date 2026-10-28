# =========================
# 风险特征常量
# =========================

SENSITIVITY_LEVEL_SCORES = {
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
}


# =========================
# 敏感等级工具
# =========================

def normalize_sensitivity_level(
    level: str | None,
) -> str:
    """
    标准化敏感等级。

    非法值或空值统一按 L1 处理。
    """

    if not level:
        return "L1"

    normalized = (
        str(level)
        .strip()
        .upper()
    )

    if normalized not in (
        SENSITIVITY_LEVEL_SCORES
    ):
        return "L1"

    return normalized


def get_max_sensitivity_level(
    levels: list[str],
) -> str:
    """
    获取字段集合中的最高敏感等级。
    """

    if not levels:
        return "L1"

    normalized_levels = [
        normalize_sensitivity_level(
            level
        )
        for level in levels
    ]

    return max(
        normalized_levels,
        key=lambda level:
            SENSITIVITY_LEVEL_SCORES[
                level
            ],
    )


# =========================
# 风险特征提取
# =========================

def extract_risk_features(
    *,
    access_count: int,
    requested_rows: int,
    sensitive_field_levels: dict[str, str],
    access_mode: str,
) -> dict:
    """
    从一次业务数据访问上下文中
    提取统一风险特征。

    当前 V1 特征：

    - access_count
        当前统计窗口内访问次数

    - requested_rows
        当前请求读取的数据量

    - sensitive_field_count
        涉及的敏感字段数量

    - max_sensitivity_level
        当前数据对象最高敏感等级

    - l4_field_count
        L4 高敏感字段数量

    - is_raw_access
        是否为原始数据访问
    """

    safe_access_count = max(
        0,
        int(access_count),
    )

    safe_requested_rows = max(
        0,
        int(requested_rows),
    )


    normalized_levels = {
        field_name:
            normalize_sensitivity_level(
                level
            )
        for (
            field_name,
            level
        ) in sensitive_field_levels.items()
    }


    level_values = list(
        normalized_levels.values()
    )


    sensitive_field_count = len(
        normalized_levels
    )


    max_sensitivity_level = (
        get_max_sensitivity_level(
            level_values
        )
    )


    l4_field_count = sum(
        1
        for level in level_values
        if level == "L4"
    )


    is_raw_access = (
        access_mode == "raw"
    )


    return {
        "access_count":
            safe_access_count,

        "requested_rows":
            safe_requested_rows,

        "sensitive_field_count":
            sensitive_field_count,

        "max_sensitivity_level":
            max_sensitivity_level,

        "max_sensitivity_score":
            SENSITIVITY_LEVEL_SCORES[
                max_sensitivity_level
            ],

        "l4_field_count":
            l4_field_count,

        "is_raw_access":
            is_raw_access,
    }



def build_access_risk_features(
    *,
    access_count: int,
    requested_rows: int,
    sensitive_field_levels: dict[str, str],
    access_mode: str,
    user_role: str | None = None,
) -> dict:
    """
    构建一次业务数据访问的完整风险特征。

    这一层作为 risk 模块对外统一入口。
    """

    base_features = (
        extract_risk_features(
            access_count=access_count,
            requested_rows=requested_rows,
            sensitive_field_levels=(
                sensitive_field_levels
            ),
            access_mode=access_mode,
        )
    )

    normalized_role = (
        str(user_role)
        .strip()
        .lower()
        if user_role
        else None
    )

    return {
        **base_features,

        "user_role":
            normalized_role,

        "is_admin":
            normalized_role == "admin",
    }