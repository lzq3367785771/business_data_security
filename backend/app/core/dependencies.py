from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.core.security import decode_user_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = (
        Depends(bearer_scheme)
    ),
    db: Session = Depends(get_db)
) -> User:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="请先登录"
        )

    user_id = decode_user_id(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效或已过期"
        )

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="账号不存在或已禁用"
        )

    return user