

from app.modules.risk.features import (
    extract_risk_features,
    get_max_sensitivity_level,
    normalize_sensitivity_level,
    build_access_risk_features,
)


def test_extract_raw_l4_risk_features():

    features = extract_risk_features(
        access_count=4,
        requested_rows=20,
        sensitive_field_levels={
            "name": "L3",
            "phone": "L3",
            "id_card": "L4",
        },
        access_mode="raw",
    )

    assert features == {
        "access_count": 4,
        "requested_rows": 20,
        "sensitive_field_count": 3,
        "max_sensitivity_level": "L4",
        "max_sensitivity_score": 4,
        "l4_field_count": 1,
        "is_raw_access": True,
    }


def test_masked_access_should_not_be_raw():

    features = extract_risk_features(
        access_count=2,
        requested_rows=10,
        sensitive_field_levels={
            "name": "L3",
            "phone": "L3",
        },
        access_mode="masked",
    )

    assert (
        features["is_raw_access"]
        is False
    )

    assert (
        features["max_sensitivity_level"]
        == "L3"
    )

    assert (
        features["max_sensitivity_score"]
        == 3
    )

    assert (
        features["l4_field_count"]
        == 0
    )


def test_negative_counts_should_be_clamped_to_zero():

    features = extract_risk_features(
        access_count=-5,
        requested_rows=-100,
        sensitive_field_levels={},
        access_mode="raw",
    )

    assert (
        features["access_count"]
        == 0
    )

    assert (
        features["requested_rows"]
        == 0
    )


def test_invalid_sensitivity_level_should_fallback_to_l1():

    assert (
        normalize_sensitivity_level(
            "UNKNOWN"
        )
        == "L1"
    )

    assert (
        normalize_sensitivity_level(
            None
        )
        == "L1"
    )

    assert (
        normalize_sensitivity_level(
            " l4 "
        )
        == "L4"
    )


def test_empty_sensitive_fields_should_use_l1():

    features = extract_risk_features(
        access_count=1,
        requested_rows=5,
        sensitive_field_levels={},
        access_mode="raw",
    )

    assert (
        features["sensitive_field_count"]
        == 0
    )

    assert (
        features["max_sensitivity_level"]
        == "L1"
    )

    assert (
        features["max_sensitivity_score"]
        == 1
    )

    assert (
        features["l4_field_count"]
        == 0
    )

    assert (
        get_max_sensitivity_level([])
        == "L1"
    )




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

    后续：
    data_access / access_monitoring
        ↓
    build_access_risk_features()
        ↓
    scoring.py
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


def test_build_access_risk_features_should_include_role():

    features = (
        build_access_risk_features(
            access_count=4,
            requested_rows=20,
            sensitive_field_levels={
                "name": "L3",
                "id_card": "L4",
            },
            access_mode="raw",
            user_role="admin",
        )
    )

    assert (
        features["user_role"]
        == "admin"
    )

    assert (
        features["is_admin"]
        is True
    )

    assert (
        features["is_raw_access"]
        is True
    )

    assert (
        features["max_sensitivity_level"]
        == "L4"
    )


def test_build_access_risk_features_should_normalize_role():

    features = (
        build_access_risk_features(
            access_count=1,
            requested_rows=5,
            sensitive_field_levels={
                "phone": "L3",
            },
            access_mode="masked",
            user_role=" ANALYST ",
        )
    )

    assert (
        features["user_role"]
        == "analyst"
    )

    assert (
        features["is_admin"]
        is False
    )

    assert (
        features["is_raw_access"]
        is False
    )