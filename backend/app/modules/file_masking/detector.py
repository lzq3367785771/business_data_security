
import re

from app.modules.sensitive_detection.rules import (
    detect_by_field_name,
)

from app.modules.sensitive_detection.content_rules import (
    analyze_sample_values,
)

from app.modules.sensitive_detection.fusion import (
    fuse_detection,
)


# 中文表头映射到现有敏感字段类型
HEADER_ALIASES = {
    "姓名": "name",
    "客户姓名": "name",
    "员工姓名": "name",
    "联系人姓名": "name",
    "真实姓名": "real_name",

    "手机号": "phone",
    "手机号码": "mobile_phone",
    "联系电话": "phone",
    "联系电话号码": "phone",

    "身份证": "id_card",
    "身份证号": "id_card",
    "身份证号码": "id_card",
    "公民身份号码": "id_card",

    "邮箱": "email",
    "电子邮箱": "email",
    "联系邮箱": "email",

    "地址": "address",
    "详细地址": "detail_address",
    "家庭住址": "address",

    "薪资": "salary",
    "工资": "salary",
    "月薪": "salary",
}


def normalize_header(value) -> str:
    """标准化表头，便于匹配中英文别名。"""

    text = str(value or "").strip().lower()

    return re.sub(
        r"[\s_\-（）()【】\[\]：:·]+",
        "",
        text,
    )


def detect_column(
    column_name: str,
    sample_values: list,
) -> dict:
    """
    识别表格列的敏感类型。

    综合：
    1. 字段名称规则
    2. 单元格内容识别
    3. 融合识别

    不返回原始样本内容。
    """

    normalized = normalize_header(column_name)

    canonical_name = HEADER_ALIASES.get(
        normalized,
        column_name,
    )

    rule_result = detect_by_field_name(
        canonical_name
    )

    content_result = analyze_sample_values(
        sample_values
    )

    detection = fuse_detection(
        rule_result=rule_result,
        content_result=content_result,
    )

    # 内容识别单独命中时，提高自动推荐门槛，
    # 降低普通中文文本被误判为姓名的概率。
    if (
        not rule_result["is_sensitive"]
        and detection["is_sensitive"]
    ):
        sample_count = content_result["sample_count"]
        match_ratio = content_result["match_ratio"]

        if sample_count < 3 or match_ratio < 0.8:
            detection = {
                "is_sensitive": False,
                "sensitive_type": None,
                "sensitive_label": None,
                "sensitivity_level": "L1",
                "detection_method": "content",
                "confidence": 0.0,
                "detection_reason": "内容识别证据不足，建议人工确认",
                "conflict": False,
            }

    return {
        "column_name": str(column_name),
        "is_sensitive": detection["is_sensitive"],
        "sensitive_type": detection["sensitive_type"],
        "sensitive_label": detection["sensitive_label"],
        "sensitivity_level": detection["sensitivity_level"],
        "detection_method": detection["detection_method"],
        "confidence": detection["confidence"],
        "sample_count": content_result["sample_count"],
        "matched_count": content_result["matched_count"],
        "match_ratio": content_result["match_ratio"],
        "conflict": detection.get("conflict", False),
        "detection_reason": detection["detection_reason"],
    }
