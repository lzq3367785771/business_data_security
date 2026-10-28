from app.modules.risk.scoring import (
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    calculate_risk_score,
    evaluate_access_risk,
)


def test_low_risk_should_return_low():

    result = calculate_risk_score(
        {
            "access_count": 1,
            "requested_rows": 5,
            "sensitive_field_count": 0,
            "max_sensitivity_score": 1,
            "l4_field_count": 0,
            "is_raw_access": False,
        }
    )

    assert (
        result["risk_score"]
        < 30
    )

    assert (
        result["risk_level"]
        == RISK_LOW
    )


def test_medium_risk_should_return_medium():

    result = calculate_risk_score(
        {
            "access_count": 5,
            "requested_rows": 20,
            "sensitive_field_count": 2,
            "max_sensitivity_score": 2,
            "l4_field_count": 0,
            "is_raw_access": False,
        }
    )

    assert (
        30
        <= result["risk_score"]
        < 60
    )

    assert (
        result["risk_level"]
        == RISK_MEDIUM
    )


def test_high_risk_should_return_high():

    result = calculate_risk_score(
        {
            "access_count": 4,
            "requested_rows": 20,
            "sensitive_field_count": 3,
            "max_sensitivity_score": 4,
            "l4_field_count": 1,
            "is_raw_access": True,
        }
    )

    assert (
        result["risk_score"]
        == 71
    )

    assert (
        result["risk_level"]
        == RISK_HIGH
    )

    assert (
        "访问对象包含 L4 高敏感字段"
        in result["reasons"]
    )

    assert (
        "当前访问为原始数据访问"
        in result["reasons"]
    )


def test_risk_score_should_not_exceed_100():

    result = calculate_risk_score(
        {
            "access_count": 100,
            "requested_rows": 1000,
            "sensitive_field_count": 20,
            "max_sensitivity_score": 4,
            "l4_field_count": 10,
            "is_raw_access": True,
        }
    )

    assert (
        result["risk_score"]
        == 100
    )

    assert (
        result["risk_level"]
        == RISK_HIGH
    )


def test_reasons_should_be_empty_for_safe_access():

    result = calculate_risk_score(
        {
            "access_count": 1,
            "requested_rows": 1,
            "sensitive_field_count": 0,
            "max_sensitivity_score": 1,
            "l4_field_count": 0,
            "is_raw_access": False,
        }
    )

    assert (
        result["reasons"]
        == []
    )



def test_evaluate_access_risk_should_return_complete_result():

    result = (
        evaluate_access_risk(
            access_count=4,
            requested_rows=20,
            sensitive_field_levels={
                "name": "L3",
                "phone": "L3",
                "id_card": "L4",
            },
            access_mode="raw",
            user_role="admin",
        )
    )

    assert (
        result["risk_score"]
        == 71
    )

    assert (
        result["risk_level"]
        == RISK_HIGH
    )

    assert (
        result["features"][
            "access_count"
        ]
        == 4
    )

    assert (
        result["features"][
            "max_sensitivity_level"
        ]
        == "L4"
    )

    assert (
        result["features"][
            "is_raw_access"
        ]
        is True
    )

    assert (
        result["features"][
            "user_role"
        ]
        == "admin"
    )

    assert (
        "访问对象包含 L4 高敏感字段"
        in result["reasons"]
    )


def test_evaluate_access_risk_safe_access_should_be_low():

    result = (
        evaluate_access_risk(
            access_count=1,
            requested_rows=5,
            sensitive_field_levels={},
            access_mode="masked",
            user_role="analyst",
        )
    )

    assert (
        result["risk_level"]
        == RISK_LOW
    )

    assert (
        result["risk_score"]
        < 30
    )

    assert (
        result["features"][
            "is_raw_access"
        ]
        is False
    )

    assert (
        result["features"][
            "is_admin"
        ]
        is False
    )