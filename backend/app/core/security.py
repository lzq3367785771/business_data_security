from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"
ISSUER = "business-data-security"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        password,
        hashed_password
    )


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iss": ISSUER,
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.jwt_expire_minutes
        )
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=ALGORITHM
    )


def decode_user_id(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={
                "require": ["sub", "exp", "iss"]
            }
        )

        user_id = int(payload["sub"])

        if user_id <= 0:
            return None

        return user_id

    except (
        InvalidTokenError,
        ValueError,
        TypeError
    ):
        return None