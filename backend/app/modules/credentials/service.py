from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Credential

from app.infrastructure.crypto import (
    decrypt_secret,
    encrypt_secret,
)

from app.modules.credentials.schemas import (
    CredentialCreate,
)


def list_credentials(
    db: Session,
) -> list[Credential]:
    """
    查询凭据列表。

    这里只返回凭据对象，
    后续由 serialize_credential()
    转换为安全响应数据。
    """

    return list(
        db.scalars(
            select(Credential)
            .order_by(
                Credential.credential_key.asc()
            )
        ).all()
    )




def get_credential_by_key(
    db: Session,
    credential_key: str,
) -> Credential | None:
    """
    根据凭据唯一标识查询凭据
    """

    normalized_key = (
        credential_key
        .strip()
        .upper()
    )

    return db.scalar(
        select(Credential).where(
            Credential.credential_key
            == normalized_key
        )
    )


def create_credential(
    db: Session,
    payload: CredentialCreate,
) -> Credential:
    """
    创建凭据。

    secret 在进入数据库之前立即加密。
    """

    credential = Credential(
        credential_key=(
            payload.credential_key
            .strip()
            .upper()
        ),

        credential_name=(
            payload.credential_name.strip()
        ),

        credential_type=(
            payload.credential_type
        ),

        username=(
            payload.username.strip()
            if payload.username
            else None
        ),

        secret_ciphertext=encrypt_secret(
            payload.secret
        ),

        status="active",
    )

    db.add(credential)

    db.commit()

    db.refresh(credential)

    return credential


def resolve_credential_secret(
    credential: Credential,
) -> str:
    """
    解密凭据。

    明文仅在需要连接数据源时短暂存在于内存，
    不写入日志、不写回数据库、不返回前端。
    """

    if credential.status != "active":
        raise ValueError(
            "凭据当前未启用"
        )

    return decrypt_secret(
        credential.secret_ciphertext
    )


def serialize_credential(
    credential: Credential,
) -> dict:
    """
    返回给前端的安全凭据信息。

    故意不返回：
    secret
    secret_ciphertext
    """

    return {
        "id": credential.id,

        "credential_key":
            credential.credential_key,

        "credential_name":
            credential.credential_name,

        "credential_type":
            credential.credential_type,

        "username":
            credential.username,

        "status":
            credential.status,

        "created_at": (
            credential.created_at.isoformat()
            if credential.created_at
            else None
        ),

        "updated_at": (
            credential.updated_at.isoformat()
            if credential.updated_at
            else None
        ),
    }