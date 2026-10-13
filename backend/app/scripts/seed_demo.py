from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password

from app.db.session import (
    Base,
    engine,
    SessionLocal,
)

from app.db.models import (
    User,
    Customer,
    PolicyRule,
)


def create_user(
    db,
    username: str,
    password: str,
    role: str,
):
    """
    创建测试用户。

    如果用户名已经存在，则跳过，
    防止重复执行初始化脚本时重复插入。
    """

    exists = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if exists is not None:
        print(f"用户已存在，跳过：{username}")
        return

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(user)

    print(f"创建用户：{username}")


def create_policy(
    db,
    name: str,
    resource: str,
    roles: list[str],
    mask_fields: list[str],
    priority: int,
):
    """
    创建安全策略。

    同名策略存在时直接跳过。
    """

    exists = db.scalar(
        select(PolicyRule).where(
            PolicyRule.name == name
        )
    )

    if exists is not None:
        print(f"策略已存在，跳过：{name}")
        return

    rule = PolicyRule(
        name=name,
        resource=resource,
        allowed_roles=roles,
        effect="allow",
        mask_fields=mask_fields,
        priority=priority,
        enabled=True,
    )

    db.add(rule)

    print(f"创建策略：{name}")


def create_demo_customers(db):
    """
    创建演示业务数据。

    这些数据只用于验证权限和脱敏功能。
    """

    exists = db.scalar(
        select(Customer.id).limit(1)
    )

    if exists is not None:
        print("演示客户数据已存在，跳过")
        return

    customers = [
        Customer(
            name="测试用户A",
            phone="13800000001",
            id_card="TEST-ID-000001",
        ),
        Customer(
            name="测试用户B",
            phone="13900000002",
            id_card="TEST-ID-000002",
        ),
        Customer(
            name="测试用户C",
            phone="13700000003",
            id_card="TEST-ID-000003",
        ),
    ]

    db.add_all(customers)

    print("创建 3 条演示客户数据")


def main():
    """
    初始化 V1.0 基础数据库。

    创建：
    1. 数据库表
    2. admin 用户
    3. analyst 用户
    4. 演示客户数据
    5. 第一批访问控制策略
    """

    print("开始初始化数据库...")

    # -------------------------
    # 2. 创建数据库表
    # -------------------------

    Base.metadata.create_all(
        bind=engine
    )

    print("数据库表创建完成")

    # -------------------------
    # 3. 写入初始化数据
    # -------------------------

    with SessionLocal() as db:

        # 管理员
        create_user(
            db=db,
            username="admin",
            password=settings.demo_admin_password,
            role="admin",
        )

        # 普通分析用户
        create_user(
            db=db,
            username="analyst",
            password=settings.demo_analyst_password,
            role="analyst",
        )

        # -------------------------
        # 客户数据访问策略
        # -------------------------

        create_policy(
            db=db,
            name="管理员客户查询策略",
            resource="customer:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="普通用户客户脱敏策略",
            resource="customer:list",
            roles=["analyst"],
            mask_fields=[
                "phone",
                "id_card",
            ],
            priority=90,
        )

        # -------------------------
        # 审计访问策略
        # -------------------------

        create_policy(
            db=db,
            name="审计日志查看策略",
            resource="audit:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        # -------------------------
        # 策略中心访问策略
        # -------------------------

        create_policy(
            db=db,
            name="策略列表查看策略",
            resource="policy:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="业务系统列表查看策略",
            resource="system:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="业务系统详情查看策略",
            resource="system:detail",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="业务系统创建策略",
            resource="system:create",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="业务系统修改策略",
            resource="system:update",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="业务系统状态修改策略",
            resource="system:status",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="数据源列表查看策略",
            resource="datasource:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="数据源详情查看策略",
            resource="datasource:detail",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="数据源创建策略",
            resource="datasource:create",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="数据源修改策略",
            resource="datasource:update",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="数据源状态修改策略",
            resource="datasource:status",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )


        create_policy(
            db=db,
            name="凭据创建策略",
            resource="credential:create",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )


        create_policy(
            db=db,
            name="凭据列表查看策略",
            resource="credential:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )


        create_policy(
            db=db,
            name="数据源连接测试策略",
            resource="datasource:test_connection",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )


        create_policy(
            db=db,
            name="数据源元数据扫描策略",
            resource="datasource:scan_metadata",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )


        create_policy(
            db=db,
            name="数据资产同步策略",
            resource="datasource:sync_assets",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="敏感字段自动识别策略",
            resource="sensitive:detect",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="敏感字段内容识别策略",
            resource="sensitive:content_detect",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="敏感字段列表查询策略",
            resource="sensitive:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="敏感字段人工复核策略",
            resource="sensitive:review",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        create_policy(
            db=db,
            name="资产目录查询策略",
            resource="asset:list",
            roles=["admin"],
            mask_fields=[],
            priority=100,
        )

        # -------------------------
        # 演示客户数据
        # -------------------------

        create_demo_customers(db)

        # 提交事务
        db.commit()

    print("")
    print("==============================")
    print("数据库和测试数据初始化完成")
    print("==============================")
    print("")
    print("已初始化：")
    print("  users")
    print("  demo_customers")
    print("  policy_rules")
    print("  audit_events")
    print("")
    print("测试账号：")
    print("  admin")
    print("  analyst")
    print("")
    print("账号密码使用 backend/.env 中的配置。")


if __name__ == "__main__":
    main()