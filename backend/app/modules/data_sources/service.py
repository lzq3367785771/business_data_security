from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    BusinessSystem,
    DataSource,
)

from app.modules.data_sources.schemas import (
    DataSourceCreate,
    DataSourceUpdate,
)


def get_source_by_id(
    db: Session,
    source_id: int,
) -> DataSource | None:

    return db.get(
        DataSource,
        source_id,
    )


def get_source_by_code(
    db: Session,
    system_id: int,
    source_code: str,
) -> DataSource | None:

    statement = select(
        DataSource
    ).where(
        DataSource.system_id == system_id,
        DataSource.source_code == source_code,
    )

    return db.scalar(statement)


def system_exists(
    db: Session,
    system_id: int,
) -> bool:

    return (
        db.get(
            BusinessSystem,
            system_id,
        )
        is not None
    )


def list_sources(
    db: Session,
    system_id: int | None = None,
) -> list[DataSource]:

    statement = select(
        DataSource
    )

    if system_id is not None:

        statement = statement.where(
            DataSource.system_id == system_id
        )

    statement = statement.order_by(
        DataSource.id.asc()
    )

    return list(
        db.scalars(statement).all()
    )


def create_source(
    db: Session,
    payload: DataSourceCreate,
) -> DataSource:

    source = DataSource(
        system_id=payload.system_id,

        source_code=(
            payload.source_code
            .strip()
            .upper()
        ),

        source_name=(
            payload.source_name.strip()
        ),

        source_type=payload.source_type,

        environment=payload.environment,

        host=(
            payload.host.strip()
            if payload.host
            else None
        ),

        port=payload.port,

        database_name=(
            payload.database_name.strip()
            if payload.database_name
            else None
        ),

        username=(
            payload.username.strip()
            if payload.username
            else None
        ),

        base_url=(
            payload.base_url.strip()
            if payload.base_url
            else None
        ),

        file_root=(
            payload.file_root.strip()
            if payload.file_root
            else None
        ),

        auth_type=payload.auth_type,

        secret_ref=(
            payload.secret_ref.strip()
            if payload.secret_ref
            else None
        ),

        description=(
            payload.description.strip()
            if payload.description
            else None
        ),

        status="active",
    )

    db.add(source)

    db.commit()

    db.refresh(source)

    return source


def update_source(
    db: Session,
    source: DataSource,
    payload: DataSourceUpdate,
) -> DataSource:

    source.source_name = (
        payload.source_name.strip()
    )

    source.environment = (
        payload.environment
    )

    source.host = (
        payload.host.strip()
        if payload.host
        else None
    )

    source.port = payload.port

    source.database_name = (
        payload.database_name.strip()
        if payload.database_name
        else None
    )

    source.username = (
        payload.username.strip()
        if payload.username
        else None
    )

    source.base_url = (
        payload.base_url.strip()
        if payload.base_url
        else None
    )

    source.file_root = (
        payload.file_root.strip()
        if payload.file_root
        else None
    )

    source.auth_type = payload.auth_type

    source.secret_ref = (
        payload.secret_ref.strip()
        if payload.secret_ref
        else None
    )

    source.description = (
        payload.description.strip()
        if payload.description
        else None
    )

    db.commit()

    db.refresh(source)

    return source


def update_source_status(
    db: Session,
    source: DataSource,
    status: str,
) -> DataSource:

    source.status = status

    db.commit()

    db.refresh(source)

    return source


def serialize_source(
    source: DataSource,
) -> dict:

    return {
        "id": source.id,
        "system_id": source.system_id,
        "source_code": source.source_code,
        "source_name": source.source_name,
        "source_type": source.source_type,
        "environment": source.environment,
        "host": source.host,
        "port": source.port,
        "database_name": source.database_name,
        "username": source.username,
        "base_url": source.base_url,
        "file_root": source.file_root,
        "auth_type": source.auth_type,
        "secret_ref": source.secret_ref,
        "description": source.description,
        "status": source.status,

        "created_at": (
            source.created_at.isoformat()
            if source.created_at
            else None
        ),

        "updated_at": (
            source.updated_at.isoformat()
            if source.updated_at
            else None
        ),
    }