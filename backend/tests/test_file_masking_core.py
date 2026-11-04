
from app.modules.file_masking.detector import detect_column
from app.modules.file_masking.masking import mask_cell_value


def test_detect_chinese_phone_header():
    result = detect_column(
        "联系电话",
        ["13812345678", "13912345678", "15012345678"],
    )

    assert result["is_sensitive"] is True
    assert result["sensitive_type"] == "phone"
    assert result["sensitivity_level"] == "L3"


def test_detect_phone_by_content():
    result = detect_column(
        "其他字段",
        ["13812345678", "13912345678", "15012345678"],
    )

    assert result["is_sensitive"] is True
    assert result["sensitive_type"] == "phone"


def test_mask_phone():
    result = mask_cell_value(
        "13812345678",
        "phone",
    )

    assert result == "138****5678"


def test_mask_name():
    result = mask_cell_value(
        "张三",
        "name",
    )

    assert result == "张*"


def test_mask_email():
    result = mask_cell_value(
        "abc123@qq.com",
        "email",
    )

    assert result == "a***@qq.com"


def test_mask_id_card():
    result = mask_cell_value(
        "110101199001011234",
        "id_card",
    )

    assert result == "110***********1234"


def test_empty_value():
    assert mask_cell_value(None, "phone") is None


def test_unsupported_type():
    try:
        mask_cell_value("test", "unknown")
    except ValueError:
        return

    assert False, "应该拒绝不支持的敏感类型"


def test_formula_string_unchanged():
    result = mask_cell_value(
        "=SUM(A1:A2)",
        "phone",
    )

    assert result == "=SUM(A1:A2)"
