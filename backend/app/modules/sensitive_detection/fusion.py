TYPE_META = {
    "phone": {
        "label": "手机号",
        "level": "L3",
    },

    "id_card": {
        "label": "身份证号",
        "level": "L4",
    },

    "email": {
        "label": "电子邮箱",
        "level": "L2",
    },

    "name": {
        "label": "姓名",
        "level": "L3",
    },

    "address": {
        "label": "详细地址",
        "level": "L3",
    },
}


def fuse_detection(
    rule_result: dict,
    content_result: dict,
) -> dict:
    """
    融合字段名规则与内容抽样结果。

    情况：
    1. 两者一致 -> hybrid
    2. 字段名未识别、内容识别 -> content
    3. 内容未识别 -> 保留 rule
    4. 两者冲突 -> 保留规则类型，但降低置信度并等待复核
    """

    content_type = content_result.get(
        "detected_type"
    )

    content_confidence = float(
        content_result.get(
            "confidence",
            0.0,
        )
    )

    sample_count = content_result.get(
        "sample_count",
        0,
    )

    matched_count = content_result.get(
        "matched_count",
        0,
    )

    match_ratio = content_result.get(
        "match_ratio",
        0.0,
    )

    # -------------------------
    # 1. 内容没有识别出来
    # -------------------------

    if not content_type:
        result = dict(rule_result)

        result["content_sample_count"] = (
            sample_count
        )

        result["content_matched_count"] = (
            matched_count
        )

        result["content_match_ratio"] = (
            match_ratio
        )

        result["conflict"] = False

        return result

    # -------------------------
    # 2. 字段名没有识别，
    #    但内容识别出来
    # -------------------------

    if not rule_result["is_sensitive"]:

        meta = TYPE_META[
            content_type
        ]

        return {
            "is_sensitive": True,

            "sensitive_type":
                content_type,

            "sensitive_label":
                meta["label"],

            "sensitivity_level":
                meta["level"],

            "detection_method":
                "content",

            "confidence":
                content_confidence,

            "detection_reason": (
                "字段名规则未命中；"
                f"内容抽样识别为{meta['label']}，"
                f"命中{matched_count}/{sample_count}"
            ),

            "content_sample_count":
                sample_count,

            "content_matched_count":
                matched_count,

            "content_match_ratio":
                match_ratio,

            "conflict":
                False,
        }

    # -------------------------
    # 3. 两种方法识别一致
    # -------------------------

    if (
        rule_result["sensitive_type"]
        == content_type
    ):

        rule_confidence = float(
            rule_result["confidence"]
        )

        # 内容证据权重稍高
        confidence = (
            rule_confidence * 0.4
            + content_confidence * 0.6
        )

        confidence = round(
            min(confidence, 0.99),
            4,
        )

        return {
            "is_sensitive": True,

            "sensitive_type":
                content_type,

            "sensitive_label":
                rule_result[
                    "sensitive_label"
                ],

            "sensitivity_level":
                rule_result[
                    "sensitivity_level"
                ],

            "detection_method":
                "hybrid",

            "confidence":
                confidence,

            "detection_reason": (
                f"字段名规则识别为"
                f"{rule_result['sensitive_label']}；"
                f"内容抽样一致，"
                f"命中{matched_count}/{sample_count}"
            ),

            "content_sample_count":
                sample_count,

            "content_matched_count":
                matched_count,

            "content_match_ratio":
                match_ratio,

            "conflict":
                False,
        }

    # -------------------------
    # 4. 两种结果冲突
    # -------------------------

    return {
        "is_sensitive": True,

        "sensitive_type":
            rule_result[
                "sensitive_type"
            ],

        "sensitive_label":
            rule_result[
                "sensitive_label"
            ],

        "sensitivity_level":
            rule_result[
                "sensitivity_level"
            ],

        "detection_method":
            "hybrid",

        "confidence":
            round(
                min(
                    float(
                        rule_result[
                            "confidence"
                        ]
                    ),
                    content_confidence,
                )
                * 0.7,
                4,
            ),

        "detection_reason": (
            "识别结果存在冲突："
            f"字段名判断为"
            f"{rule_result['sensitive_type']}，"
            f"内容判断为{content_type}，"
            "需要人工复核"
        ),

        "content_sample_count":
            sample_count,

        "content_matched_count":
            matched_count,

        "content_match_ratio":
            match_ratio,

        "conflict":
            True,
    }