from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BusinessSystem

from app.modules.systems.schemas import (
    BusinessSystemCreate,
    BusinessSystemUpdate,
)


def get_system_by_id(
    db: Session,
    system_id: int,
) -> BusinessSystem | None:
    """
    根据 ID 查询业务系统
    """

    return db.get(
        BusinessSystem,
        system_id,
    )


def get_system_by_code(
    db: Session,
    system_code: str,
) -> BusinessSystem | None:
    """
    根据系统编码查询
    """

    statement = select(
        BusinessSystem
    ).where(
        BusinessSystem.system_code == system_code
    )

    return db.scalar(statement)


def list_systems(
    db: Session,
) -> list[BusinessSystem]:
    """
    查询全部业务系统
    """

    statement = (
        select(BusinessSystem)
        .order_by(
            BusinessSystem.id.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def create_system(
    db: Session,
    payload: BusinessSystemCreate,
) -> BusinessSystem:
    """
    创建业务系统
    """

    system = BusinessSystem(
        system_code=payload.system_code.strip().upper(),
        system_name=payload.system_name.strip(),
        system_type=payload.system_type,
        environment=payload.environment,
        owner_department=(
            payload.owner_department.strip()
            if payload.owner_department
            else None
        ),
        base_url=(
            payload.base_url.strip()
            if payload.base_url
            else None
        ),
        description=(
            payload.description.strip()
            if payload.description
            else None
        ),
        status="active",
    )

    db.add(system)

    db.commit()

    db.refresh(system)

    return system


def update_system(
    db: Session,
    system: BusinessSystem,
    payload: BusinessSystemUpdate,
) -> BusinessSystem:
    """
    修改业务系统
    """

    system.system_name = (
        payload.system_name.strip()
    )

    system.system_type = (
        payload.system_type
    )

    system.environment = (
        payload.environment
    )

    system.owner_department = (
        payload.owner_department.strip()
        if payload.owner_department
        else None
    )

    system.base_url = (
        payload.base_url.strip()
        if payload.base_url
        else None
    )

    system.description = (
        payload.description.strip()
        if payload.description
        else None
    )

    db.commit()

    db.refresh(system)

    return system


def update_system_status(
    db: Session,
    system: BusinessSystem,
    status: str,
) -> BusinessSystem:
    """
    修改系统启停状态
    """

    system.status = status

    db.commit()

    db.refresh(system)

    return system


def serialize_system(
    system: BusinessSystem,
) -> dict:
    """
    ORM 对象转换为前端返回数据
    """

    return {
        "id": system.id,
        "system_code": system.system_code,
        "system_name": system.system_name,
        "system_type": system.system_type,
        "environment": system.environment,
        "owner_department": system.owner_department,
        "base_url": system.base_url,
        "description": system.description,
        "status": system.status,
        "created_at": (
            system.created_at.isoformat()
            if system.created_at
            else None
        ),
        "updated_at": (
            system.updated_at.isoformat()
            if system.updated_at
            else None
        ),
    }