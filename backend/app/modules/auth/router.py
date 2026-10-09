from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.responses import success
from app.core.dependencies import get_current_user
from app.core.security import (
    verify_password,
    create_access_token
)
from app.db.session import get_db
from app.db.models import User


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    username: str
    password: str


def user_data(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    user = db.scalar(
        select(User).where(
            User.username == payload.username
        )
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(
            payload.password,
            user.password_hash
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    token = create_access_token(user.id)

    return success(
        request,
        {
            "access_token": token,
            "token_type": "bearer",
            "user": user_data(user)
        }
    )


@router.get("/me")
def get_me(
    request: Request,
    user: User = Depends(get_current_user)
):
    return success(
        request,
        user_data(user)
    )