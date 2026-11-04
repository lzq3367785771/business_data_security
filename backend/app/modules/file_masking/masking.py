
from app.modules.masking.service import mask_value


SUPPORTED_SENSITIVE_TYPES = {
    "name",
    "phone",
    "id_card",
    "email",
    "address",
    "salary",
}


def mask_cell_value(
    value,
    sensitive_type: str,
):
    """
    对单元格内容执行脱敏。

    规则：
    1. 只允许已支持的敏感类型。
    2. 空值保持不变。
    3. 不修改公式字符串。
    4. 复用现有 mask_value。
    """

    if sensitive_type not in SUPPORTED_SENSITIVE_TYPES:
        raise ValueError(
            f"不支持的敏感类型：{sensitive_type}"
        )

    if value is None:
        return None

    # CSV 中可能存在公式字符串，第一版不处理。
    if isinstance(value, str):
        if value.lstrip().startswith("="):
            return value

    return mask_value(
        value,
        sensitive_type,
    )
