from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.db.models import User


def update_password(
    db,
    username: str,
    new_password: str,
):
    user = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if user is None:
        print(f"用户不存在：{username}")
        return

    user.password_hash = hash_password(new_password)

    print(f"密码已更新：{username}")


def main():

    with SessionLocal() as db:

        update_password(
            db,
            username="admin",
            new_password=settings.demo_admin_password,
        )

        update_password(
            db,
            username="analyst",
            new_password=settings.demo_analyst_password,
        )

        db.commit()

    print("")
    print("==============================")
    print("测试账号密码更新完成")
    print("==============================")


if __name__ == "__main__":
    main()