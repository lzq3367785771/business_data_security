from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.data_access import router as data_router
from app.modules.data_access import service as data_service

def make_common_objects():

    request = SimpleNamespace(
        state=SimpleNamespace(
            request_id="test-request-id",
        )
    )

    user = SimpleNamespace(
        id=1,
        role="admin",
    )

    source = SimpleNamespace(
        id=1,
        system_id=2,
        status="active",
        source_type="mysql",
        host="127.0.0.1",
        port=3306,
        database_name="crm_db",
        secret_ref="CRM_MYSQL_CREDENTIAL",
        username=None,
        source_code="CRM_MYSQL",
        source_name="CRM MySQL",
    )

    system = SimpleNamespace(
        system_code="CRM",
    )

    database = SimpleNamespace(
        database_name="crm_db",
    )

    table = SimpleNamespace(
        id=100,
        table_name="customer",
    )

    columns = [
        SimpleNamespace(
            id=1,
            column_name="id",
            data_type="int",
        ),
        SimpleNamespace(
            id=2,
            column_name="name",
            data_type="varchar",
        ),
        SimpleNamespace(
            id=3,
            column_name="phone",
            data_type="varchar",
        ),
    ]

    credential = SimpleNamespace(
        status="active",
        username="bdas_scanner",
    )

    return {
        "request": request,
        "user": user,
        "source": source,
        "system": system,
        "database": database,
        "table": table,
        "columns": columns,
        "credential": credential,
    }


def patch_common(
    monkeypatch,
    objects,
    audit_calls,
):

    monkeypatch.setattr(
        data_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=1,
            ),
    )

    monkeypatch.setattr(
        data_router,
        "get_source_by_id",
        lambda *args, **kwargs:
            objects["source"],
    )

    monkeypatch.setattr(
        data_router,
        "get_system_by_id",
        lambda *args, **kwargs:
            objects["system"],
    )

    monkeypatch.setattr(
        data_router,
        "prepare_data_access_asset",
        lambda *args, **kwargs: {
            "database":
                objects["database"],

            "table":
                objects["table"],

            "columns":
                objects["columns"],
        },
    )

    monkeypatch.setattr(
        data_router,
        "prepare_data_access_credential",
        lambda *args, **kwargs: {
            "credential":
                objects["credential"],

            "username":
                (
                    objects["credential"].username
                    or objects["source"].username
                ),
        },
    )

    monkeypatch.setattr(
        data_router,
        "write_audit",
        lambda **kwargs:
            audit_calls.append(
                kwargs
            ),
    )

    monkeypatch.setattr(
        data_router,
        "get_confirmed_sensitive_field_types",
        lambda **kwargs: {
            "name": "name",
            "phone": "phone",
        },
    )

    monkeypatch.setattr(
        data_router,
        "get_confirmed_sensitive_field_levels",
        lambda **kwargs: {
            "name": "L3",
            "phone": "L3",
        },
    )

    # 测试时不构造真正 JSONResponse，
    # 直接把接口 data 返回出来。
    monkeypatch.setattr(
        data_router,
        "success",
        lambda request,
               data,
               message="success":
            data,
    )


# =========================
# LIMIT
# 必须真正只查询 5 行
# =========================

def test_limit_should_query_only_five_rows(
    monkeypatch,
):

    objects = make_common_objects()

    audit_calls = []

    patch_common(
        monkeypatch,
        objects,
        audit_calls,
    )


    monkeypatch.setattr(
        data_router,
        "decide_data_access_control",
        lambda **kwargs: {
            "action": "LIMIT",
            "risk_control_applied": True,
            "reason":
                "ACTIVE_HIGH_RISK_ANOMALY",
            "active_anomaly_id":
                "test-open-anomaly",
            "max_rows": 5,
            "mask_required": True,
        },
    )


    monkeypatch.setattr(
        data_router,
        "resolve_credential_secret",
        lambda credential:
            "fake-password",
    )


    query_info = {}


    def fake_read_mysql_table(
        **kwargs,
    ):

        query_info.update(
            kwargs
        )

        return [
            {
                "id": index,
                "name": f"user-{index}",
                "phone": "13800000000",
            }
            for index in range(
                1,
                6,
            )
        ]


    monkeypatch.setattr(
        data_router,
        "read_mysql_table",
        fake_read_mysql_table,
    )


    def fake_mask_rows(
        *,
        rows,
        field_types,
    ):

        return [
            {
                **row,
                "name": "***",
                "phone": "138****0000",
            }
            for row in rows
        ]


    monkeypatch.setattr(
        data_service,
        "mask_rows",
        fake_mask_rows,
    )

    result = (
        data_router.preview_business_table(
            source_id=1,
            table_name="customer",
            request=objects["request"],
            limit=20,
            db=object(),
            user=objects["user"],
        )
    )


    # 最重要：
    # MySQL SELECT 本身必须只读取 5 行。
    assert (
        query_info["limit"]
        == 5
    )


    assert (
        result["risk_action"]
        == "LIMIT"
    )

    assert (
        result["risk_control_applied"]
        is True
    )

    assert (
        result["effective_limit"]
        == 5
    )

    assert (
        result["limit_applied"]
        is True
    )

    assert (
        result["access_mode"]
        == "limited_masked"
    )

    assert (
        result["total_returned"]
        == 5
    )


    assert (
        result["items"][0]["name"]
        == "***"
    )


    # 审计也必须记录真实限制结果。
    audit = audit_calls[-1]

    assert (
        audit["result"]
        == "ALLOW"
    )

    assert (
        audit["details"]["risk_action"]
        == "LIMIT"
    )

    assert (
        audit["details"]["requested_limit"]
        == 20
    )

    assert (
        audit["details"]["effective_limit"]
        == 5
    )

    assert (
        audit["details"]["returned_rows"]
        == 5
    )


# =========================
# BLOCK
# 必须在解密密码和访问 MySQL 前终止
# =========================

def test_block_should_stop_before_database_access(
    monkeypatch,
):

    objects = make_common_objects()

    audit_calls = []

    patch_common(
        monkeypatch,
        objects,
        audit_calls,
    )


    monkeypatch.setattr(
        data_router,
        "decide_data_access_control",
        lambda **kwargs: {
            "action": "BLOCK",
            "risk_control_applied": True,
            "reason":
                "CONFIRMED_HIGH_RISK_ANOMALY",
            "active_anomaly_id":
                "test-confirmed-anomaly",
            "max_rows": 0,
            "mask_required": False,
        },
    )


    def should_not_decrypt(
        *args,
        **kwargs,
    ):

        raise AssertionError(
            "BLOCK 后不应解密数据库密码"
        )


    def should_not_read_mysql(
        *args,
        **kwargs,
    ):

        raise AssertionError(
            "BLOCK 后不应访问 MySQL"
        )


    monkeypatch.setattr(
        data_router,
        "resolve_credential_secret",
        should_not_decrypt,
    )

    monkeypatch.setattr(
        data_router,
        "read_mysql_table",
        should_not_read_mysql,
    )


    with pytest.raises(
        HTTPException
    ) as exc_info:

        data_router.preview_business_table(
            source_id=1,
            table_name="customer",
            request=objects["request"],
            limit=20,
            db=object(),
            user=objects["user"],
        )


    error = exc_info.value


    assert (
        error.status_code
        == 403
    )

    assert (
        error.detail["risk_action"]
        == "BLOCK"
    )

    assert (
        error.detail[
            "risk_control_reason"
        ]
        ==
        "CONFIRMED_HIGH_RISK_ANOMALY"
    )

    assert (
        error.detail[
            "active_anomaly_id"
        ]
        ==
        "test-confirmed-anomaly"
    )


    # BLOCK 必须留下 DENY 审计。
    assert len(
        audit_calls
    ) == 1

    audit = audit_calls[0]

    assert (
        audit["result"]
        == "DENY"
    )

    assert (
        audit["object_count"]
        == 0
    )

    assert (
        audit["details"]["access_mode"]
        == "blocked"
    )

    assert (
        audit["details"]["risk_action"]
        == "BLOCK"
    )

    assert (
        audit["details"]["effective_limit"]
        == 0
    )

    assert (
        audit["details"]["returned_rows"]
        == 0
    )


def test_allow_should_return_raw_data(
    monkeypatch,
):

    objects = make_common_objects()

    audit_calls = []

    patch_common(
        monkeypatch,
        objects,
        audit_calls,
    )


    # =========================
    # Risk Control -> ALLOW
    # =========================

    monkeypatch.setattr(
        data_router,
        "decide_data_access_control",
        lambda **kwargs: {
            "action":
                "ALLOW",

            "risk_control_applied":
                False,

            "reason":
                "NORMAL_ACCESS",

            "active_anomaly_id":
                None,

            "max_rows":
                None,

            "mask_required":
                False,
        },
    )


    # =========================
    # 临时解密凭据
    # =========================

    monkeypatch.setattr(
        data_router,
        "resolve_credential_secret",
        lambda credential:
            "fake-password",
    )


    # =========================
    # 模拟真实 MySQL 数据
    # =========================

    raw_rows = [
        {
            "id": 1,
            "name": "Alice",
            "phone": "13800000001",
        },
        {
            "id": 2,
            "name": "Bob",
            "phone": "13800000002",
        },
    ]


    query_info = {}


    def fake_read_mysql_table(
        **kwargs,
    ):

        query_info.update(
            kwargs
        )

        return raw_rows


    monkeypatch.setattr(
        data_router,
        "read_mysql_table",
        fake_read_mysql_table,
    )


    # =========================
    # ALLOW 不能调用脱敏
    # =========================

    def should_not_mask(
        **kwargs,
    ):

        raise AssertionError(
            "ALLOW 模式不应该执行数据脱敏"
        )


    monkeypatch.setattr(
        data_service,
        "mask_rows",
        should_not_mask,
    )


    # =========================
    # 简化 success()
    # 直接拿到业务返回数据
    # =========================

    monkeypatch.setattr(
        data_router,
        "success",
        lambda request, data, message=None:
            data,
    )


    # =========================
    # 执行接口
    # =========================

    result = (
        data_router.preview_business_table(
            source_id=objects["source"].id,
            table_name=(
                objects["table"].table_name
            ),
            request=objects["request"],
            limit=20,
            db=SimpleNamespace(),
            user=objects["user"],
        )
    )


    # =========================
    # 1. MySQL 应按请求值读取
    # =========================

    assert (
        query_info["limit"]
        == 20
    )


    # =========================
    # 2. ALLOW 返回原始数据
    # =========================

    assert (
        result["risk_action"]
        == "ALLOW"
    )

    assert (
        result["access_mode"]
        == "raw"
    )

    assert (
        result["risk_control_applied"]
        is False
    )

    assert (
        result["risk_control_reason"]
        == "NORMAL_ACCESS"
    )

    assert (
        result["active_anomaly_id"]
        is None
    )


    # =========================
    # 3. 不允许出现脱敏字段
    # =========================

    assert (
        result["masked_fields"]
        == []
    )


    # =========================
    # 4. 数据保持原值
    # =========================

    assert (
        result["items"]
        == raw_rows
    )

    assert (
        result["items"][0]["name"]
        == "Alice"
    )

    assert (
        result["items"][0]["phone"]
        == "13800000001"
    )


    # =========================
    # 5. LIMIT 未生效
    # =========================

    assert (
        result["requested_limit"]
        == 20
    )

    assert (
        result["effective_limit"]
        == 20
    )

    assert (
        result["limit_applied"]
        is False
    )


    # =========================
    # 6. 审计必须记录 ALLOW
    # =========================

    assert audit_calls

    audit = audit_calls[-1]

    assert (
        audit["result"]
        == "ALLOW"
    )

    assert (
        audit["object_count"]
        == 2
    )

    assert (
        audit["details"]["risk_action"]
        == "ALLOW"
    )

    assert (
        audit["details"]["access_mode"]
        == "raw"
    )

    assert (
        audit["details"]["risk_control_applied"]
        is False
    )



def test_mask_should_return_masked_data(
    monkeypatch,
):

    objects = make_common_objects()

    audit_calls = []

    patch_common(
        monkeypatch,
        objects,
        audit_calls,
    )


    # =========================
    # Risk Control -> MASK
    # =========================

    monkeypatch.setattr(
        data_router,
        "decide_data_access_control",
        lambda **kwargs: {
            "action":
                "MASK",

            "risk_control_applied":
                False,

            "reason":
                "ROLE_BASED_MASKING",

            "active_anomaly_id":
                None,

            "max_rows":
                None,

            "mask_required":
                True,
        },
    )


    # =========================
    # 临时解密凭据
    # =========================

    monkeypatch.setattr(
        data_router,
        "resolve_credential_secret",
        lambda credential:
            "fake-password",
    )


    # =========================
    # 固定敏感字段
    # =========================

    monkeypatch.setattr(
        data_router,
        "get_confirmed_sensitive_field_types",
        lambda **kwargs: {
            "name": "NAME",
            "phone": "PHONE",
        },
    )

    monkeypatch.setattr(
        data_router,
        "get_confirmed_sensitive_field_levels",
        lambda **kwargs: {
            "name": "L3",
            "phone": "L3",
        },
    )


    # =========================
    # 模拟 MySQL 原始数据
    # =========================

    raw_rows = [
        {
            "id": 1,
            "name": "Alice",
            "phone": "13800000001",
        },
        {
            "id": 2,
            "name": "Bob",
            "phone": "13800000002",
        },
    ]


    query_info = {}


    def fake_read_mysql_table(
        **kwargs,
    ):

        query_info.update(
            kwargs
        )

        return raw_rows


    monkeypatch.setattr(
        data_router,
        "read_mysql_table",
        fake_read_mysql_table,
    )


    # =========================
    # 模拟脱敏
    # =========================

    mask_calls = []


    def fake_mask_rows(
        *,
        rows,
        field_types,
    ):

        mask_calls.append(
            {
                "rows":
                    rows,

                "field_types":
                    field_types,
            }
        )

        return [
            {
                **row,
                "name": "***",
                "phone": "138****0000",
            }
            for row in rows
        ]


    monkeypatch.setattr(
        data_service,
        "mask_rows",
        fake_mask_rows,
    )


    # =========================
    # 简化 success()
    # =========================

    monkeypatch.setattr(
        data_router,
        "success",
        lambda request, data, message=None:
            data,
    )


    # =========================
    # 执行接口
    # =========================

    result = (
        data_router.preview_business_table(
            source_id=objects["source"].id,
            table_name=(
                objects["table"].table_name
            ),
            request=objects["request"],
            limit=20,
            db=SimpleNamespace(),
            user=objects["user"],
        )
    )


    # =========================
    # 1. MASK 不应限制读取行数
    # =========================

    assert (
        query_info["limit"]
        == 20
    )

    assert (
        result["requested_limit"]
        == 20
    )

    assert (
        result["effective_limit"]
        == 20
    )

    assert (
        result["limit_applied"]
        is False
    )


    # =========================
    # 2. 风险动作正确
    # =========================

    assert (
        result["risk_action"]
        == "MASK"
    )

    assert (
        result["risk_control_applied"]
        is False
    )

    assert (
        result["risk_control_reason"]
        == "ROLE_BASED_MASKING"
    )

    assert (
        result["active_anomaly_id"]
        is None
    )


    # =========================
    # 3. 必须执行脱敏
    # =========================

    assert len(mask_calls) == 1

    assert (
        mask_calls[0]["field_types"]
        == {
            "name": "NAME",
            "phone": "PHONE",
        }
    )


    # =========================
    # 4. 返回模式必须 masked
    # =========================

    assert (
        result["access_mode"]
        == "masked"
    )

    assert (
        result["masked_fields"]
        == [
            "name",
            "phone",
        ]
    )


    # =========================
    # 5. 返回数据必须已经脱敏
    # =========================

    assert (
        result["items"][0]["name"]
        == "***"
    )

    assert (
        result["items"][0]["phone"]
        == "138****0000"
    )

    assert (
        result["items"][1]["name"]
        == "***"
    )


    # =========================
    # 6. 审计仍然是 ALLOW
    # =========================

    assert audit_calls

    audit = audit_calls[-1]

    assert (
        audit["result"]
        == "ALLOW"
    )

    assert (
        audit["object_count"]
        == 2
    )

    assert (
        audit["details"]["risk_action"]
        == "MASK"
    )

    assert (
        audit["details"]["access_mode"]
        == "masked"
    )

    assert (
        audit["details"]["risk_control_reason"]
        == "ROLE_BASED_MASKING"
    )

    assert (
        audit["details"]["masked_fields"]
        == [
            "name",
            "phone",
        ]
    )