from dataclasses import dataclass


@dataclass(frozen=True)
class SensitiveRule:
    sensitive_type: str
    sensitive_label: str
    sensitivity_level: str
    confidence: float


FIELD_NAME_RULES: dict[str, SensitiveRule] = {

    # -------------------------
    # 身份证件
    # -------------------------
    "id_card": SensitiveRule(
        sensitive_type="id_card",
        sensitive_label="身份证号",
        sensitivity_level="L4",
        confidence=0.98,
    ),

    "idcard": SensitiveRule(
        sensitive_type="id_card",
        sensitive_label="身份证号",
        sensitivity_level="L4",
        confidence=0.98,
    ),

    "identity_card": SensitiveRule(
        sensitive_type="id_card",
        sensitive_label="身份证号",
        sensitivity_level="L4",
        confidence=0.98,
    ),

    # -------------------------
    # 手机号
    # -------------------------
    "phone": SensitiveRule(
        sensitive_type="phone",
        sensitive_label="手机号",
        sensitivity_level="L3",
        confidence=0.95,
    ),

    "mobile": SensitiveRule(
        sensitive_type="phone",
        sensitive_label="手机号",
        sensitivity_level="L3",
        confidence=0.95,
    ),

    "mobile_phone": SensitiveRule(
        sensitive_type="phone",
        sensitive_label="手机号",
        sensitivity_level="L3",
        confidence=0.95,
    ),

    # -------------------------
    # 姓名
    # -------------------------
    "name": SensitiveRule(
        sensitive_type="name",
        sensitive_label="姓名",
        sensitivity_level="L3",
        confidence=0.85,
    ),

    "real_name": SensitiveRule(
        sensitive_type="name",
        sensitive_label="姓名",
        sensitivity_level="L3",
        confidence=0.95,
    ),

    "full_name": SensitiveRule(
        sensitive_type="name",
        sensitive_label="姓名",
        sensitivity_level="L3",
        confidence=0.95,
    ),

    # -------------------------
    # Email
    # -------------------------
    "email": SensitiveRule(
        sensitive_type="email",
        sensitive_label="电子邮箱",
        sensitivity_level="L2",
        confidence=0.95,
    ),

    "email_address": SensitiveRule(
        sensitive_type="email",
        sensitive_label="电子邮箱",
        sensitivity_level="L2",
        confidence=0.95,
    ),

    # -------------------------
    # 地址
    # -------------------------
    "address": SensitiveRule(
        sensitive_type="address",
        sensitive_label="详细地址",
        sensitivity_level="L3",
        confidence=0.90,
    ),

    "home_address": SensitiveRule(
        sensitive_type="address",
        sensitive_label="详细地址",
        sensitivity_level="L3",
        confidence=0.95,
    ),

    "detail_address": SensitiveRule(
        sensitive_type="address",
        sensitive_label="详细地址",
        sensitivity_level="L3",
        confidence=0.95,
    ),
}


def normalize_field_name(
    field_name: str,
) -> str:
    """
    统一字段名称：
    - 去空格
    - 转小写
    - '-' 转 '_'
    """

    return (
        field_name
        .strip()
        .lower()
        .replace("-", "_")
    )


def detect_by_field_name(
    field_name: str,
) -> dict:
    """
    根据字段名称判断敏感类型。
    """

    normalized_name = normalize_field_name(
        field_name
    )

    rule = FIELD_NAME_RULES.get(
        normalized_name
    )

    if rule is None:
        return {
            "is_sensitive": False,
            "sensitive_type": None,
            "sensitive_label": None,
            "sensitivity_level": "L1",
            "detection_method": "rule",
            "confidence": 0.0,
            "detection_reason": (
                f"字段名规则未命中：{field_name}"
            ),
        }

    return {
        "is_sensitive": True,

        "sensitive_type":
            rule.sensitive_type,

        "sensitive_label":
            rule.sensitive_label,

        "sensitivity_level":
            rule.sensitivity_level,

        "detection_method":
            "rule",

        "confidence":
            rule.confidence,

        "detection_reason":
            f"字段名规则命中：{normalized_name}",
    }