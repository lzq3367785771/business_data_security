#提供对称加密和解密能力，用于安全地存储和读取敏感信息（如数据库密码、第三方 API 密钥）

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)

from app.core.config import settings


def _fernet() -> Fernet:
    return Fernet(
        settings.credential_master_key.encode(
            "utf-8"
        )
    )


def _file_fernet() -> Fernet:
    return Fernet(
        settings.file_master_key.encode(
            "utf-8"
        )
    )





def encrypt_secret(
    secret: str,
) -> str:

    if not secret:
        raise ValueError(
            "凭据不能为空"
        )

    return (
        _fernet()
        .encrypt(
            secret.encode("utf-8")
        )
        .decode("utf-8")
    )


def decrypt_secret(
    ciphertext: str,
) -> str:

    try:

        return (
            _fernet()
            .decrypt(
                ciphertext.encode("utf-8")
            )
            .decode("utf-8")
        )

    except InvalidToken as exc:

        raise ValueError(
            "凭据解密失败，请检查主密钥"
        ) from exc



def encrypt_file_bytes(
    data: bytes,
) -> bytes:
    """
    对文件字节内容进行加密。

    当前用于 Mini V1 文件安全模块。
    """

    if not data:
        raise ValueError(
            "文件内容不能为空"
        )

    return (
        _file_fernet()
        .encrypt(
            data
        )
    )


def decrypt_file_bytes(
    ciphertext: bytes,
) -> bytes:
    """
    解密文件字节内容。
    """

    if not ciphertext:
        raise ValueError(
            "加密文件内容不能为空"
        )

    try:

        return (
            _file_fernet()
            .decrypt(
                ciphertext
            )
        )

    except InvalidToken as exc:

        raise ValueError(
            "文件解密失败，文件可能已损坏或主密钥不匹配"
        ) from exc