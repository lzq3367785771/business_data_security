import asyncio
import io

from types import SimpleNamespace

import pytest

from fastapi import (
    HTTPException,
    UploadFile,
)

from starlette.datastructures import (
    Headers,
)

import app.modules.file_security.router as file_security_router

def make_upload_file(
    *,
    filename: str,
    data: bytes,
    content_type: str,
) -> UploadFile:

    return UploadFile(
        filename=filename,
        file=io.BytesIO(
            data
        ),
        headers=Headers(
            {
                "content-type":
                    content_type,
            }
        ),
    )


def test_file_security_api_should_encrypt_and_decrypt(
    monkeypatch,
):

    policy_calls = []
    audit_calls = []


    def fake_require_policy(
        **kwargs,
    ):

        policy_calls.append(
            kwargs
        )

        return SimpleNamespace(
            policy_id=101
        )


    def fake_write_audit(
        **kwargs,
    ):

        audit_calls.append(
            kwargs
        )


    monkeypatch.setattr(
        file_security_router,
        "require_policy",
        fake_require_policy,
    )

    monkeypatch.setattr(
        file_security_router,
        "write_audit",
        fake_write_audit,
    )


    request = SimpleNamespace()

    db = SimpleNamespace()

    user = SimpleNamespace(
        id=1,
        username="admin",
        role="admin",
    )


    original_data = (
        b"Business Data Security "
        b"Mini V1 API Test"
    )


    # =========================
    # 1. 加密
    # =========================

    upload = make_upload_file(
        filename="report.txt",
        data=original_data,
        content_type="text/plain",
    )


    encrypt_response = asyncio.run(
        file_security_router.encrypt_file(
            request=request,
            file=upload,
            db=db,
            user=user,
        )
    )


    assert (
        encrypt_response.status_code
        == 200
    )

    assert (
        encrypt_response.body
        != original_data
    )

    assert (
        b"Business Data Security"
        not in encrypt_response.body
    )

    assert (
        ".bdsec"
        in encrypt_response.headers[
            "content-disposition"
        ]
    )


    assert (
        policy_calls[0]["resource"]
        == "file_security:encrypt"
    )

    assert (
        policy_calls[0]["action"]
        == "FILE_ENCRYPT"
    )


    assert (
        audit_calls[-1]["action"]
        == "FILE_ENCRYPT"
    )

    assert (
        audit_calls[-1]["result"]
        == "ALLOW"
    )


    # =========================
    # 2. 解密
    # =========================

    encrypted_upload = (
        make_upload_file(
            filename="report.txt.bdsec",
            data=encrypt_response.body,
            content_type=(
                "application/octet-stream"
            ),
        )
    )


    decrypt_response = asyncio.run(
        file_security_router.decrypt_file(
            request=request,
            file=encrypted_upload,
            db=db,
            user=user,
        )
    )


    assert (
        decrypt_response.status_code
        == 200
    )

    assert (
        decrypt_response.body
        == original_data
    )

    assert (
        "report.txt"
        in decrypt_response.headers[
            "content-disposition"
        ]
    )


    assert (
        policy_calls[1]["resource"]
        == "file_security:decrypt"
    )

    assert (
        policy_calls[1]["action"]
        == "FILE_DECRYPT"
    )


    assert (
        audit_calls[-1]["action"]
        == "FILE_DECRYPT"
    )

    assert (
        audit_calls[-1]["result"]
        == "ALLOW"
    )


def test_invalid_encrypted_file_should_be_rejected(
    monkeypatch,
):

    audit_calls = []


    monkeypatch.setattr(
        file_security_router,
        "require_policy",
        lambda **kwargs:
            SimpleNamespace(
                policy_id=101
            ),
    )


    monkeypatch.setattr(
        file_security_router,
        "write_audit",
        lambda **kwargs:
            audit_calls.append(
                kwargs
            ),
    )


    upload = make_upload_file(
        filename="broken.bdsec",
        data=b"not-a-valid-bdsec-file",
        content_type=(
            "application/octet-stream"
        ),
    )


    with pytest.raises(
        HTTPException
    ) as exc_info:

        asyncio.run(
            file_security_router.decrypt_file(
                request=SimpleNamespace(),
                file=upload,
                db=SimpleNamespace(),
                user=SimpleNamespace(
                    id=1,
                    username="admin",
                    role="admin",
                ),
            )
        )


    assert (
        exc_info.value.status_code
        == 400
    )


    assert audit_calls

    assert (
        audit_calls[-1]["action"]
        == "FILE_DECRYPT"
    )

    assert (
        audit_calls[-1]["result"]
        == "DENY"
    )