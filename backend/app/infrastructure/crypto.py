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