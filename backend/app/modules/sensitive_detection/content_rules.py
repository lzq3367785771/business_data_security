import re
from collections import Counter


PHONE_PATTERN = re.compile(
    r"^1[3-9]\d{9}$"
)

# 支持：
# 15位旧身份证
# 18位身份证
ID_CARD_PATTERN = re.compile(
    r"^(?:\d{15}|\d{17}[\dXx])$"
)

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

# 中文姓名第一版规则
CHINESE_NAME_PATTERN = re.compile(
    r"^[\u4e00-\u9fff·]{2,6}$"
)


# 行政区域值，避免把“北京市”“四川省”等误判成人名
ADMIN_REGION_SUFFIXES = (
    "省",
    "市",
    "区",
    "县",
    "自治区",
    "特别行政区",
)


# 地址中常见结构词
ADDRESS_KEYWORDS = (
    "省",
    "自治区",
    "市",
    "区",
    "县",
    "镇",
    "乡",
    "街道",
    "街",
    "路",
    "大道",
    "巷",
    "村",
    "社区",
    "小区",
    "号",
    "栋",
    "单元",
    "室",
)


def normalize_value(value) -> str:
    if value is None:
        return ""

    return str(value).strip()


def normalize_compact(
    value,
) -> str:
    """
    用于手机号、身份证等格式识别。

    删除空格和 '-'，避免：

    110101-19900101-001X

    这类格式因为分隔符识别失败。
    """

    text = normalize_value(value)

    return re.sub(
        r"[\s-]+",
        "",
        text,
    )


def looks_like_chinese_name(
    value,
) -> bool:
    """
    中文姓名启发式判断。

    第一版：
    - 2~6 个中文字符
    - 可以含 ·
    - 排除明显行政区名称
    """

    text = normalize_value(value)

    if not CHINESE_NAME_PATTERN.fullmatch(
        text
    ):
        return False

    if text.endswith(
        ADMIN_REGION_SUFFIXES
    ):
        return False

    return True


def looks_like_address(
    value,
) -> bool:
    """
    中文详细地址启发式判断。

    为降低 city / province 等字段误报：

    - 长度至少 6
    - 至少命中两个地址结构词
    """

    text = normalize_value(value)

    if len(text) < 6:
        return False

    keyword_count = sum(
        1
        for keyword in ADDRESS_KEYWORDS
        if keyword in text
    )

    return keyword_count >= 2


def detect_value_type(
    value,
) -> str | None:
    """
    判断单个样本值的敏感类型。

    当前支持：
    - phone
    - id_card
    - email
    - address
    - name

    注意：
    只返回类型，不返回原始值。
    """

    text = normalize_value(value)

    if not text:
        return None

    compact_text = normalize_compact(
        value
    )

    # 手机号
    if PHONE_PATTERN.fullmatch(
        compact_text
    ):
        return "phone"

    # 身份证
    if ID_CARD_PATTERN.fullmatch(
        compact_text
    ):
        return "id_card"

    # 邮箱
    if EMAIL_PATTERN.fullmatch(
        text
    ):
        return "email"

    # 地址必须先于姓名判断
    if looks_like_address(
        text
    ):
        return "address"

    # 中文姓名
    if looks_like_chinese_name(
        text
    ):
        return "name"

    return None


def analyze_sample_values(
    values: list,
) -> dict:
    """
    分析一批样本。

    只输出统计结果，
    永远不输出真实业务数据。
    """

    valid_values = [
        value
        for value in values
        if normalize_value(value)
    ]

    if not valid_values:
        return {
            "sample_count": 0,
            "matched_count": 0,
            "detected_type": None,
            "match_ratio": 0.0,
            "confidence": 0.0,
        }

    detected_types = []

    for value in valid_values:

        detected_type = (
            detect_value_type(
                value
            )
        )

        if detected_type:
            detected_types.append(
                detected_type
            )

    if not detected_types:
        return {
            "sample_count":
                len(valid_values),

            "matched_count": 0,

            "detected_type": None,

            "match_ratio": 0.0,

            "confidence": 0.0,
        }

    counter = Counter(
        detected_types
    )

    detected_type, matched_count = (
        counter.most_common(1)[0]
    )

    match_ratio = (
        matched_count
        / len(valid_values)
    )

    return {
        "sample_count":
            len(valid_values),

        "matched_count":
            matched_count,

        "detected_type":
            detected_type,

        "match_ratio":
            round(
                match_ratio,
                4,
            ),

        "confidence":
            round(
                match_ratio,
                4,
            ),
    }