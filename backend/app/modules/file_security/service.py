import base64
import hashlib
import json

from pathlib import Path

from app.infrastructure.crypto import (
    decrypt_file_bytes,
    encrypt_file_bytes,
)


FILE_PACKAGE_VERSION = 1

MAX_FILE_SIZE = (
    10
    * 1024
    * 1024
)


def calculate_sha256(
    data: bytes,
) -> str:
    """
    计算文件内容 SHA-256。
    """

    return hashlib.sha256(
        data
    ).hexdigest()


def normalize_filename(
    filename: str,
) -> str:
    """
    清理用户提交的文件名。

    只保留最终文件名，
    防止把客户端目录路径写入安全包。
    """

    normalized = (
        Path(
            filename
        ).name.strip()
    )

    if not normalized:
        raise ValueError(
            "文件名不能为空"
        )

    return normalized


def build_secure_file(
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
) -> bytes:
    """
    将普通文件封装并加密为 .bdsec 内容。
    """

    if not data:
        raise ValueError(
            "文件内容不能为空"
        )

    if len(data) > MAX_FILE_SIZE:
        raise ValueError(
            "文件大小超过 10 MB 限制"
        )


    normalized_filename = (
        normalize_filename(
            filename
        )
    )


    sha256 = (
        calculate_sha256(
            data
        )
    )


    payload = {
        "version":
            FILE_PACKAGE_VERSION,

        "original_filename":
            normalized_filename,

        "content_type":
            content_type
            or "application/octet-stream",

        "size":
            len(data),

        "sha256":
            sha256,

        "data":
            base64.b64encode(
                data
            ).decode(
                "ascii"
            ),
    }


    serialized = (
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )
        .encode(
            "utf-8"
        )
    )


    return encrypt_file_bytes(
        serialized
    )


def restore_secure_file(
    encrypted_data: bytes,
) -> dict:
    """
    解密 .bdsec 文件并恢复原始文件信息。

    返回：
    {
        filename,
        content_type,
        size,
        sha256,
        data
    }
    """

    if not encrypted_data:
        raise ValueError(
            "加密文件内容不能为空"
        )


    decrypted = (
        decrypt_file_bytes(
            encrypted_data
        )
    )


    try:

        payload = json.loads(
            decrypted.decode(
                "utf-8"
            )
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:

        raise ValueError(
            "加密文件格式无效"
        ) from exc


    if (
        payload.get("version")
        != FILE_PACKAGE_VERSION
    ):
        raise ValueError(
            "不支持的加密文件版本"
        )


    filename = (
        payload.get(
            "original_filename"
        )
    )

    content_type = (
        payload.get(
            "content_type"
        )
        or "application/octet-stream"
    )

    expected_sha256 = (
        payload.get(
            "sha256"
        )
    )


    encoded_data = (
        payload.get(
            "data"
        )
    )


    if (
        not filename
        or not expected_sha256
        or not encoded_data
    ):
        raise ValueError(
            "加密文件缺少必要元数据"
        )


    try:

        restored_data = (
            base64.b64decode(
                encoded_data,
                validate=True,
            )
        )

    except ValueError as exc:

        raise ValueError(
            "加密文件内容编码无效"
        ) from exc


    actual_sha256 = (
        calculate_sha256(
            restored_data
        )
    )


    if (
        actual_sha256
        != expected_sha256
    ):
        raise ValueError(
            "文件完整性校验失败"
        )


    expected_size = (
        payload.get("size")
    )


    if (
        expected_size is not None
        and expected_size
        != len(restored_data)
    ):
        raise ValueError(
            "文件大小校验失败"
        )


    return {
        "filename":
            normalize_filename(
                filename
            ),

        "content_type":
            content_type,

        "size":
            len(restored_data),

        "sha256":
            actual_sha256,

        "data":
            restored_data,
    }