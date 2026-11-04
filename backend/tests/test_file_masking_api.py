import asyncio
import io

from types import SimpleNamespace

import pytest

from fastapi import (
    HTTPException,
    UploadFile,
)

from starlette.datastructures import Headers

import app.modules.file_masking.router as file_masking_router
from fastapi.responses import Response

def make_upload_file(
    *,
    filename: str,
    data: bytes,
    content_type: str,
) -> UploadFile:

    return UploadFile(
        filename=filename,
        file=io.BytesIO(data),
        headers=Headers({
            "content-type": content_type,
        }),
    )


def make_request():
    return SimpleNamespace(
        state=SimpleNamespace(
            request_id="test-request-id"
        )
    )


def make_user():
    return SimpleNamespace(
        id=1,
        username="admin",
        role="admin",
    )


def test_preview_csv_should_detect_sensitive_fields(
    monkeypatch,
):
    policy_calls = []
    audit_calls = []

    def fake_require_policy(**kwargs):
        policy_calls.append(kwargs)

        return SimpleNamespace(
            policy_id=201
        )

    def fake_write_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        file_masking_router,
        "require_policy",
        fake_require_policy,
    )

    monkeypatch.setattr(
        file_masking_router,
        "write_audit",
        fake_write_audit,
    )

    content = (
        "客户姓名,联系电话,邮箱\n"
        "张三,13812345678,abc@qq.com\n"
        "李四,13912345678,def@qq.com\n"
    ).encode("utf-8")

    upload = make_upload_file(
        filename="customers.csv",
        data=content,
        content_type="text/csv",
    )

    response = asyncio.run(
        file_masking_router.preview_file_masking(
            request=make_request(),
            file=upload,
            db=SimpleNamespace(),
            user=make_user(),
        )
    )

    assert response["code"] == 0

    assert (
        response["message"]
        == "文件敏感字段识别完成"
    )

    data = response["data"]

    assert data["file_type"] == "csv"

    assert (
        data["total_sensitive_columns"]
        >= 2
    )

    # =========================
    # 不允许泄露原始敏感值
    # =========================

    serialized = str(response)

    assert "13812345678" not in serialized
    assert "13912345678" not in serialized
    assert "abc@qq.com" not in serialized
    assert "张三" not in serialized

    # =========================
    # 权限调用
    # =========================

    assert (
        policy_calls[0]["resource"]
        == "file_masking:preview"
    )

    assert (
        policy_calls[0]["action"]
        == "FILE_MASK_PREVIEW"
    )

    # =========================
    # 审计
    # =========================

    assert audit_calls

    audit = audit_calls[-1]

    assert (
        audit["action"]
        == "FILE_MASK_PREVIEW"
    )

    assert (
        audit["result"]
        == "ALLOW"
    )

    assert (
        "13812345678"
        not in str(audit["details"])
    )


def test_invalid_file_should_be_rejected_and_audited(
    monkeypatch,
):
    audit_calls = []

    monkeypatch.setattr(
        file_masking_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=201
            ),
    )

    monkeypatch.setattr(
        file_masking_router,
        "write_audit",
        lambda **kwargs:
            audit_calls.append(kwargs),
    )

    upload = make_upload_file(
        filename="customers.txt",
        data=b"hello",
        content_type="text/plain",
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        asyncio.run(
            file_masking_router.preview_file_masking(
                request=make_request(),
                file=upload,
                db=SimpleNamespace(),
                user=make_user(),
            )
        )

    assert (
        exc_info.value.status_code
        == 400
    )

    assert audit_calls

    assert (
        audit_calls[-1]["result"]
        == "DENY"
    )

    assert (
        audit_calls[-1]["action"]
        == "FILE_MASK_PREVIEW"
    )


def test_preview_should_stop_when_policy_denied(
    monkeypatch,
):
    def fake_require_policy(**kwargs):
        raise HTTPException(
            status_code=403,
            detail="没有执行该操作的权限",
        )

    monkeypatch.setattr(
        file_masking_router,
        "require_policy",
        fake_require_policy,
    )

    upload = make_upload_file(
        filename="customers.csv",
        data=(
            b"name,phone\n"
            b"test,13812345678\n"
        ),
        content_type="text/csv",
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:

        asyncio.run(
            file_masking_router.preview_file_masking(
                request=make_request(),
                file=upload,
                db=SimpleNamespace(),
                user=SimpleNamespace(
                    id=2,
                    username="analyst",
                    role="analyst",
                ),
            )
        )

    assert (
        exc_info.value.status_code
        == 403
    )





def test_mask_csv_download_and_audit(monkeypatch):
    audit_calls = []

    monkeypatch.setattr(
        file_masking_router,
        "require_policy",
        lambda **kwargs: SimpleNamespace(policy_id=202),
    )

    monkeypatch.setattr(
        file_masking_router,
        "write_audit",
        lambda **kwargs: audit_calls.append(kwargs),
    )

    content = (
        "姓名,手机号\n"
        "张三,13812345678\n"
    ).encode("utf-8")

    upload = make_upload_file(
        filename="customers.csv",
        data=content,
        content_type="text/csv",
    )

    response = asyncio.run(
        file_masking_router.mask_file_download(
            request=make_request(),
            file=upload,
            selections=(
                '[{"sheet_name":"CSV",'
                '"column_index":2,'
                '"sensitive_type":"phone"}]'
            ),
            db=SimpleNamespace(),
            user=make_user(),
        )
    )

    assert isinstance(response, Response)
    assert response.status_code == 200

    assert (
        "customers_masked.csv"
        in response.headers["content-disposition"]
    )

    assert b"138****5678" in response.body
    assert b"13812345678" not in response.body

    audit = audit_calls[-1]

    assert audit["resource"] == "file_masking:mask"
    assert audit["action"] == "FILE_MASK_EXECUTE"
    assert audit["result"] == "ALLOW"

    assert "13812345678" not in str(audit["details"])


def test_mask_invalid_selection(monkeypatch):
    audit_calls = []

    monkeypatch.setattr(
        file_masking_router,
        "require_policy",
        lambda **kwargs: SimpleNamespace(policy_id=202),
    )

    monkeypatch.setattr(
        file_masking_router,
        "write_audit",
        lambda **kwargs: audit_calls.append(kwargs),
    )

    upload = make_upload_file(
        filename="customers.csv",
        data=b"name,phone\nAlice,13812345678\n",
        content_type="text/csv",
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            file_masking_router.mask_file_download(
                request=make_request(),
                file=upload,
                selections="not-json",
                db=SimpleNamespace(),
                user=make_user(),
            )
        )

    assert exc_info.value.status_code == 400
    assert audit_calls[-1]["result"] == "DENY"


def test_mask_permission_denied(monkeypatch):
    def fake_require_policy(**kwargs):
        raise HTTPException(
            status_code=403,
            detail="没有执行该操作的权限",
        )

    monkeypatch.setattr(
        file_masking_router,
        "require_policy",
        fake_require_policy,
    )

    upload = make_upload_file(
        filename="customers.csv",
        data=b"name,phone\nAlice,13812345678\n",
        content_type="text/csv",
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            file_masking_router.mask_file_download(
                request=make_request(),
                file=upload,
                selections=(
                    '[{"sheet_name":"CSV",'
                    '"column_index":2,'
                    '"sensitive_type":"phone"}]'
                ),
                db=SimpleNamespace(),
                user=SimpleNamespace(
                    id=2,
                    username="analyst",
                    role="analyst",
                ),
            )
        )

    assert exc_info.value.status_code == 403
