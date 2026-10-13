from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from sqlalchemy.orm import Session

from app.core.authorization import (
    require_policy,
)

from app.core.dependencies import (
    get_current_user,
)

from app.core.responses import success

from app.db.models import User
from app.db.session import get_db

from app.modules.audit.service import (
    write_audit,
)

from app.modules.credentials.schemas import (
    CredentialCreate,
)

from app.modules.credentials.service import (
    create_credential,
    get_credential_by_key,
    list_credentials,
    serialize_credential,
)


router = APIRouter(
    prefix="/api/v1/credentials",
    tags=["Credentials"],
)


@router.get("")
def get_credentials(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询安全凭据列表。

    注意：
    不返回密码、
    secret 或 secret_ciphertext。
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="credential:list",
        action="READ",
    )


    credentials = list_credentials(
        db
    )


    write_audit(
        db=db,
        request=request,
        user=user,
        action="READ",
        resource="credential:list",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=len(credentials),
    )


    return success(
        request,
        {
            "items": [
                serialize_credential(
                    credential
                )
                for credential
                in credentials
            ],
            "total":
                len(credentials),
        },
    )




@router.post("")
def create_new_credential(
    payload: CredentialCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    创建安全凭据
    """

    decision = require_policy(
        db=db,
        request=request,
        user=user,
        resource="credential:create",
        action="CREATE",
    )

    normalized_key = (
        payload.credential_key
        .strip()
        .upper()
    )

    exists = get_credential_by_key(
        db,
        normalized_key,
    )

    if exists is not None:

        raise HTTPException(
            status_code=409,
            detail="凭据标识已经存在",
        )

    credential = create_credential(
        db,
        payload,
    )

    write_audit(
        db=db,
        request=request,
        user=user,
        action="CREATE",
        resource="credential:create",
        result="ALLOW",
        policy_id=decision.policy_id,
        object_count=1,
    )

    return success(
        request,
        serialize_credential(
            credential
        ),
        message="凭据创建成功",
    )